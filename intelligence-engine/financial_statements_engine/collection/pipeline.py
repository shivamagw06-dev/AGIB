"""Collection lifecycle orchestration — stops at raw store + event emit (FSE-02 §7)."""

from __future__ import annotations

from typing import Any, Callable

from financial_statements_engine.collection.discovery import discover_from_rows
from financial_statements_engine.collection.downloader import download_bytes
from financial_statements_engine.collection.event_bus import publish
from financial_statements_engine.collection.integrity import verify_download
from financial_statements_engine.collection.jobs import dead_letter, save_job, set_status
from financial_statements_engine.collection.retry import retry_plan
from financial_statements_engine.collection.scheduler import plan_jobs
from financial_statements_engine.collection.writer import write_evidence
from financial_statements_engine.observability import record_event


def run_job(
    job: dict[str, Any],
    *,
    bytes_provider: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Execute one collection job through Store Raw → Emit Event.

    Does **not** call parsers, normalizers, validators, or warehouse publish.
    """
    job = save_job(job)
    job = set_status(job, "downloading")

    if bytes_provider is not None:
        dl = bytes_provider(job)
    else:
        dl = download_bytes(job.get("url"))

    if not dl.get("ok"):
        plan = retry_plan(int(job.get("attempt") or 0), http_status=dl.get("http_status"), exc=None)
        if plan["retry"]:
            job = set_status(
                job,
                "failed_transient",
                attempt=int(job.get("attempt") or 0) + 1,
                error=dl.get("error"),
                retry=plan,
            )
        else:
            job = dead_letter(job, str(dl.get("error") or "download_failed"))
            publish("collection.job_failed", {"job_id": job["job_id"], "error_code": "download_failed", "detail": dl.get("error")})
        return {"ok": False, "job": job, "download": dl}

    job = set_status(job, "downloaded", http_status=dl.get("http_status"))
    job = set_status(job, "verifying")
    verification = verify_download(dl["bytes"], document_type=job.get("document_type"))
    if not verification.get("ok"):
        job = dead_letter(job, "integrity_failed:" + ",".join(verification.get("issues") or []))
        publish(
            "collection.job_failed",
            {"job_id": job["job_id"], "error_code": "integrity_failed", "detail": verification.get("issues")},
        )
        return {"ok": False, "job": job, "verification": verification}

    job = set_status(job, "verified", content_sha256=verification.get("content_sha256"))
    write_result = write_evidence(
        ticker=str(job["ticker"]),
        data=dl["bytes"],
        source=str(job.get("source") or "unknown"),
        source_url=job.get("url"),
        document_type=str(job.get("document_type") or "unknown"),
        period_type=job.get("period_type"),
        period_end=job.get("period_end"),
        entity=job.get("entity"),
    )
    action = write_result.get("action")
    if action == "duplicate_skipped":
        job = set_status(job, "skipped_duplicate", evidence_id=write_result.get("evidence_id"))
        publish(
            "evidence.duplicate_skipped",
            {
                "evidence_id": write_result.get("evidence_id"),
                "ticker": job["ticker"],
                "job_id": job["job_id"],
                "logical_key": write_result.get("logical_key"),
            },
        )
        job = set_status(job, "completed")
        publish("collection.job_completed", {"job_id": job["job_id"], "status": "skipped_duplicate"})
        return {"ok": True, "job": job, "write": write_result, "action": action}

    job = set_status(job, "stored", evidence_id=write_result.get("evidence_id"))
    publish(
        "evidence.stored",
        {
            "evidence_id": write_result.get("evidence_id"),
            "ticker": job["ticker"],
            "source": job.get("source"),
            "content_sha256": write_result.get("content_sha256"),
            "path": (write_result.get("meta") or {}).get("bytes_path"),
            "job_id": job["job_id"],
            "logical_key": write_result.get("logical_key"),
        },
    )
    if action == "restatement_candidate":
        publish(
            "evidence.restatement_candidate",
            {
                "evidence_id": write_result.get("evidence_id"),
                "prior_evidence_id": write_result.get("prior_evidence_id"),
                "logical_key": write_result.get("logical_key"),
                "ticker": job["ticker"],
                "job_id": job["job_id"],
            },
        )
    job = set_status(job, "event_emitted")
    job = set_status(job, "completed")
    publish("collection.job_completed", {"job_id": job["job_id"], "status": "completed", "action": action})
    record_event({"stage": "collection", "ticker": job["ticker"], "job_id": job["job_id"], "action": action})
    return {"ok": True, "job": job, "write": write_result, "action": action, "verification": verification}


def collect_from_discovery_rows(
    ticker: str,
    rows: list[dict[str, Any]],
    *,
    mode: str = "live",
    bytes_by_url: dict[str, bytes] | None = None,
) -> dict[str, Any]:
    """Discover → plan jobs → run each job. Optional in-memory bytes map for tests."""
    discoveries = discover_from_rows(ticker, rows)
    jobs = plan_jobs(ticker, [d["discovery"] for d in discoveries], mode=mode)

    def provider(job: dict[str, Any]) -> dict[str, Any]:
        if bytes_by_url is not None:
            url = str(job.get("url") or "")
            if url in bytes_by_url:
                return download_bytes(url, data=bytes_by_url[url])
            # allow period_end key
            pe = str(job.get("period_end") or "")
            if pe in bytes_by_url:
                return download_bytes(url or pe, data=bytes_by_url[pe])
        return download_bytes(job.get("url"))

    results = [run_job(job, bytes_provider=provider if bytes_by_url is not None else None) for job in jobs]
    return {
        "ok": all(r.get("ok") for r in results) if results else True,
        "ticker": ticker.upper().strip(),
        "mode": mode,
        "discoveries": len(discoveries),
        "jobs": len(jobs),
        "results": results,
        "issues_recommendations": False,
    }

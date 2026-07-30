"""Office registry — catalog of live + planned application offices."""

from __future__ import annotations

from typing import Any, Callable, Optional

from office_sdk.domains import DOMAIN_OFFICES, list_domains
from office_sdk.schema import DOMAIN_RESEARCH, SDK_VERSION


def _dispatch_io(req: dict[str, Any]) -> dict[str, Any]:
    from office_sdk.adapters import wrap_io_response
    from investment_office.production import company, query

    tickers = list(req.get("tickers") or [])
    ticker = tickers[0] if tickers else None
    if not ticker:
        raise ValueError("IO-01 requires tickers[0]")
    question = req.get("question")
    package_type = req.get("package_type")
    options = req.get("options") if isinstance(req.get("options"), dict) else {}
    if question:
        pack = query(
            ticker=ticker,
            question=str(question),
            package_type=package_type,
            prebuilt=options.get("prebuilt"),
            series_map=options.get("series_map"),
            documents=options.get("documents"),
        )
    else:
        pack = company(
            ticker,
            package_type=package_type,
            prebuilt=options.get("prebuilt"),
            series_map=options.get("series_map"),
            documents=options.get("documents"),
        )
    return wrap_io_response(pack, request=req)


def _dispatch_cio(req: dict[str, Any]) -> dict[str, Any]:
    from office_sdk.adapters import wrap_cio_response
    from comparative_intelligence.production import compare_companies, query

    tickers = list(req.get("tickers") or [])
    question = req.get("question")
    options = req.get("options") if isinstance(req.get("options"), dict) else {}
    kwargs = {
        "comparison_type": req.get("comparison_type"),
        "modules": req.get("modules") or None,
        "prebuilt_map": options.get("prebuilt_map"),
        "series_maps": options.get("series_maps"),
        "documents_map": options.get("documents_map"),
    }
    if question:
        pack = query(tickers=tickers or None, question=str(question), **kwargs)
    else:
        pack = compare_companies(tickers, **kwargs)
    return wrap_cio_response(pack, request=req)


_DISPATCHERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "io-01": _dispatch_io,
    "cio-01": _dispatch_cio,
}


def catalog() -> dict[str, Any]:
    domains = list_domains()
    offices: list[dict[str, Any]] = []
    for d in domains:
        for o in d.get("offices") or []:
            offices.append({**o, "domain": d["domain"], "domain_label": d["label"]})
    return {
        "sdk_version": SDK_VERSION,
        "domains": domains,
        "offices": offices,
        "live_offices": [o for o in offices if o.get("status") == "live"],
        "planned_offices": [o for o in offices if o.get("status") == "planned"],
        "dispatchable": sorted(_DISPATCHERS.keys()),
        "contract": {
            "request": "office_sdk.office_request.v1",
            "response": "office_sdk.office_response.v1",
            "evidence_block": "office_sdk.evidence_block.v1",
        },
    }


def get_office(office_id: str) -> Optional[dict[str, Any]]:
    oid = (office_id or "").strip().lower()
    for domain, offices in DOMAIN_OFFICES.items():
        for o in offices:
            if o.get("office_id") == oid or o.get("workstream_id", "").lower() == oid:
                return {**o, "domain": domain}
    return None


def dispatch(request: dict[str, Any]) -> dict[str, Any]:
    """Route a shared OfficeRequest to a live office dispatcher."""
    from office_sdk.contracts import office_request

    oid = str(request.get("office_id") or "").strip().lower()
    if oid not in _DISPATCHERS:
        raise ValueError(f"office_id not dispatchable: {oid or '(empty)'}")
    # Normalize request shape
    req = office_request(
        office_id=oid,
        intent=str(request.get("intent") or "query"),
        tickers=list(request.get("tickers") or []),
        question=request.get("question"),
        package_type=request.get("package_type"),
        comparison_type=request.get("comparison_type"),
        modules=list(request.get("modules") or []),
        options=request.get("options") if isinstance(request.get("options"), dict) else {},
    )
    return _DISPATCHERS[oid](req)


def research_domain_default() -> str:
    return DOMAIN_RESEARCH

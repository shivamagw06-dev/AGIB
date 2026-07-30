"""CLI: python -m financial_statements_engine --health|TCS|--dashboard|..."""

from __future__ import annotations

import json
import sys

from financial_statements_engine.production import (
    coverage_report,
    dashboard,
    get_statements,
    health,
    ingest_and_publish,
)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("-h", "--help"):
        print(
            "usage: python -m financial_statements_engine "
            "--health|--dashboard|--coverage|--registry|"
            "--cfdm-health|--metric-registry|--resolve-metric NAME|"
            "--parsing-health|--parsing-dashboard|--parse-bytes TICKER --format FMT --file PATH|"
            "--quality-health|--quality-dashboard|--certify|--benchmark|"
            "--coverage-health|--coverage-dashboard|--coverage-analytics|"
            "--coverage-matrices TICKER|--coverage-history TICKER [--document-hash HASH]|"
            "--pcc-health|--pcc-dashboard|--pcc-analytics|--pcc-certify [--sector SECTOR]|--pcc-cases|"
            "--validation-health|--validation-dashboard|--validate-draft PATH|--validate-ticker TICKER|"
            "--warehouse-health|--warehouse-dashboard|--warehouse-latest TICKER|"
            "--warehouse-contract CONTRACT TICKER|--warehouse-view TICKER VIEW [--as-of TS]|"
            "--schema-evolution-health|--schema-resolve LABEL|"
            "--collection-health|--collection-dashboard|"
            "--collect TICKER [--mode live|historical]|TICKER [--publish]"
        )
        return 0

    cmd = args[0]
    if cmd == "--health":
        print(json.dumps(health(), indent=2, default=str))
        return 0
    if cmd == "--dashboard":
        print(json.dumps(dashboard(), indent=2, default=str))
        return 0
    if cmd == "--coverage":
        universe = args[1] if len(args) > 1 else "gold"
        print(json.dumps(coverage_report(universe), indent=2, default=str))
        return 0
    if cmd == "--registry":
        from financial_statements_engine.registry import registry_manifest

        print(json.dumps(registry_manifest(), indent=2, default=str))
        return 0
    if cmd == "--cfdm-health":
        from financial_statements_engine.cfdm.production import health as cfdm_health

        print(json.dumps(cfdm_health(), indent=2, default=str))
        return 0
    if cmd == "--metric-registry":
        from financial_statements_engine.metric_registry.production import health as mr_health

        print(json.dumps(mr_health(), indent=2, default=str))
        return 0
    if cmd == "--resolve-metric":
        from financial_statements_engine.metric_registry.production import resolve_payload

        if len(args) < 2:
            print("metric name required", file=sys.stderr)
            return 2
        print(json.dumps(resolve_payload(" ".join(args[1:])), indent=2, default=str))
        return 0
    if cmd == "--parsing-health":
        from financial_statements_engine.parsing.production import health as parsing_health

        print(json.dumps(parsing_health(), indent=2, default=str))
        return 0
    if cmd == "--parsing-dashboard":
        from financial_statements_engine.parsing.production import dashboard as parsing_dashboard

        print(json.dumps(parsing_dashboard(), indent=2, default=str))
        return 0
    if cmd == "--parse-bytes":
        from financial_statements_engine.parsing.production import parse_file

        if len(args) < 2:
            print("ticker required", file=sys.stderr)
            return 2
        ticker = args[1].upper()
        fmt = "xbrl"
        path = None
        period_end = None
        if "--format" in args:
            i = args.index("--format")
            if i + 1 < len(args):
                fmt = args[i + 1]
        if "--file" in args:
            i = args.index("--file")
            if i + 1 < len(args):
                path = args[i + 1]
        if "--period-end" in args:
            i = args.index("--period-end")
            if i + 1 < len(args):
                period_end = args[i + 1]
        if not path:
            print("--file PATH required", file=sys.stderr)
            return 2
        print(
            json.dumps(
                parse_file(ticker, path, document_type=fmt, period_end=period_end, period_type="annual"),
                indent=2,
                default=str,
            )
        )
        return 0
    if cmd == "--quality-health":
        from financial_statements_engine.parsing.quality.production import health as q_health

        print(json.dumps(q_health(), indent=2, default=str))
        return 0
    if cmd == "--quality-dashboard":
        from financial_statements_engine.parsing.quality.production import dashboard as q_dash

        print(json.dumps(q_dash(), indent=2, default=str))
        return 0
    if cmd == "--certify":
        from financial_statements_engine.parsing.quality.production import run_certification

        print(json.dumps(run_certification(), indent=2, default=str))
        return 0
    if cmd == "--benchmark":
        from financial_statements_engine.parsing.quality.production import run_benchmark_suite

        print(json.dumps(run_benchmark_suite(), indent=2, default=str))
        return 0
    if cmd == "--coverage-health":
        from financial_statements_engine.parsing.coverage.production import health as cov_health

        print(json.dumps(cov_health(), indent=2, default=str))
        return 0
    if cmd == "--coverage-dashboard":
        from financial_statements_engine.parsing.coverage.production import dashboard as cov_dash

        print(json.dumps(cov_dash(), indent=2, default=str))
        return 0
    if cmd == "--coverage-analytics":
        from financial_statements_engine.parsing.coverage.production import analytics as cov_analytics

        print(json.dumps(cov_analytics(), indent=2, default=str))
        return 0
    if cmd == "--coverage-matrices":
        from financial_statements_engine.parsing.coverage.production import matrices_for

        if len(args) < 2:
            print("ticker required", file=sys.stderr)
            return 2
        print(json.dumps(matrices_for(args[1]), indent=2, default=str))
        return 0
    if cmd == "--coverage-history":
        from financial_statements_engine.parsing.coverage.production import history_for

        if len(args) < 2:
            print("ticker required", file=sys.stderr)
            return 2
        doc_hash = None
        if "--document-hash" in args:
            i = args.index("--document-hash")
            if i + 1 < len(args):
                doc_hash = args[i + 1]
        print(json.dumps(history_for(args[1], document_hash=doc_hash), indent=2, default=str))
        return 0
    if cmd == "--pcc-health":
        from financial_statements_engine.parsing.pcc.production import health as pcc_health

        print(json.dumps(pcc_health(), indent=2, default=str))
        return 0
    if cmd == "--pcc-dashboard":
        from financial_statements_engine.parsing.pcc.production import dashboard as pcc_dash

        print(json.dumps(pcc_dash(), indent=2, default=str))
        return 0
    if cmd == "--pcc-analytics":
        from financial_statements_engine.parsing.pcc.production import analytics as pcc_analytics

        print(json.dumps(pcc_analytics(), indent=2, default=str))
        return 0
    if cmd == "--pcc-certify":
        from financial_statements_engine.parsing.pcc.production import run_certification as pcc_certify

        sector = None
        if "--sector" in args:
            i = args.index("--sector")
            if i + 1 < len(args):
                sector = args[i + 1]
        print(json.dumps(pcc_certify(sector=sector), indent=2, default=str))
        return 0
    if cmd == "--pcc-cases":
        from financial_statements_engine.parsing.pcc.production import cases as pcc_cases

        sector = args[1] if len(args) > 1 else None
        print(json.dumps(pcc_cases(sector=sector), indent=2, default=str))
        return 0
    if cmd == "--validation-health":
        from financial_statements_engine.validation.production import health as v_health

        print(json.dumps(v_health(), indent=2, default=str))
        return 0
    if cmd == "--validation-dashboard":
        from financial_statements_engine.validation.production import dashboard as v_dash

        print(json.dumps(v_dash(), indent=2, default=str))
        return 0
    if cmd == "--validate-draft":
        from financial_statements_engine.validation.production import run_validation_file

        if len(args) < 2:
            print("draft path required", file=sys.stderr)
            return 2
        publish = "--no-publish" not in args
        print(json.dumps(run_validation_file(args[1], publish=publish), indent=2, default=str))
        return 0
    if cmd == "--validate-ticker":
        from pathlib import Path

        from financial_statements_engine.store import ensure_dirs
        from financial_statements_engine.validation.production import run_validation_file

        if len(args) < 2:
            print("ticker required", file=sys.stderr)
            return 2
        ticker = args[1].upper().strip()
        latest = ensure_dirs() / "parsing" / "drafts" / ticker / "latest.json"
        if not latest.exists():
            print(f"no draft for {ticker}", file=sys.stderr)
            return 2
        meta = json.loads(latest.read_text(encoding="utf-8"))
        path = meta.get("path")
        if not path or not Path(path).exists():
            print("draft path missing", file=sys.stderr)
            return 2
        publish = "--no-publish" not in args
        print(json.dumps(run_validation_file(str(path), publish=publish), indent=2, default=str))
        return 0
    if cmd == "--warehouse-health":
        from financial_statements_engine.financial_warehouse.production import health as wh_health

        print(json.dumps(wh_health(), indent=2, default=str))
        return 0
    if cmd == "--warehouse-dashboard":
        from financial_statements_engine.financial_warehouse.production import dashboard as wh_dash

        print(json.dumps(wh_dash(), indent=2, default=str))
        return 0
    if cmd == "--warehouse-latest":
        from financial_statements_engine.financial_warehouse.production import get_latest

        if len(args) < 2:
            print("ticker required", file=sys.stderr)
            return 2
        print(json.dumps(get_latest(args[1]), indent=2, default=str))
        return 0
    if cmd == "--warehouse-contract":
        from financial_statements_engine.financial_warehouse.production import contract as wh_contract

        if len(args) < 3:
            print("contract_id and ticker required", file=sys.stderr)
            return 2
        print(json.dumps(wh_contract(args[1], args[2]), indent=2, default=str))
        return 0
    if cmd == "--warehouse-view":
        from financial_statements_engine.financial_warehouse.production import time_travel

        if len(args) < 3:
            print("ticker and view required", file=sys.stderr)
            return 2
        as_of = None
        if "--as-of" in args:
            i = args.index("--as-of")
            if i + 1 < len(args):
                as_of = args[i + 1]
        print(json.dumps(time_travel(args[1], args[2], as_of=as_of), indent=2, default=str))
        return 0
    if cmd == "--dme-health":
        from financial_statements_engine.derived_metrics.production import health as dme_health

        print(json.dumps(dme_health(), indent=2, default=str))
        return 0
    if cmd == "--dme-dashboard":
        from financial_statements_engine.derived_metrics.production import dashboard as dme_dash

        print(json.dumps(dme_dash(), indent=2, default=str))
        return 0
    if cmd == "--dme-calculate":
        from financial_statements_engine.derived_metrics.production import calculate as dme_calc

        if len(args) < 2:
            print("ticker required", file=sys.stderr)
            return 2
        persist = "--no-persist" not in args
        print(json.dumps(dme_calc(args[1], persist=persist), indent=2, default=str))
        return 0
    if cmd == "--dme-formulas":
        from financial_statements_engine.derived_metrics.production import formulas as dme_formulas

        cat = None
        if "--category" in args:
            i = args.index("--category")
            if i + 1 < len(args):
                cat = args[i + 1]
        print(json.dumps(dme_formulas(category=cat), indent=2, default=str))
        return 0
    if cmd == "--dme-contract":
        from financial_statements_engine.derived_metrics.production import contract as dme_contract

        if len(args) < 3:
            print("contract_id and ticker required", file=sys.stderr)
            return 2
        print(json.dumps(dme_contract(args[1], args[2]), indent=2, default=str))
        return 0
    if cmd == "--dme-lineage":
        from financial_statements_engine.derived_metrics.production import lineage as dme_lineage

        if len(args) < 2:
            print("metric_name required", file=sys.stderr)
            return 2
        print(json.dumps(dme_lineage(args[1]), indent=2, default=str))
        return 0
    if cmd == "--schema-evolution-health":
        from financial_statements_engine.schema_evolution.production import health as se_health

        print(json.dumps(se_health(), indent=2, default=str))
        return 0
    if cmd == "--schema-resolve":
        from financial_statements_engine.schema_evolution.production import resolve_payload as se_resolve

        if len(args) < 2:
            print("label required", file=sys.stderr)
            return 2
        print(json.dumps(se_resolve(" ".join(args[1:])), indent=2, default=str))
        return 0

    if cmd == "--collection-health":
        from financial_statements_engine.collection.production import health as collection_health

        print(json.dumps(collection_health(), indent=2, default=str))
        return 0
    if cmd == "--collection-dashboard":
        from financial_statements_engine.collection.production import dashboard as collection_dashboard

        print(json.dumps(collection_dashboard(), indent=2, default=str))
        return 0
    if cmd == "--collect":
        from financial_statements_engine.collection.production import collect_ticker

        if len(args) < 2:
            print("ticker required", file=sys.stderr)
            return 2
        ticker = args[1].upper()
        mode = "live"
        if "--mode" in args:
            i = args.index("--mode")
            if i + 1 < len(args):
                mode = args[i + 1]
        print(json.dumps(collect_ticker(ticker, mode=mode), indent=2, default=str))
        return 0
    if cmd == "--collect-universe":
        from financial_statements_engine.collection.production import run_universe

        universe = args[1] if len(args) > 1 else "gold"
        mode = "live"
        if "--mode" in args:
            i = args.index("--mode")
            if i + 1 < len(args):
                mode = args[i + 1]
        print(json.dumps(run_universe(universe, mode=mode), indent=2, default=str))
        return 0

    ticker = cmd.lstrip("-").upper()
    publish = "--publish" in args
    if publish:
        print(json.dumps(ingest_and_publish(ticker, publish=True), indent=2, default=str))
    else:
        print(json.dumps(get_statements(ticker), indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

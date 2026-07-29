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

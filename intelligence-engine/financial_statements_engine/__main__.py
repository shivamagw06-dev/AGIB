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
            "--health|--dashboard|--coverage|--registry|TICKER [--publish]"
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

    ticker = cmd.lstrip("-").upper()
    publish = "--publish" in args
    if publish:
        print(json.dumps(ingest_and_publish(ticker, publish=True), indent=2, default=str))
    else:
        print(json.dumps(get_statements(ticker), indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

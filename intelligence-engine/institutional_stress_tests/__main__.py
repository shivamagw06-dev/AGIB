"""CLI: python -m institutional_stress_tests --case IST-01"""

from __future__ import annotations

import argparse
import json
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="institutional_stress_tests",
        description="AGI Institutional Stress Tests — orchestration required",
    )
    parser.add_argument("--case", default="IST-01", help="Case id (default IST-01)")
    parser.add_argument("--health", action="store_true")
    parser.add_argument("--dashboard", action="store_true")
    parser.add_argument("--run", action="store_true", help="Run case with complete fixture answers")
    parser.add_argument("--inventory", action="store_true", help="Run probes only (expect answer-contract fail)")
    parser.add_argument("--single-module", metavar="MODULE", help="Negative test: probe only one module")
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args(list(sys.argv[1:] if argv is None else argv))

    if args.health:
        from institutional_stress_tests.production import health

        print(json.dumps(health(), indent=2, default=str))
        return 0
    if args.dashboard:
        from institutional_stress_tests.production import dashboard

        print(json.dumps(dashboard(), indent=2, default=str))
        return 0
    if args.report:
        from institutional_stress_tests.production import report

        out = report(args.case)
        print(out.get("markdown") or json.dumps(out, indent=2, default=str))
        return 0 if out.get("passed") else 1

    if args.run or args.inventory or args.single_module:
        from institutional_stress_tests.fixtures import complete_answers, fire_prebuilt
        from institutional_stress_tests.production import run

        prebuilt = fire_prebuilt() if (args.run or args.single_module) else None
        answers = complete_answers() if args.run else None
        modules_filter = [args.single_module] if args.single_module else None
        # Single-module negative test still needs the module's prebuilt if FIRE
        result = run(
            args.case,
            prebuilt=prebuilt,
            answers=answers,
            modules_filter=modules_filter,
            write_report=args.write_report,
        )
        print(json.dumps(
            {
                "case_id": result.get("case_id"),
                "passed": result.get("passed"),
                "score": (result.get("score") or {}).get("weighted_total"),
                "automatic_failures": (result.get("score") or {}).get("automatic_failures"),
                "gates": (result.get("score") or {}).get("gates"),
                "orchestration": (result.get("score") or {}).get("orchestration"),
                "summary": (result.get("score") or {}).get("summary"),
                "report_paths": result.get("report_paths"),
            },
            indent=2,
            default=str,
        ))
        return 0 if result.get("passed") else 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

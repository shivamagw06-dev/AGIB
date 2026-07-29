"""CLI: python -m institutional_evaluation_lab.iat --release PR309 [--freeze]"""

from __future__ import annotations

import argparse
import json
import sys


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="AGIB Phase 1 Institutional Acceptance Test")
    p.add_argument("--release", "--release-id", dest="release_id", default=None)
    p.add_argument("--previous", dest="previous_release", default=None)
    p.add_argument("--freeze", action="store_true", help="Freeze baseline only if IAT PASS")
    p.add_argument("--smoke", action="store_true", help="Advisory universe size (not official exam)")
    p.add_argument("--protocol", action="store_true", help="Print Baseline v1.0 Parts A–G protocol")
    p.add_argument(
        "--protocol-report",
        action="store_true",
        help="Write protocol workbook for a release (optional --release)",
    )
    p.add_argument("--json", action="store_true", help="Print full JSON pack")
    p.add_argument("--no-persist", action="store_true")
    args = p.parse_args(argv)

    from institutional_evaluation_lab.iat.production import protocol, protocol_report, run_iat

    if args.protocol and not args.protocol_report:
        pack = protocol()
        if args.json:
            print(json.dumps(pack, indent=2, default=str))
        else:
            from institutional_evaluation_lab.iat.protocol import format_protocol_text

            print(format_protocol_text(pack))
        return 0 if (pack.get("status") or {}).get("A") == "PASS" and (pack.get("status") or {}).get("B") == "PASS" else 1

    if args.protocol_report:
        pack = protocol_report(release_id=args.release_id, run_iat_first=False)
        if args.json:
            print(json.dumps({k: v for k, v in pack.items() if k != "report_text"}, indent=2, default=str))
        else:
            print(pack.get("report_text") or "")
            print()
            print("Part G workbook: human review required (see part_g_workbook in JSON).")
        return 0

    if not args.release_id:
        p.error("--release is required unless --protocol / --protocol-report")

    pack = run_iat(
        release_id=args.release_id,
        previous_release=args.previous_release,
        persist=not args.no_persist,
        freeze=args.freeze,
        require_full_universe=not args.smoke,
    )
    if args.json:
        print(json.dumps({k: v for k, v in pack.items() if k != "report_text"}, indent=2, default=str))
    else:
        print(pack.get("report_text") or json.dumps(pack, indent=2, default=str))
        freeze = pack.get("freeze") or {}
        if args.freeze:
            print()
            if freeze.get("frozen"):
                print(freeze.get("baseline", {}).get("freeze_prompt") or "FROZEN")
            else:
                print(f"Freeze refused: {freeze.get('reason')}")

    overall = (pack.get("overall") or {}).get("status")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

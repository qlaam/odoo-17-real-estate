"""Reject missing, empty or failed Odoo 17 test summaries in CI logs."""
from pathlib import Path
import re
import sys


def main():
    log = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
    summaries = re.findall(
        r"(\d+) failed, (\d+) error\(s\) of (\d+) tests", log
    )
    if not summaries:
        sys.exit("No recognized Odoo test summary; inspect the log.")
    if any(int(failed) or int(errors) for failed, errors, _ in summaries):
        sys.exit("Odoo reported failing tests; inspect the log.")
    if not any(int(total) > 0 for _, _, total in summaries):
        sys.exit("Odoo reported no tests; inspect test discovery.")
    print("Odoo summary reports tests with zero failures and errors.")


if __name__ == "__main__":
    main()

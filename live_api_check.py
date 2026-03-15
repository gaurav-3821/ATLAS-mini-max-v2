from __future__ import annotations

from utils.live_data import run_live_diagnostics


def main() -> None:
    results = run_live_diagnostics()
    failed = False
    for item in results:
        print(f"{item['name']}: {item['status']} - {item['detail']}")
        if item["status"] in {"Fail", "API key missing or invalid"}:
            failed = True

    if failed:
        raise SystemExit(1)

    print("ATLAS live API check completed.")


if __name__ == "__main__":
    main()

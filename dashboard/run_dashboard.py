from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root))
    try:
        from visual_twin_dashboard.app import main as app_main
    except ModuleNotFoundError as exc:
        missing = exc.name or "dependency"
        print(f"Missing dependency: {missing}")
        print("Install with: py -3 -m pip install -r dashboard\\requirements.txt")
        return 2
    except (ImportError, OSError) as exc:
        print("Dashboard dependency failed to load.")
        print(str(exc))
        print()
        print("Try rebuilding the dashboard virtual environment:")
        print("  Remove-Item -Recurse -Force dashboard\\.venv")
        print("  py -3 -m venv dashboard\\.venv")
        print("  dashboard\\.venv\\Scripts\\python -m pip install --upgrade pip")
        print("  dashboard\\.venv\\Scripts\\python -m pip install -r dashboard\\requirements.txt")
        print("  dashboard\\.venv\\Scripts\\python dashboard\\run_dashboard.py")
        return 2
    return app_main()


if __name__ == "__main__":
    raise SystemExit(main())

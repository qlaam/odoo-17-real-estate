"""Static addon checks only; does not import or execute Odoo or addon code."""
import ast
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
MODULES = ("estate", "estate_account")


def verify():
    errors = []
    for name in MODULES:
        addon = ROOT / "addons" / name
        manifest_path = addon / "__manifest__.py"
        if not manifest_path.is_file():
            errors.append(f"{name}: missing __manifest__.py")
            continue
        if not (addon / "__init__.py").is_file():
            errors.append(f"{name}: missing __init__.py")
        for path in sorted(addon.rglob("*.py")):
            try:
                ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
            except (SyntaxError, UnicodeError, OSError) as exc:
                errors.append(f"{path.relative_to(ROOT)}: {exc}")
        for path in sorted(addon.rglob("*.xml")):
            try:
                ET.parse(path)
            except (ET.ParseError, OSError) as exc:
                errors.append(f"{path.relative_to(ROOT)}: {exc}")
        try:
            manifest = ast.literal_eval(manifest_path.read_text(encoding="utf-8-sig"))
            if not isinstance(manifest, dict):
                raise ValueError("manifest must be a literal dictionary")
            for key in ("name", "version", "license"):
                if not isinstance(manifest.get(key), str) or not manifest[key].strip():
                    errors.append(f"{name}: missing string field {key}")
            if not str(manifest.get("version", "")).startswith("17.0."):
                errors.append(f"{name}: version must start with 17.0.")
            if manifest.get("license") != "LGPL-3":
                errors.append(f"{name}: expected LGPL-3 license")
            dependencies = manifest.get("depends", [])
            if not isinstance(dependencies, list) or not all(isinstance(x, str) for x in dependencies):
                errors.append(f"{name}: depends must be a list of strings")
                dependencies = []
            required = {"base"} if name == "estate" else {"estate", "account"}
            if not required.issubset(dependencies):
                errors.append(f"{name}: missing dependencies {sorted(required - set(dependencies))}")
            for key in ("data", "demo"):
                entries = manifest.get(key, [])
                if not isinstance(entries, list):
                    errors.append(f"{name}: {key} must be a list")
                    continue
                for entry in entries:
                    if not isinstance(entry, str):
                        errors.append(f"{name}: invalid {key} entry {entry!r}")
                        continue
                    target = (addon / entry).resolve()
                    if not target.is_relative_to(addon.resolve()) or not target.is_file():
                        errors.append(f"{name}: missing or external {key} file {entry}")
        except (ValueError, SyntaxError, UnicodeError, OSError) as exc:
            errors.append(f"{name}: invalid manifest: {exc}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        return 1
    print("Static AST/XML/manifest checks complete. Odoo integration tests were not run.")
    return 0


if __name__ == "__main__":
    sys.exit(verify())

from pathlib import Path
import re
import sys


ROOT = Path(".")


def insert_after(pattern: str, insertion: str, text: str) -> tuple[str, bool]:
    match = re.search(pattern, text, flags=re.MULTILINE)
    if not match:
        return text, False

    pos = match.end()
    return text[:pos] + insertion + text[pos:], True


def get_srvd_label(xml_path: Path) -> str | None:
    source_path = xml_path.with_suffix(".srvdsrv")

    if not source_path.exists():
        return None

    source = source_path.read_text(encoding="utf-8-sig")

    match = re.search(
        r"@EndUserText\.label\s*:\s*'([^']+)'",
        source,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    return match.group(1).strip()


def fix_srvd(xml_path: Path) -> bool:
    text = xml_path.read_text(encoding="utf-8-sig")

    if "<DESCRIPTION>" in text:
        print(f"OK   SRVD {xml_path}")
        return False

    label = get_srvd_label(xml_path)

    if not label:
        name_match = re.search(r"<NAME>([^<]+)</NAME>", text)
        if not name_match:
            print(f"ERROR: no se pudo determinar NAME en {xml_path}")
            return False

        label = f"{name_match.group(1)} Service Definition"

    insertion = f"\n    <DESCRIPTION>{label}</DESCRIPTION>"

    new_text, changed = insert_after(
        r"    <TYPE>SRVD/SRV</TYPE>",
        insertion,
        text,
    )

    if not changed:
        print(f"ERROR: no se encontró TYPE SRVD/SRV en {xml_path}")
        return False

    xml_path.write_text(
        new_text,
        encoding="utf-8-sig",
        newline="\n",
    )

    print(f"FIX  SRVD {xml_path}: {label}")
    return True


def fix_srvb(xml_path: Path) -> bool:
    text = xml_path.read_text(encoding="utf-8-sig")

    metadata_match = re.search(
        r"<METADATA>(.*?)</METADATA>",
        text,
        flags=re.DOTALL,
    )

    if not metadata_match:
        print(f"ERROR: METADATA no encontrado en {xml_path}")
        return False

    metadata = metadata_match.group(1)

    if "<DESCRIPTION>" in metadata:
        print(f"OK   SRVB {xml_path}")
        return False

    name_match = re.search(r"<NAME>([^<]+)</NAME>", metadata)

    if not name_match:
        print(f"ERROR: NAME no encontrado en METADATA de {xml_path}")
        return False

    name = name_match.group(1).strip()

    version_match = re.search(
        r"<BIND_TYPE_VERSION>([^<]+)</BIND_TYPE_VERSION>",
        text,
    )

    category_match = re.search(
        r"<BIND_TYPE_CATEGORY>([^<]+)</BIND_TYPE_CATEGORY>",
        text,
    )

    version = version_match.group(1).strip() if version_match else ""

    if version == "V2" and category_match:
        description = f"{name} - OData V2 Web API"
    elif version == "V4":
        description = f"{name} - OData V4"
    elif version:
        description = f"{name} - OData {version}"
    else:
        description = f"{name} Service Binding"

    insertion = f"\n     <DESCRIPTION>{description}</DESCRIPTION>"

    new_text, changed = insert_after(
        r"     <TYPE>SRVB/SVB</TYPE>",
        insertion,
        text,
    )

    if not changed:
        print(f"ERROR: no se encontró TYPE SRVB/SVB en {xml_path}")
        return False

    xml_path.write_text(
        new_text,
        encoding="utf-8-sig",
        newline="\n",
    )

    print(f"FIX  SRVB {xml_path}: {description}")
    return True


def main() -> int:
    src = ROOT / "src"

    if not src.exists():
        print("No existe carpeta src/. Nada que corregir.")
        return 0

    changed = 0

    for xml_path in sorted(src.rglob("*.srvd.xml")):
        if fix_srvd(xml_path):
            changed += 1

    for xml_path in sorted(src.rglob("*.srvb.xml")):
        if fix_srvb(xml_path):
            changed += 1

    print()
    print(f"Archivos corregidos: {changed}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

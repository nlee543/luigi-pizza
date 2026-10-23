"""Zip this project's Python sources and requirements.txt, preserving relative paths."""

import argparse
import os
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


PROJECT_ROOT = Path(__file__).resolve().parent
EXCLUDED_DIRECTORIES = {".venv", "__pycache__", ".git"}


def create_archive(output: Path) -> int:
    """Create a deployment archive and return the number of files included."""
    sources = []
    for directory, subdirectories, filenames in os.walk(PROJECT_ROOT):
        subdirectories[:] = sorted(
            name for name in subdirectories
            if name.lower() not in EXCLUDED_DIRECTORIES
            and not (Path(directory) / name).is_symlink()
        )
        for name in sorted(filenames):
            source = Path(directory) / name
            if (
                source.suffix.lower() == ".py"
                or source == PROJECT_ROOT / "requirements.txt"
            ) and not source.is_symlink():
                sources.append(source)

    output = output.resolve()
    if output.suffix.lower() != ".zip":
        raise ValueError("The output filename must end in .zip")
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        for source in sources:
            archive.write(source, source.relative_to(PROJECT_ROOT).as_posix())
    return len(sources)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-o", "--output", type=Path,
        default=PROJECT_ROOT / "deployment.zip",
        help="ZIP destination (default: deployment.zip beside this script; replaces existing ZIP)",
    )
    args = parser.parse_args()
    if args.output.suffix.lower() != ".zip":
        parser.error("The output filename must end in .zip")
    count = create_archive(args.output)
    print(f"Created {args.output.resolve()} with {count} files.")


if __name__ == "__main__":
    main()

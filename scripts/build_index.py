from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


PYODIDE_PACKAGES: list[str] = ["pyyaml", "pandas", "openpyxl"]
MOUNT_DIRS: tuple[str, ...] = ("models", "utils", "config", "styles")
TEXT_SUFFIXES: tuple[str, ...] = (
    ".py",
    ".yaml",
    ".yml",
    ".css",
    ".json",
    ".md",
    ".txt",
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", required=True, help="Path to the Streamlit entrypoint.")
    parser.add_argument("--out", required=True, help="Path to the generated index.html file.")
    parser.add_argument("--css", required=True, help="stlite CSS URL.")
    parser.add_argument("--js", required=True, help="stlite JS URL.")
    parser.add_argument("--title", default="EpiCON Cost Calculator", help="HTML page title.")
    return parser.parse_args()


def should_mount_file(path: Path) -> bool:
    """Return True when a file should be embedded into the stlite bundle."""
    if not path.is_file():
        return False

    if path.name.startswith("."):
        return False

    if "__pycache__" in path.parts:
        return False

    if path.suffix == ".pyc":
        return False

    return path.suffix.lower() in TEXT_SUFFIXES


def collect_files(project_root: Path, app_path: Path) -> dict[str, str]:
    """Collect source files that must be mounted into the stlite virtual filesystem."""
    mounted_files: dict[str, str] = {}

    files_to_mount: list[Path] = [app_path]

    for dirname in MOUNT_DIRS:
        directory = project_root / dirname
        if directory.exists():
            files_to_mount.extend(sorted(directory.rglob("*")))

    for path in files_to_mount:
        if not should_mount_file(path):
            continue

        relative_path = path.relative_to(project_root).as_posix()
        mounted_files[relative_path] = path.read_text(encoding="utf-8")

    return mounted_files


def build_html(
    *,
    title: str,
    css_url: str,
    js_url: str,
    entrypoint: str,
    mounted_files: dict[str, str],
) -> str:
    """Build the stlite HTML document."""
    title_html = html.escape(title, quote=True)
    css_html = html.escape(css_url, quote=True)
    js_json = json.dumps(js_url)
    entrypoint_json = json.dumps(entrypoint)
    files_json = json.dumps(mounted_files, ensure_ascii=False)
    packages_json = json.dumps(PYODIDE_PACKAGES)

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title_html}</title>
    <link rel="stylesheet" href="{css_html}" />
  </head>
  <body>
    <div id="root"></div>
    <script type="module">
      import {{ mount }} from {js_json};

      const root = document.getElementById("root");

      mount(
        {{
          entrypoint: {entrypoint_json},
          files: {files_json},
          requirements: {packages_json},
        }},
        root,
      );
    </script>
  </body>
</html>
"""


def main():
    """Generate the stlite index.html file."""
    args = parse_args()

    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent.resolve()
    app_path = (project_root / args.app).resolve()
    out_path = (project_root / args.out).resolve()

    mounted_files = collect_files(project_root, app_path)
    html_text = build_html(
        title=args.title,
        css_url=args.css,
        js_url=args.js,
        entrypoint=app_path.relative_to(project_root).as_posix(),
        mounted_files=mounted_files,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_text, encoding="utf-8")

    print(
        f"Written: {out_path.relative_to(project_root)}  "
        f"({len(html_text.encode('utf-8')):,} bytes, {len(mounted_files)} files mounted)"
    )
    print(f"Pyodide packages: {', '.join(PYODIDE_PACKAGES)}")


if __name__ == "__main__":
    main()
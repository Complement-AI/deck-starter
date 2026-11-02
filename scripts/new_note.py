#!/usr/bin/env python3
"""Create a note file with a fresh id. Standard library only.

    python3 scripts/new_note.py "Pharmacology/Autonomics" atenolol-selectivity --model Cloze
    python3 scripts/new_note.py "Pharmacology/Autonomics" atropine-toxicity --model Basic --tags anticholinergic,toxicology

Prints the new file's path. Never overwrites an existing file.
"""

from __future__ import annotations

import argparse
import re
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

BODIES = {
    "Cloze": "## Text\n\n{{c1::answer}}\n\n## Extra\n\n",
    "Basic": "## Front\n\n\n\n## Back\n\n\n\n## Extra\n\n",
}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("subdeck", help='folder under notes/, e.g. "Pharmacology/Autonomics" ("" for the deck root)')
    p.add_argument("slug", help="file name without .md, e.g. atenolol-selectivity")
    p.add_argument("--model", choices=sorted(BODIES), default="Cloze")
    p.add_argument("--tags", default="", help="comma-separated tags")
    args = p.parse_args()

    slug = re.sub(r"[^a-z0-9]+", "-", args.slug.lower()).strip("-")
    if not slug:
        sys.exit("slug must contain letters or digits")
    folder = ROOT / "notes" / args.subdeck.strip("/")
    path = folder / f"{slug}.md"
    if path.exists():
        sys.exit(f"{path.relative_to(ROOT)} already exists")
    tags = ", ".join(f'"{t.strip()}"' for t in args.tags.split(",") if t.strip())
    folder.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'---\nid    = "{uuid.uuid4()}"\nmodel = "{args.model}"\ntags  = [{tags}]\n---\n\n{BODIES[args.model]}',
        encoding="utf-8",
    )
    print(path.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main())

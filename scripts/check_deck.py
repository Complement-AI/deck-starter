#!/usr/bin/env python3
"""Check this deck repo before pushing. Standard library only (any Python 3.9+).

    python3 scripts/check_deck.py            # check the deck at the repo root
    python3 scripts/check_deck.py path/to/deck

Prints every error and warning with its file. Exits 1 if there are errors.
It applies the same rules Complement does when it publishes, so a clean run
here should publish. Complement's own check (publish_deck_from_github with
check_only) is the final word.
"""

from __future__ import annotations

import ast
import re
import sys
import uuid
from pathlib import Path

try:  # Python 3.11+
    import tomllib as _toml

    TOMLError = _toml.TOMLDecodeError

    def toml_loads(text: str) -> dict:
        return _toml.loads(text)
except ModuleNotFoundError:  # macOS ships Python 3.9: a small parser for what decks use
    class TOMLError(ValueError):
        pass

    _KEY = re.compile(r"^([A-Za-z0-9_-]+)\s*=\s*(.*)$")

    def _value(raw: str, lines: list, i: int):
        raw = raw.strip()
        for q in ('"""', "'''"):
            if raw.startswith(q):
                body = raw[3:]
                parts = []
                while q not in body:
                    parts.append(body)
                    i += 1
                    if i >= len(lines):
                        raise TOMLError("unterminated multi-line string")
                    body = lines[i]
                parts.append(body[: body.index(q)])
                text = "\n".join(parts)
                return (text[1:] if text.startswith("\n") else text), i
        if raw.startswith("["):
            while raw.count("[") > raw.count("]"):
                i += 1
                if i >= len(lines):
                    raise TOMLError("unterminated array")
                raw += " " + lines[i].split("#", 1)[0]
        raw = re.sub(r"\s+#[^\"']*$", "", raw)
        if raw in ("true", "false"):
            return raw == "true", i
        try:
            return ast.literal_eval(raw), i
        except (ValueError, SyntaxError) as e:
            raise TOMLError(f"cannot read value {raw!r}") from e

    def toml_loads(text: str) -> dict:
        data: dict = {}
        table = data
        lines = text.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line or line.startswith("#"):
                i += 1
                continue
            if line.startswith("[["):
                table = {}
                data.setdefault(line.strip("[] "), []).append(table)
            elif line.startswith("["):
                table = data.setdefault(line.strip("[] "), {})
            else:
                m = _KEY.match(line)
                if not m:
                    raise TOMLError(f"line {i + 1}: expected key = value")
                table[m.group(1)], i = _value(m.group(2), lines, i)
            i += 1
        return data

FRONT_MATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", re.DOTALL)
SECTION = re.compile(r"^##\s+(\S.*?)\s*$", re.MULTILINE)
CANONICAL_UUID = re.compile(r"\A[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\Z")
TAG_RUN = r"(?:</?[A-Za-z][^<>]*>)*"
CLOZE_OPENER = re.compile(r"\{" + TAG_RUN + r"\{c(\d+)::")
CLOZE_CLOSER = re.compile(r"\}" + TAG_RUN + r"\}")
MD_IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
HTML_IMG = re.compile(r"<img\b[^>]*?\bsrc\s*=\s*([\"'])([^\"']+)\1", re.IGNORECASE)
SOUND = re.compile(r"\[sound:([^\]]+)\]")
FIELD_NAMES = {"front": "Front", "back": "Back", "extra": "Extra", "text": "Text", "header": "Header", "image": "Image"}
KNOWN_SECTIONS = {"cloze": {"Text", "Extra"}, "basic": {"Front", "Back", "Extra"}}
MAX_MEDIA_BYTES = 20 * 1024 * 1024

errors: list[tuple[str, str]] = []
warnings: list[tuple[str, str]] = []


def normpath(p: str) -> str:
    parts: list[str] = []
    for seg in p.split("/"):
        if seg in ("", "."):
            continue
        if seg == "..":
            if parts:
                parts.pop()
            continue
        parts.append(seg)
    return "/".join(parts)


def cloze_numbers(text: str) -> set[int]:
    found = set()
    for m in CLOZE_OPENER.finditer(text):
        if CLOZE_CLOSER.search(text, m.end()):
            found.add(int(m.group(1)))
    return found


def media_refs(text: str) -> list[str]:
    refs = [m.group(2) for m in MD_IMAGE.finditer(text)]
    refs += [m.group(2) for m in HTML_IMG.finditer(text)]
    refs += [m.group(1) for m in SOUND.finditer(text)]
    return [r for r in refs if not r.startswith(("http://", "https://", "data:"))]


def check_manifest(root: Path) -> str:
    path = root / "deck.toml"
    if not path.exists():
        errors.append(("deck.toml", "deck.toml is missing at the deck root"))
        return "media/"
    try:
        data = toml_loads(path.read_text(encoding="utf-8"))
    except (TOMLError, UnicodeDecodeError) as e:
        errors.append(("deck.toml", f"deck.toml is not valid TOML: {e}"))
        return "media/"
    deck = data.get("deck") or {}
    if not str(deck.get("title") or "").strip():
        errors.append(("deck.toml", "[deck].title is required"))
    if not isinstance(deck.get("keywords", []), list):
        errors.append(("deck.toml", "[deck].keywords must be a list of strings"))
    for key in ("license", "attribution", "source_url"):
        if key in deck and not isinstance(deck[key], str):
            errors.append(("deck.toml", f"[deck].{key} must be a string"))
    url = deck.get("source_url")
    if isinstance(url, str) and url.strip() and not url.startswith(("https://", "http://")):
        errors.append(("deck.toml", "[deck].source_url must be an http(s) URL"))
    if not str(deck.get("summary") or "").strip():
        warnings.append(("deck.toml", "[deck].summary is empty; Deck Cloud shows it under the title"))
    if not str(deck.get("license") or "").strip():
        warnings.append(("deck.toml", "[deck].license is missing; Deck Cloud will show no license"))
    return ((data.get("sync") or {}).get("media_root") or "media/").rstrip("/") + "/"


def check_note(rel: str, body: str, media: set[str], ids: dict[str, str]) -> int:
    m = FRONT_MATTER.match(body)
    if not m:
        errors.append((rel, "file must begin with `---`-delimited TOML front-matter"))
        return 0
    try:
        fm = toml_loads(m.group(1))
    except TOMLError as e:
        errors.append((rel, f"front-matter is not valid TOML: {e}"))
        return 0
    note_id = fm.get("id")
    if not isinstance(note_id, str) or not note_id:
        errors.append((rel, "front-matter missing required `id` (UUID)"))
        return 0
    if not CANONICAL_UUID.match(note_id):
        errors.append((rel, f"`id` must be a canonical hyphenated UUID (8-4-4-4-12 hex), got {note_id!r}"))
        return 0
    parsed = uuid.UUID(note_id)
    if parsed.int == 0 or parsed.version is None:
        errors.append((rel, "`id` must be a v4 or v7 UUID"))
        return 0
    note_id = str(parsed)
    model = fm.get("model")
    if not isinstance(model, str) or not model:
        errors.append((rel, "front-matter missing required `model`"))
        return 0
    tags = fm.get("tags") or []
    if not isinstance(tags, list):
        errors.append((rel, "`tags` must be a list of strings"))
        return 0
    sections = list(SECTION.finditer(m.group(2)))
    if not sections:
        errors.append((rel, "no `## Section` blocks found — at least one is required"))
        return 0
    if note_id in ids:
        errors.append((rel, f"shares id {note_id} with {ids[note_id]}. Keep the id on the note students already have "
                            "(usually the older file: check git log) and give the other a new one"))
        return 0
    ids[note_id] = rel

    content = m.group(2)
    fields: dict[str, str] = {}
    for i, s in enumerate(sections):
        end = sections[i + 1].start() if i + 1 < len(sections) else len(content)
        name = FIELD_NAMES.get(s.group(1).strip().lower(), s.group(1).strip())
        fields[name] = content[s.end():end].strip()

    kind = model.lower()
    cards = 1
    if kind == "cloze":
        text = fields.get("Text", "")
        numbers = cloze_numbers(text)
        if not text.strip():
            errors.append((rel, "Cloze note needs a non-empty ## Text section"))
        elif not numbers:
            errors.append((rel, "## Text has no cloze deletions; write at least one {{c1::answer}}"))
        elif "{{c1::answer}}" in text:
            errors.append((rel, "## Text still has the placeholder {{c1::answer}} from new_note.py; write the card"))
        cards = max(1, len(numbers))
        if CLOZE_OPENER.search(fields.get("Extra", "")):
            warnings.append((rel, "## Extra contains cloze markers; only ## Text is clozed"))
    else:
        if not (fields.get("Front") or fields.get("Text", "")).strip():
            errors.append((rel, f"{model} note needs a non-empty ## Front section"))
        if not (fields.get("Back") or fields.get("Extra") or "").strip():
            errors.append((rel, f"{model} note needs a non-empty ## Back section"))
        if kind != "basic":
            warnings.append((rel, f"model {model!r} is not Basic or Cloze; it makes one card from ## Front and ## Back"))
        if CLOZE_OPENER.search(fields.get("Front", "")):
            warnings.append((rel, '## Front has cloze markers but the model is not Cloze; set model = "Cloze" and use ## Text'))
    known = KNOWN_SECTIONS.get(kind, KNOWN_SECTIONS["basic"])
    for name in fields:
        if name not in known:
            warnings.append((rel, f"## {name} is not a {model} section ({', '.join(sorted(known))}); it is kept as an extra field but not shown on the card face"))
    for tag in tags:
        if any(ch.isspace() for ch in str(tag)):
            warnings.append((rel, f"tag {tag!r} contains a space; Anki splits tags on spaces, use - or ::"))
    note_dir = "/".join(rel.split("/")[:-1])
    for name, text in fields.items():
        for ref in media_refs(text):
            target = normpath(f"{note_dir}/{ref}")
            if target not in media:
                errors.append((rel, f"## {name} references {ref}, which resolves to {target}; no such file in the repo"))
    return cards


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent)
    media_root = check_manifest(root)
    media = set()
    media_dir = root / media_root
    if media_dir.exists():
        for f in media_dir.rglob("*"):
            if f.is_file() and not any(p.startswith(".") for p in f.relative_to(root).parts):
                rel = f.relative_to(root).as_posix()
                media.add(rel)
                if f.stat().st_size > MAX_MEDIA_BYTES:
                    errors.append((rel, f"media file is over {MAX_MEDIA_BYTES // (1024 * 1024)} MB"))
    notes_dir = root / "notes"
    ids: dict[str, str] = {}
    notes = cards = 0
    subdecks = set()
    files = sorted(f for f in notes_dir.rglob("*") if f.is_file()) if notes_dir.exists() else []
    for f in files:
        rel = f.relative_to(root).as_posix()
        if any(p.startswith(".") for p in f.relative_to(root).parts):
            continue
        if f.suffix != ".md":
            warnings.append((rel, "ignored: only .md files under notes/ become notes"))
            continue
        try:
            body = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append((rel, "not UTF-8 text"))
            continue
        before = len(errors)
        n = check_note(rel, body, media, ids)
        if n and len(errors) == before:
            notes += 1
            cards += n
            parts = rel.split("/")[1:-1]
            if parts:
                subdecks.add("::".join(parts))
    if not files:
        errors.append(("notes/", "no notes: add one .md file per note under notes/"))

    for path, msg in errors:
        print(f"error   {path}: {msg}")
    for path, msg in warnings:
        print(f"warning {path}: {msg}")
    print(f"{notes} notes, {cards} cards, {len(subdecks)} subdecks, {len(media)} media files; "
          f"{len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

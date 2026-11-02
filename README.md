# Complement deck starter

Template for a [Complement](https://complementai.app) Deck Cloud deck that
lives in a GitHub repo. Push to `main`, and Complement publishes a new version
that subscribers can apply.

Use this template, then replace the example notes.

## Layout

```
deck.toml        manifest (required)
notes/           one Markdown file per note; folders become subdecks
media/           images and audio referenced by notes
CREDITS.md       source and license for every image or adapted text
LICENSE          license for your cards
```

Everything outside `deck.toml`, `notes/**/*.md` and `media/` is ignored by the
sync.

## deck.toml

| key | required | notes |
| --- | --- | --- |
| `title` | yes | Deck name on Deck Cloud |
| `summary` | yes | One-line teaser |
| `description` | recommended | Long text, shown under "About this deck" |
| `keywords` | no | Topics used for browsing and filters |
| `license` | no | SPDX id, shown on the deck page |
| `attribution` | recommended | Credit for upstream authors and sources |
| `source_url` | no | Link to full credits (usually `CREDITS.md`) |

The manifest overrides anything entered when the deck was created, on every
sync.

## Notes

Each note is a Markdown file with TOML front-matter between `---` fences:

```markdown
---
id    = "3f0c2a52-6d1e-4c39-9d43-2b8f7d1e5a10"
model = "Cloze"
tags  = ["cardio"]
---

## Text

<b>Beta-blockers</b> block {{c1::β1}} receptors.

## Extra

Supporting context.
```

- `id` is a UUID. Generate it once (`python -c 'import uuid; print(uuid.uuid4())'`)
  and never change it: sync matches notes by id, so moving or renaming a file
  keeps its review history, while changing the id replaces the card.
- `model = "Cloze"`: every distinct `cN` becomes a card. Sections are usually
  `## Text` and `## Extra`.
- Any other model makes one card per note. Sections are usually `## Front`,
  `## Back` and `## Extra`.
- Use HTML `<b>` and `<u>` for emphasis; Markdown `**bold**` shows literal
  asterisks.
- Reference media relative to the note file: `![alt](../../media/file.png)`.
  Sync uploads it and rewrites the link.

## Licensing

Decks on Deck Cloud must be yours or openly licensed.

- Fill in `license`, `attribution` and `source_url`.
- Credit every image in `CREDITS.md`. Wikimedia Commons files list their
  license on the file page.
- Don't copy from commercial resources (First Aid, Pathoma, UWorld, Sketchy,
  Boards & Beyond, bar-prep outlines), from AnkiWeb shared decks, or from
  sources licensed NonCommercial (NC).

This template is released under [CC BY-SA 4.0](LICENSE), the license
Complement uses for its own decks.

## Check before you push

```sh
python3 scripts/check_deck.py
```

It lists every problem with its file. The same check runs on every push and
pull request (`.github/workflows/check-deck.yml`). Create notes with
`python3 scripts/new_note.py "<Subdeck>" <slug> [--model Basic]` (Cloze by
default) so each one gets a fresh id.

## Connect to Complement

With an AI agent (Claude Code, Claude Desktop, or any MCP client connected to
Complement): ask it to publish the repo. It reads [AGENTS.md](AGENTS.md),
pushes, and calls `publish_deck_from_github`, which returns the deck's link.
Calling it again after a push publishes the new version to everyone who added
the deck.

By hand:

1. On Deck Cloud, choose **Publish from GitHub** and paste the repo URL.
2. Click **Open GitHub webhook settings**, paste the secret it shows you, and
   click **Add webhook**. The secret is shown only once.
3. Push to `main`, or click **Sync now**. The first sync publishes version 1.

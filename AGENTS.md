# Writing and publishing this deck (for AI agents)

This repo is a flashcard deck. The files are the deck: Complement reads them
from GitHub and publishes them on Deck Cloud, where students add the deck and
study it. You write notes as files, check them, commit, push, and publish.
The user decides what goes in the deck and when it is published.

## The loop

1. **Set up once.** Make a public repo from this template:
   `gh repo create <name> --public --template Complement-AI/deck-starter --clone`.
   Fill in every field of `deck.toml` (title, summary, description, keywords,
   license, attribution, source_url). Delete `notes/Example/`. Images go in a
   `media/` folder you create when you need one.
2. **Write notes.** Create each note with
   `python3 scripts/new_note.py "<Subdeck>/<Topic>" <slug> --model Cloze`
   (or `--model Basic`; quote folder names with spaces). It writes a file with
   a fresh id and placeholder sections; replace them (the checker refuses a
   leftover `{{c1::answer}}`).
3. **Check.** `python3 scripts/check_deck.py`. Fix every error. Read the warnings.
4. **Commit and push** to `main`.
5. **Publish.** Call the Complement MCP tool `publish_deck_from_github` with
   `repo: "<owner>/<name>"`. The first call creates the deck and returns its
   link (`deck_url`) to share with students. Each later call publishes the
   pushed commit as a new version, and every student who added the deck gets it.
   If it returns `status: "invalid"` or `"refused"`, nothing was published:
   follow its `next_step` (fix the listed files, push, call again).
   Before publishing changes to a deck students already use, call it with
   `check_only: true` first: `would_change` lists the notes that would be
   added, edited, moved and removed, and every card students would lose.
   Show the user any removals before you publish.
   Pass `release_note`: one or two sentences from the user to their students,
   in the user's voice, about what changed for them ("Week 3 is up:
   antiplatelets for Thursday. Fixed the nebivolol card."). Students see it on
   Home with the update. No file names, ids or version numbers.
6. **Report** to the user: the version, what changed (`changes`; a moved note
   counts as modified), how many students got it (`subscribers.students_updated`),
   how many kept their own edited version of a changed card
   (`subscribers.students_keeping_own_edits`), and the link.

No Complement MCP connection? Ask the user to add it (https://mcp.complementai.app/mcp)
or to publish from Deck Cloud → Publish from GitHub. `list_published_decks` shows
the user's decks and the last sync's status and error.

The first publish also returns `auto_sync`: an optional push webhook. If you
have `gh` and the user agrees, run its `gh_command` once; then every push to
`main` (including pull requests merged by classmates) publishes on its own.
Don't paste its secret into chat or files.
`list_published_decks` with `include_webhook_setup: true` returns it again.

## Listening to students

Students suggest fixes from a card's menu while they study. They reach the
user, and you, without names.

- `list_deck_suggestions` lists open ones, each with the note's file and its
  current text. When the user asks to "review suggestions", check each against
  the source material, fix the files that need it, push, publish (mention the
  fixes in `release_note`), then `resolve_deck_suggestions` with `outcome:
  "fixed"` and a short reply. When a card is right as it is, resolve it as
  `declined` with the reason. The student reads the reply on Home.
- `list_published_decks` returns `usage`, counted across students and never per
  student: how many study the deck, how many have the latest version, reviews
  this week, open suggestions, and `hardest`, the cards students miss most. A
  card most students miss is often worded badly or tests two things: offer to
  rewrite or split it.

## Layout

```
deck.toml        manifest (required)
notes/           one .md file per note; folders are subdecks
media/           images and audio the notes reference (create it when needed)
CREDITS.md       source and license of every image and adapted text
scripts/         check_deck.py, new_note.py
```

Folders under `notes/` become subdecks, nested with `::`:
`notes/Pharmacology/Autonomics/atenolol.md` is in `Pharmacology::Autonomics`.
Name folders the way students should see them. Decks sort alphabetically, so
number every top-level folder to keep course order (`Week 01 Autonomics`,
`Week 02 Anticoagulants`), and give sections outside the sequence a prefix
that sorts where they belong (`Week 99 Toxicology`, or `Z Toxicology` to put
it last).
One level of folders (weeks or topics) is enough for a course deck; nest
deeper only when a topic is big. Everything outside `deck.toml`, `notes/` and
`media/` is ignored.

## A note file

```markdown
---
id    = "3f0c2a52-6d1e-4c39-9d43-2b8f7d1e5a10"
model = "Cloze"
tags  = ["autonomics", "beta-blockers"]
---

## Text

<b>Atenolol</b> is a {{c1::β1-selective::receptor selectivity}} antagonist.

## Extra

Cardioselective agents (atenolol, metoprolol, bisoprolol) are preferred in asthma.
```

- Front-matter is TOML between `---` lines: `id`, `model`, `tags`.
- `model = "Cloze"`: sections `## Text` (with `{{c1::...}}`) and `## Extra`.
  Every distinct number (`c1`, `c2`, ...) becomes one card.
- `model = "Basic"`: sections `## Front`, `## Back`, `## Extra`. One card.
- Emphasis: `<b>` for key terms, `<u>` for buzzwords. Markdown lists and
  `![alt](...)` images work too.
- Images: put the file in `media/` and reference it relative to the note:
  `![SA node](../../media/sa-node.png)`. Credit it in `CREDITS.md`.
- Tags: no spaces (use `-` or `::`).

## Ids are students' progress

The `id` ties a note to every student's review history. Complement matches
notes by id, never by file name.

- **Never change, regenerate or reuse an id.** Editing a note, renaming its
  file, or moving it to another folder keeps its id, and students keep their
  progress and see the edit.
- New note: new id (`new_note.py` does this). Duplicating a file to start a new
  note? Replace the copied id.
- Splitting a note: the original id stays on the part closest to the original;
  the other parts get new ids. Cards that move to a new note start over for
  every student (their history stays with the old card, which is removed), so
  tell the user before splitting a card students have studied.
- Deleting a note file removes that card from every student who has it, with
  its history. Removing a `{{cN}}` removes that card. Do it only when the user
  wants the card gone.
- Publishing refuses a commit that removes many notes at once, or that gives
  existing content a new id. If that happens, you most likely broke ids: restore
  them from git history (`git log -p -- <file>`). Pass `expected_removals` only
  when the user confirms the removal is intended.

Students who edit a card themselves keep their version; your later edits to
that note don't overwrite it.

## Writing good cards

Default to Cloze. Use Basic only when the answer is a short structured list
or a comparison that reads badly as a blank.

- **One fact per card.** If you can delete one cloze and the card still tests
  a complete fact, split it.
- **≤ 3 cloze numbers per note** (each number is one card), except named lists (triads, criteria, a regimen):
  cloze every item, all as `c1`.
- **`c1` for items at the same level, `c2` for a second layer** of the same
  concept (drug c1 → mechanism c2; condition A c1 vs condition B c2).
- **Cloze the target, not the context.** `In <b>DKA</b>, serum K⁺ is {{c1::high}}`.
- **Hint the answer type when the stem doesn't**: `{{c1::propranolol::drug}}`,
  `{{c1::CYP3A4::enzyme}}`, `{{c1::AR::inheritance}}`.
- **No giveaways after a cloze.** Write `{{c1::N-acetylcysteine (NAC)}}`, not
  `{{c1::N-acetylcysteine}} (NAC)`.
- **No `<b>`/`<u>` inside a cloze. No clozes in `## Extra`.** Extra is plain
  supporting context: mechanism, mnemonic, clinical pearl.

Pharmacy examples:

```
<b>Warfarin</b> inhibits {{c1::vitamin K epoxide reductase::enzyme}} → ↓ factors {{c2::II, VII, IX, X}}.
<b>Digoxin</b> toxicity: {{c1::nausea}}, {{c1::visual changes (yellow-green halos)}}, {{c1::arrhythmias}}.
Strong CYP3A4 inhibitors: {{c1::clarithromycin}}, {{c1::ketoconazole}}, {{c1::ritonavir}}, {{c1::grapefruit juice}}.
Antidote for <b>acetaminophen</b> overdose: {{c1::N-acetylcysteine::antidote}}.
<b>Vancomycin</b> infused too fast → {{c1::vancomycin infusion reaction (red man syndrome)}}.
```

## Content you may use

Decks on Deck Cloud are public and must be yours or openly licensed.

- Write cards in your own words from what the user gives you (their notes,
  lecture outlines, guidelines). Facts aren't owned; wording and images are.
- Don't copy text, tables or images from textbooks, lecture slides, question
  banks (UWorld, RxPrep, Lexicomp, Pharmacist's Letter) or AnkiWeb decks.
- Images: your own diagrams (SVG is fine), or Wikimedia Commons / public-domain
  files, each credited in `CREDITS.md` with its license.
- Set `license` in `deck.toml` (this template uses `CC-BY-SA-4.0`).

## Collaborating

Classmates can send pull requests. `.github/workflows/check-deck.yml` runs the
checker on every push and pull request, so a broken note shows as a failed
check before it is merged. After a merge, publish (or let the webhook do it).

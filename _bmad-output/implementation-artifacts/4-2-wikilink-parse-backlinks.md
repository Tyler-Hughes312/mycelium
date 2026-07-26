# Story 4.2: Wikilink parse + backlinks

Status: done

## Story

As a developer,
I want `[[wikilinks]]` resolved to backlinks,
So that my Thinking Vault behaves like a second brain (FR-12).

## Delivered

- Parse `[[target]]` / `[[target|alias]]`
- Resolve note↔note (`wikilink`) and note→symbol (`mentions`)
- Unresolved links flagged on note payload
- `GET /vault/notes/{id}/backlinks`
- `POST /vault/reindex`

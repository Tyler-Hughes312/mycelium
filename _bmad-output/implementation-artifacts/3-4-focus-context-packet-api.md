# Story 3.4: Focus Context Packet API

Status: done

## Story

As a developer,
I want Context for the current file/symbol,
So that the Side Panel has a backend (FR-10).

## Acceptance Criteria

1. `POST /context/focus` returns ranked packet (similarity + graph + recency) — **done**
2. Empty index returns empty packet with `reason: empty_index` — **done**

## Delivered

- `RagService.focus` + `POST /context/focus`
- Desktop client helper `focusContext`

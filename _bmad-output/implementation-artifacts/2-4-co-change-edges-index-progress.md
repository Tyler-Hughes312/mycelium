# Story 2.4: Co-change Edges + index progress

Status: done

## Story

As a developer,
I want co-change links and visible index progress,
so that related code is graph-reachable and long indexes feel safe (FR-3, FR-7).

## Acceptance Criteria

1. Symbols changed in the same Commit get `co_changed` Edges — **done**
2. `GET /workspaces/{id}/index/status` reports progress; cancel supported without store corruption — **done**

## Notes

- Async index via background thread; `POST .../index/cancel` sets cancel event
- Symbol/edge snapshots written only after phases complete (cancel skips final write)
- Index console polls status, Cancel button, Co-change Edges list
- 10 pytest tests passing

# Story 1.1: Project scaffold and Core Service hello

Status: done

## Story

As a developer,
I want a Mycelium repo with Python Core Service scaffolding,
so that subsequent features have a stable place to land.

## Acceptance Criteria

1. **Given** a clean checkout  
   **When** I create the Core package layout per architecture Structural Seed  
   **Then** `core/`, `adapters/`, `bridges/` directories exist with empty ports interfaces  
   **And** the project uses the existing `venv` / lockfile approach for Python 3.12

2. **Given** the scaffold is in place  
   **When** I import the package from the project venv  
   **Then** `import mycelium` succeeds and exposes a version string

3. **Given** ports interfaces are defined  
   **When** I inspect `core/ports/`  
   **Then** there are typed Protocol stubs for GraphStore, EmbeddingRuntime, WorkspaceRepo

## Tasks / Subtasks

- [x] Align package root with Structural Seed (AC: #1)
  - [x] Create hexagonal dirs under `services/core/src/mycelium/`
  - [x] Ensure: `core/domain/`, `core/ports/`, `adapters/{http,git,embeddings,store}/`, `bridges/`
  - [x] Add `__init__.py` files so packages import cleanly
- [x] Wire Python packaging to existing venv (AC: #1, #2)
  - [x] Update `services/core/pyproject.toml` for src-layout install (`pip install -e .`)
  - [x] Keep FastAPI runnable via `main.py` re-export
  - [x] Confirm `venv` at repo root works with Python 3.12
- [x] Define empty ports (AC: #3)
  - [x] `GraphStore`, `EmbeddingRuntime`, `WorkspaceRepo` Protocols
- [x] Smoke verification
  - [x] `python -c "import mycelium; print(mycelium.__version__)"`
  - [x] Health endpoint still responds (`uvicorn main:app`)

## Dev Agent Record

### Completion Notes List

- Package lives at `services/core/src/mycelium/` (documented in README)
- FastAPI moved to `mycelium.adapters.http.app`; `main:app` preserved
- 4 pytest smoke tests passing

### File List

- `services/core/pyproject.toml`
- `services/core/main.py`
- `services/core/src/mycelium/**`
- `services/core/tests/test_scaffold.py`
- `services/core/README.md`

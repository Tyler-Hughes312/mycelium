"""Plain-markdown Vault on disk (AD-5 / FR-11)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mycelium.adapters.vault.wikilinks import slugify_title

INDEX_FILENAME = "_index.md"


class VaultError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class NoteRecord:
    id: str
    title: str
    path: str
    abs_path: str
    body: str
    updated_at: str
    created_at: str | None = None

    @property
    def bucket(self) -> str:
        parent = Path(self.path).parent
        if parent == Path("."):
            return ""
        return parent.as_posix()

    @property
    def is_index(self) -> bool:
        return Path(self.path).name == INDEX_FILENAME


def note_id_for_rel(rel: Path) -> str:
    stem = rel.with_suffix("").as_posix()
    return f"note:{stem}"


def rel_from_note_id(note_id: str) -> Path:
    if not note_id.startswith("note:"):
        raise VaultError("invalid_id", f"Invalid note id: {note_id}")
    stem = note_id[len("note:") :]
    if not stem or ".." in stem.split("/"):
        raise VaultError("invalid_id", f"Invalid note id: {note_id}")
    return Path(f"{stem}.md")


def normalize_bucket(bucket: str | None) -> str:
    """Return posix relative bucket path or '' for vault root."""
    if bucket is None:
        return ""
    raw = bucket.strip().replace("\\", "/").strip("/")
    if not raw:
        return ""
    parts: list[str] = []
    for part in raw.split("/"):
        part = part.strip()
        if not part or part in {".", ".."}:
            raise VaultError("invalid_bucket", f"Invalid bucket path: {bucket}")
        cleaned = "".join(c if c.isalnum() or c in "-_" else "-" for c in part)
        cleaned = cleaned.strip("-._") or "bucket"
        if ".." in cleaned:
            raise VaultError("invalid_bucket", f"Invalid bucket path: {bucket}")
        parts.append(cleaned.lower())
    return "/".join(parts)


class VaultFs:
    """Read/write `.md` notes under a vault root."""

    def __init__(self, vault_dir: Path) -> None:
        self.root = vault_dir.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _safe(self, rel: Path) -> Path:
        if rel.is_absolute() or ".." in rel.parts:
            raise VaultError("outside_vault", f"Path escapes vault: {rel}")
        abs_path = (self.root / rel).resolve()
        try:
            abs_path.relative_to(self.root)
        except ValueError as exc:
            raise VaultError("outside_vault", f"Path escapes vault: {rel}") from exc
        return abs_path

    def list_notes(self) -> list[NoteRecord]:
        rows: list[NoteRecord] = []
        for path in sorted(self.root.rglob("*.md")):
            rel = path.relative_to(self.root)
            rows.append(self._read_path(rel, path))
        return rows

    def get(self, note_id: str) -> NoteRecord:
        rel = rel_from_note_id(note_id)
        path = self._safe(rel)
        if not path.is_file():
            raise VaultError("not_found", f"Note not found: {note_id}")
        return self._read_path(rel, path)

    def get_by_title_or_stem(self, target: str) -> NoteRecord | None:
        needle = target.strip().lower()
        if not needle:
            return None
        for note in self.list_notes():
            stem = Path(note.path).stem.lower()
            if stem == needle or note.title.lower() == needle:
                return note
            # also match note id without prefix
            if note.id.lower() == f"note:{needle}" or note.id[5:].lower() == needle:
                return note
        return None

    def create(
        self,
        *,
        title: str,
        body: str = "",
        filename: str | None = None,
        bucket: str | None = None,
    ) -> NoteRecord:
        stem = slugify_title(filename or title)
        # Filename stem must not include path separators
        stem = stem.replace("/", "-").replace("\\", "-") or "untitled"
        bucket_path = normalize_bucket(bucket)
        rel = Path(bucket_path) / f"{stem}.md" if bucket_path else Path(f"{stem}.md")
        path = self._safe(rel)
        if path.exists():
            raise VaultError("exists", f"Note already exists: {rel.as_posix()}")
        path.parent.mkdir(parents=True, exist_ok=True)
        content = self._compose(title=title, body=body)
        path.write_text(content, encoding="utf-8")
        return self._read_path(rel, path)

    def mkdir_bucket(self, name: str) -> dict[str, Any]:
        bucket_path = normalize_bucket(name)
        if not bucket_path:
            raise VaultError("invalid_bucket", "Bucket name required")
        folder = self._safe(Path(bucket_path))
        folder.mkdir(parents=True, exist_ok=True)
        index_rel = Path(bucket_path) / INDEX_FILENAME
        index_abs = self._safe(index_rel)
        created_index = False
        if not index_abs.exists():
            title = Path(bucket_path).name.replace("-", " ").title()
            body = (
                f"Bucket brief for **{bucket_path}**. "
                "Summarize key notes here for cheap LLM context (no RAG).\n"
            )
            index_abs.write_text(self._compose(title=title, body=body), encoding="utf-8")
            created_index = True
        index_note = self._read_path(index_rel, index_abs) if index_abs.is_file() else None
        return {
            "bucket": bucket_path,
            "path": bucket_path,
            "abs_path": str(folder),
            "created_index": created_index,
            "index": (
                {
                    "id": index_note.id,
                    "title": index_note.title,
                    "path": index_note.path,
                }
                if index_note
                else None
            ),
        }

    def list_tree(self) -> dict[str, Any]:
        """Nested folder/note map for structure-first LLM context."""
        notes = self.list_notes()
        root: dict[str, Any] = {
            "type": "folder",
            "name": "",
            "path": "",
            "children": [],
        }

        # Ensure empty dirs (buckets without notes yet) appear
        folders: set[str] = set()
        for path in self.root.rglob("*"):
            if path.is_dir():
                rel = path.relative_to(self.root).as_posix()
                if rel != ".":
                    folders.add(rel)

        for note in notes:
            if note.bucket:
                folders.add(note.bucket)
                # parents
                parts = note.bucket.split("/")
                for i in range(1, len(parts)):
                    folders.add("/".join(parts[:i]))

        def ensure_folder(bucket: str) -> dict[str, Any]:
            if not bucket:
                return root
            node = root
            built = []
            for part in bucket.split("/"):
                built.append(part)
                cur = "/".join(built)
                kids = node["children"]
                found = next(
                    (c for c in kids if c.get("type") == "folder" and c.get("path") == cur),
                    None,
                )
                if found is None:
                    found = {
                        "type": "folder",
                        "name": part,
                        "path": cur,
                        "children": [],
                    }
                    kids.append(found)
                node = found
            return node

        for folder in sorted(folders):
            ensure_folder(folder)

        for note in notes:
            parent = ensure_folder(note.bucket)
            parent["children"].append(
                {
                    "type": "note",
                    "id": note.id,
                    "title": note.title,
                    "path": note.path,
                    "name": Path(note.path).name,
                    "is_index": note.is_index,
                    "updated_at": note.updated_at,
                }
            )

        def sort_children(node: dict[str, Any]) -> None:
            kids = node.get("children") or []
            folders_first = sorted(
                [c for c in kids if c.get("type") == "folder"],
                key=lambda c: str(c.get("path") or ""),
            )
            notes_sorted = sorted(
                [c for c in kids if c.get("type") == "note"],
                key=lambda c: (not c.get("is_index"), str(c.get("path") or "")),
            )
            node["children"] = folders_first + notes_sorted
            for child in folders_first:
                sort_children(child)

        sort_children(root)
        return {
            "root": root,
            "notes": len(notes),
            "buckets": len(folders),
        }

    def notes_in_bucket(self, bucket: str | None = None) -> list[NoteRecord]:
        bucket_path = normalize_bucket(bucket) if bucket else ""
        notes = self.list_notes()
        if not bucket_path:
            return notes
        prefix = f"{bucket_path}/"
        return [
            n
            for n in notes
            if n.path.startswith(prefix) or n.bucket == bucket_path
        ]

    def update(self, note_id: str, *, title: str | None = None, body: str | None = None) -> NoteRecord:
        existing = self.get(note_id)
        new_title = title if title is not None else existing.title
        new_body = body if body is not None else existing.body
        rel = rel_from_note_id(note_id)
        path = self._safe(rel)
        path.write_text(self._compose(title=new_title, body=new_body), encoding="utf-8")
        return self._read_path(rel, path)

    def delete(self, note_id: str) -> None:
        rel = rel_from_note_id(note_id)
        path = self._safe(rel)
        if not path.is_file():
            raise VaultError("not_found", f"Note not found: {note_id}")
        path.unlink()
        # clean empty dirs
        parent = path.parent
        while parent != self.root and parent.is_dir() and not any(parent.iterdir()):
            parent.rmdir()
            parent = parent.parent

    def _compose(self, *, title: str, body: str) -> str:
        body = body.lstrip()
        if body.startswith("# "):
            return body if body.endswith("\n") else body + "\n"
        return f"# {title.strip() or 'Untitled'}\n\n{body.rstrip()}\n"

    def _read_path(self, rel: Path, path: Path) -> NoteRecord:
        text = path.read_text(encoding="utf-8")
        title, body = self._split_title(text, fallback=rel.stem)
        stat = path.stat()
        updated = datetime.fromtimestamp(stat.st_mtime, tz=UTC).replace(microsecond=0)
        return NoteRecord(
            id=note_id_for_rel(rel),
            title=title,
            path=rel.as_posix(),
            abs_path=str(path),
            body=body,
            updated_at=updated.isoformat().replace("+00:00", "Z"),
        )

    @staticmethod
    def _split_title(text: str, *, fallback: str) -> tuple[str, str]:
        lines = text.splitlines()
        if lines and lines[0].startswith("# "):
            title = lines[0][2:].strip() or fallback
            rest = "\n".join(lines[1:]).lstrip("\n")
            return title, rest
        # first non-empty line as soft title
        for line in lines:
            if line.strip():
                return line.strip()[:80], text
        return fallback, text

"""Vault adapter package."""

from mycelium.adapters.vault.fs import NoteRecord, VaultError, VaultFs
from mycelium.adapters.vault.wikilinks import Wikilink, parse_wikilinks, slugify_title

__all__ = [
    "NoteRecord",
    "VaultError",
    "VaultFs",
    "Wikilink",
    "parse_wikilinks",
    "slugify_title",
]

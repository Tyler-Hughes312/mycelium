# Story 4.1: Vault path + Note file CRUD API

Status: done

## Story

As a developer,
I want a plain markdown Vault on disk,
So that I can think in files I own (FR-11).

## Delivered

- `~/.mycelium/vault/` (configurable) with `.md` CRUD
- `GET/POST /vault/notes`, `GET/PUT/DELETE /vault/notes/{id}`
- Desktop Vault page reads/writes through Core

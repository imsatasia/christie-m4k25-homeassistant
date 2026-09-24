# AGENTS.md

## Purpose

`christie-m4k25-homeassistant` is the Home Assistant integration for the
Christie M 4K25 RGB projector, built on top of
[`py-christie-mseries`](https://github.com/imsatasia/py-christie-mseries).

## Workflow

- Use `make`/`uv` for local commands (`make install`, `make test`, `make check`).
- Run repo-local lint, format, typecheck and tests before pushing.
- For local dev, point the sibling checkout: `pyproject.toml`'s
  `[tool.uv] sources` and the `Makefile`'s `CHRISTIE_LIB_PATH` both default
  to `../py-christie-mseries`, so `make install`/`make test` run against
  whatever's checked out there rather than waiting on a PyPI release.
  `ty` needs the same path explicitly (`--extra-search-path`, already wired
  into `make typecheck`) since it doesn't follow setuptools' finder-based
  editable installs the way the Python interpreter does at runtime.

## Design Expectations

- **Keep this repo projection-only.** Protocol semantics, device quirks, and
  the brightness-floor/test-pattern/lens-range rules all belong in
  `py-christie-mseries`; this repo turns `ChristieM4K25`/`Snapshot` into HA
  entities and nothing more. If a bug looks like "the projector said X but
  we show Y," check whether the fix belongs in the library's `snapshot()`
  first — the exact lesson learned porting the Trinnov integration's upmixer
  bugs upstream instead of patching around them here.
- The coordinator (`coordinator.py`) and every command (`commands.py`) open
  their own short-lived connection per call, matching the CLI's design —
  don't hold a persistent connection across Home Assistant's lifecycle, and
  don't rewrite `py-christie-mseries`'s client as async. It's a simple
  synchronous request/response client by design; wrap calls in
  `hass.async_add_executor_job` instead.
- A poll failure (including the few seconds right after a power command,
  where the projector accepts the connection but answers nothing) should
  raise `UpdateFailed` from `_async_update_data`, not be caught and turned
  into a sentinel "unavailable" field the way the old YAML-based setup did.
  `DataUpdateCoordinator`/`CoordinatorEntity` already give every entity
  `available` for free from `last_update_success`.
- Lens presets are synthesised the same way the Control4 driver does it —
  the projector has no lens memory of its own — using Home Assistant's
  `Store` helper as the equivalent of `C4:PersistSetValue`. See
  `services.py`.
- Entity `unique_id`s and `translation_key`s should stay stable; changing
  them silently creates duplicate entities in a live install rather than
  updating the existing ones.

## Commits

Use conventional commits for releasable changes: `fix: ...` or `feat: ...`.

## Releases

1. Merge normal conventional commits to `main`.
2. Let `release-please` open or update the release PR.
3. Do not manually edit `manifest.json`'s version or `CHANGELOG.md` outside
   the Release Please PR.
4. Merge the Release Please PR to publish. Distribution is via HACS (add
   this repo as a custom repository), not PyPI — there's nothing to publish
   there for a Home Assistant integration.
5. When bumping `py-christie-mseries`'s minimum version in `manifest.json`'s
   `requirements` and `pyproject.toml`'s `dependencies`, keep both in sync
   and confirm the referenced version is actually published before merging.

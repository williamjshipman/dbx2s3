# Repository Guidelines

## Project Structure & Module Organization
The codebase centers on `src/dbx2s3`, which houses the backup workflow. `backup.py` orchestrates Dropbox traversal with storage adapters; `dropbox_client.py`, `s3_storage.py`, and `storage.py` implement provider logic; `state_manager.py` persists incremental state and drives resume behavior. CLI entry points live in `cli.py` and top-level `main.py`. Tests reside under `tests/`, mirroring core services. Sample invocations and reference assets live in `examples/`, while `.github/` contains automation, and docs (`README.md`, `QUICKSTART.md`, `TROUBLESHOOTING.md`) outline user flows.

## Build, Test, and Development Commands
Install dependencies with `uv sync`. Run the tool in development via `uv run dbx2s3 --path /Documents --no-resume` or `uv run python main.py --help`. Regenerate the lockfile after dependency updates with `uv lock`. Execute the smoke test suite using `uv run python tests/test_basic.py`; extend it with module-specific checks before submitting changes.

## Coding Style & Naming Conventions
Follow PEP 8 with 4-space indentation and descriptive snake_case for modules, functions, and variables. Public classes use PascalCase (`BackupManager`). Maintain type hints and docstrings as seen across `src/dbx2s3`. Favor the standard `logging` module for runtime diagnostics and keep logging configuration within CLI layers.

## Testing Guidelines
Keep unit tests under `tests/` and mirror target module names (e.g., `test_state_manager.py`). Use `unittest.TestCase` and `self.assert*` assertions to match the existing test suite, even when calling modules directly with `python`. When adding network-facing logic, supply fakes or fixtures rather than hitting external services. Verify that incremental workflows persist state by covering both `should_backup_file` and `mark_file_backed_up`.

## Commit & Pull Request Guidelines
Write imperative, present-tense commit subjects (e.g., `Add comprehensive troubleshooting guide`) and group related changes per commit. Before opening a PR, ensure `uv run python tests/test_basic.py` passes and manual CLI smoke tests cover new paths. PR descriptions should summarize the change, list key test commands, mention any configuration updates, and reference related issues. Include screenshots or logs when altering user-visible CLI output.

## Configuration Tips
Store secrets solely in `.env`; never commit them. Document new environment variables in `config.py` docstrings and `README.md`. When adding storage backends, keep their configuration isolated under dedicated prefixes to align with existing `S3_` and `AZURE_` settings.

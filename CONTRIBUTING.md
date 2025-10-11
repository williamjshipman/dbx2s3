# Contributing to dbx2s3

Thank you for your interest in contributing to dbx2s3!

## Development Setup

1. Install `uv`:
   ```bash
   pip install uv
   ```

2. Clone the repository:
   ```bash
   git clone https://github.com/williamjshipman/dbx2s3.git
   cd dbx2s3
   ```

3. Install dependencies:
   ```bash
   uv sync
   ```

4. Run tests:
   ```bash
   uv run python tests/test_basic.py
   ```

## Project Structure

```
dbx2s3/
├── src/dbx2s3/         # Main package source code
│   ├── __init__.py     # Package initialization
│   ├── backup.py       # Backup orchestration logic
│   ├── cli.py          # Command-line interface
│   ├── config.py       # Configuration management
│   ├── dropbox_client.py  # Dropbox API client
│   ├── s3_storage.py   # Storage backend implementations
│   ├── state_manager.py   # State tracking for incremental backups
│   └── storage.py      # Abstract storage interface
├── tests/              # Test files
├── main.py             # Entry point
├── pyproject.toml      # Project metadata and dependencies
└── README.md           # Documentation
```

## Adding a New Storage Backend

To add support for a new storage backend:

1. Create a new class that inherits from `Storage` in `storage.py`
2. Implement the required methods:
   - `upload_file(key, data, metadata)`
   - `file_exists(key)`
   - `get_file_metadata(key)`
3. Add configuration options to `config.py`
4. Update the CLI in `cli.py` to support the new backend
5. Update the README with usage instructions

## Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings to all public functions and classes
- Keep functions focused and small

## Testing

Before submitting a pull request:

1. Ensure all existing tests pass
2. Add tests for new functionality
3. Test with real Dropbox and storage credentials (if possible)

## Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request with a clear description of changes

## License

By contributing, you agree that your contributions will be licensed under the GNU General Public License v3.0.

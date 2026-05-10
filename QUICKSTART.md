# Quick Start Guide

## Prerequisites

- Python 3.12 or higher
- A Dropbox account with API access token
- AWS S3, Azure Blob Storage, or any S3-compatible storage account

## Installation

```bash
# Install uv (if not already installed)
pip install uv

# Clone and setup
git clone https://github.com/williamjshipman/dbx2s3.git
cd dbx2s3
uv sync
```

## Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your credentials:

### For Amazon S3:
```env
DROPBOX_TOKEN=your_dropbox_token
STORAGE_TYPE=s3
S3_BUCKET=my-backup-bucket
# Optional if running with IAM role or other default AWS credentials:
S3_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE
S3_SECRET_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
S3_REGION=us-east-1
```

### For Azure Blob Storage:
```env
DROPBOX_TOKEN=your_dropbox_token
STORAGE_TYPE=azure
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
AZURE_CONTAINER=dropbox-backup
```

### For S3-Compatible Storage (MinIO, DigitalOcean Spaces, etc.):
```env
DROPBOX_TOKEN=your_dropbox_token
STORAGE_TYPE=s3
S3_ENDPOINT=https://minio.example.com
S3_BUCKET=dropbox-backup
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
```

## Usage

### Basic backup (full Dropbox):
```bash
uv run python main.py
```

### Backup specific folder:
```bash
uv run python main.py --path /Documents
```

### Force full backup (ignore incremental state):
```bash
uv run python main.py --no-resume
```

### Verbose output for debugging:
```bash
uv run python main.py -v
```

## Getting Dropbox Token

1. Visit: https://www.dropbox.com/developers/apps
2. Click "Create app"
3. Choose "Scoped access" → "Full Dropbox"
4. Name your app
5. In "Permissions" tab, enable:
   - `files.metadata.read`
   - `files.content.read`
6. In "Settings" tab, generate access token

## What Gets Backed Up?

- All files in your Dropbox (or specified path)
- File metadata (revision, size, modification time)
- Directory structure is preserved

## Incremental Backups

The tool automatically tracks what's been backed up in `.dbx2s3_state.json`:
- Only changed files are uploaded on subsequent runs
- Uses Dropbox revision tracking
- Safe to interrupt (Ctrl+C) and resume later

## Troubleshooting

### "DROPBOX_TOKEN environment variable is required"
→ Make sure `.env` file exists and contains `DROPBOX_TOKEN=...`

### "Error uploading to S3"
→ Check bucket name, access keys, and region are correct
→ Verify bucket exists or tool has permission to create it

### "Error listing files from Dropbox"
→ Check Dropbox token is valid
→ Verify app has correct permissions

## File Locations

- Configuration: `.env` (or environment variables)
- State file: `.dbx2s3_state.json` (tracks backup progress)
- Logs: stdout/stderr (redirect to file if needed)

## Advanced Usage

See `examples/example_usage.py` for programmatic usage.

## Need Help?

- See full README.md for detailed documentation
- Check CONTRIBUTING.md for development setup
- Open an issue on GitHub

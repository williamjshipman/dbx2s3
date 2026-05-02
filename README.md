# dbx2s3

Backup Dropbox to any S3-compatible cloud storage.

## Features

- **Multiple Storage Backends**: Support for Amazon S3, Azure Blob Storage, and any S3-compatible storage
- **Incremental Backups**: Only backup files that have changed since the last backup
- **Resume Support**: Automatically resume interrupted backups
- **Simple Configuration**: Environment variable-based configuration
- **Flexible**: Backup entire Dropbox or specific folders

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for package management.

```bash
# Install uv if you haven't already
pip install uv

# Clone the repository
git clone https://github.com/williamjshipman/dbx2s3.git
cd dbx2s3

# Install dependencies
uv sync

# Run the tool
uv run python main.py
```

Alternatively, install as a package:

```bash
uv pip install .
```

## Configuration

Create a `.env` file in the project directory or set environment variables:

### Required for all configurations:

```env
DROPBOX_TOKEN=your_dropbox_access_token
STORAGE_TYPE=s3  # Options: s3, aws, azure
```

### For Amazon S3 or S3-compatible storage:

```env
STORAGE_TYPE=s3
S3_BUCKET=your-bucket-name
S3_ACCESS_KEY=your-access-key
S3_SECRET_KEY=your-secret-key
S3_REGION=us-east-1  # Optional, defaults to us-east-1
S3_ENDPOINT=https://custom-endpoint.com  # Optional, for non-AWS S3-compatible storage
```

### For Azure Blob Storage:

```env
STORAGE_TYPE=azure
AZURE_STORAGE_CONNECTION_STRING=your-connection-string
AZURE_CONTAINER=your-container-name
```

### Optional settings:

```env
STATE_FILE=.dbx2s3_state.json  # Path to state file for incremental backups
DROPBOX_RETRY_MAX_ATTEMPTS=3  # Total attempts for retryable Dropbox list/download calls
DROPBOX_RETRY_BASE_DELAY=1.0  # Base delay in seconds for exponential backoff
```

Retry handling applies to transient Dropbox listing and download failures. Dropbox rate-limit backoff is honored when the API provides one; otherwise the client uses bounded exponential backoff.

## Usage

### Basic backup (entire Dropbox):

```bash
uv run python main.py
```

### Backup a specific folder:

```bash
uv run python main.py --path /Documents
```

### Disable incremental backup (backup all files):

```bash
uv run python main.py --no-resume
```

### Enable verbose logging:

```bash
uv run python main.py -v
```

## Testing

```bash
uv run python -m unittest discover -s tests -p "test_*.py"
```

## Getting Dropbox Access Token

1. Go to [Dropbox App Console](https://www.dropbox.com/developers/apps)
2. Create a new app
3. Choose "Scoped access"
4. Choose "Full Dropbox" access
5. Name your app
6. Go to the "Permissions" tab and enable:
   - `files.metadata.read`
   - `files.content.read`
7. Generate an access token in the "Settings" tab

## How it Works

1. **Enumeration**: The tool connects to Dropbox and recursively lists all files
2. **State Check**: For each file, it checks the local state file to determine if the file has changed
3. **Download**: Changed files are downloaded from Dropbox
4. **Upload**: Files are uploaded to the configured storage backend
5. **State Update**: The local state is updated to track the backed-up files

The state file (`dbx2s3_state.json` by default) stores information about each backed-up file including:
- File revision
- File size
- Content hash (if available)
- Timestamp of backup

This allows the tool to skip unchanged files on subsequent runs, making backups faster and more efficient.

## Storage Backend Details

### Amazon S3
- Supports standard AWS S3
- Can use IAM credentials or access keys
- Supports all AWS regions

### S3-Compatible Storage
- Works with MinIO, DigitalOcean Spaces, Wasabi, etc.
- Requires custom endpoint URL
- Use same configuration as S3 with `S3_ENDPOINT` set

### Azure Blob Storage
- Uses connection string authentication
- Automatically creates container if it doesn't exist
- Stores files as blobs with metadata

## Error Handling

- The tool logs errors but continues processing other files
- Failed files are not marked as backed up in the state
- On the next run, failed files will be retried
- Use Ctrl+C to interrupt; the tool will save state and can resume later

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.


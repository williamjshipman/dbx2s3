# Troubleshooting Guide

## Common Issues and Solutions

### Configuration Issues

#### Error: "DROPBOX_TOKEN environment variable is required"
**Cause**: The tool can't find your Dropbox access token.

**Solutions**:
1. Create a `.env` file in the project root
2. Add `DROPBOX_TOKEN=your_token_here`
3. Or set the environment variable: `export DROPBOX_TOKEN=your_token`

#### Error: "S3_ACCESS_KEY, S3_SECRET_KEY, and S3_BUCKET are required"
**Cause**: Missing S3 configuration.

**Solutions**:
1. Add to `.env`:
   ```
   S3_ACCESS_KEY=your_access_key
   S3_SECRET_KEY=your_secret_key
   S3_BUCKET=your-bucket-name
   ```
2. For AWS, you can also use `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`

#### Error: "Unsupported storage type"
**Cause**: STORAGE_TYPE has an invalid value.

**Solutions**:
- Valid values are: `s3`, `aws`, or `azure`
- Set in `.env`: `STORAGE_TYPE=s3`

### Dropbox Issues

#### Error: "Error listing files" or Dropbox API errors
**Possible causes**:
1. Invalid or expired access token
2. Missing permissions
3. Network connectivity issues

**Solutions**:
1. Generate a new access token from Dropbox App Console
2. Ensure your app has these permissions:
   - `files.metadata.read`
   - `files.content.read`
3. Check internet connection
4. Try with `-v` flag for verbose logging

#### Files not appearing in backup
**Possible causes**:
1. Files in specific folder not being scanned
2. Incremental backup skipping unchanged files

**Solutions**:
1. Check the path: `uv run python main.py --path /YourFolder`
2. Force full backup: `uv run python main.py --no-resume`
3. Use verbose mode to see what's happening: `uv run python main.py -v`

### Storage Issues

#### Error: "Error uploading to S3"
**Possible causes**:
1. Invalid credentials
2. Bucket doesn't exist and can't be created
3. Insufficient permissions
4. Network issues

**Solutions**:
1. Verify credentials are correct
2. Manually create the bucket first
3. Check IAM permissions include: `s3:PutObject`, `s3:GetObject`, `s3:ListBucket`
4. For custom S3 endpoints, verify `S3_ENDPOINT` is correct
5. Check network/firewall settings

#### Error: "NoSuchBucket"
**Cause**: S3 bucket doesn't exist.

**Solutions**:
1. Create the bucket manually in AWS console
2. Ensure the tool has permission to create buckets (`s3:CreateBucket`)
3. Check region is correct if using AWS

#### Azure Blob Storage errors
**Possible causes**:
1. Invalid connection string
2. Container doesn't exist

**Solutions**:
1. Verify connection string format:
   ```
   DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net
   ```
2. Check container name (lowercase, no spaces)
3. Ensure storage account exists

### Performance Issues

#### Backup is very slow
**Possible causes**:
1. Large files
2. Network bandwidth
3. API rate limits

**Solutions**:
1. Be patient - first backup takes longest
2. Subsequent backups are incremental and faster
3. Check your internet connection speed
4. Consider backing up in smaller chunks using `--path`

#### High memory usage
**Cause**: Large files are loaded entirely into memory.

**Solutions**:
1. This is expected for large files
2. System will handle it, but may be slow
3. Future versions may add streaming support

### State File Issues

#### Error: "Error loading state file"
**Cause**: Corrupted state file.

**Solutions**:
1. Usually safe to ignore on first run
2. If persistent, delete `.dbx2s3_state.json` and restart
3. This will trigger a full backup

#### State file keeps growing
**Cause**: Normal behavior - tracks all files.

**Solutions**:
1. This is expected and necessary for incremental backups
2. File size should stabilize after full backup
3. Safe to delete and rebuild if needed

### Installation Issues

#### Error: "uv: command not found"
**Cause**: UV package manager not installed.

**Solutions**:
```bash
pip install uv
```

#### Error: "ImportError: No module named 'dropbox'"
**Cause**: Dependencies not installed.

**Solutions**:
```bash
cd /path/to/dbx2s3
uv sync
```

### Debugging Tips

1. **Use verbose mode**:
   ```bash
   uv run python main.py -v
   ```

2. **Check environment variables**:
   ```bash
   cat .env
   ```

3. **Test Dropbox connection**:
   ```bash
   uv run python -c "
   import os
   from dotenv import load_dotenv
   import dropbox
   load_dotenv()
   dbx = dropbox.Dropbox(os.getenv('DROPBOX_TOKEN'))
   print(dbx.users_get_current_account())
   "
   ```

4. **Test S3 connection**:
   ```bash
   uv run python -c "
   import os
   from dotenv import load_dotenv
   import boto3
   load_dotenv()
   s3 = boto3.client('s3',
       aws_access_key_id=os.getenv('S3_ACCESS_KEY'),
       aws_secret_access_key=os.getenv('S3_SECRET_KEY'))
   print(s3.list_buckets())
   "
   ```

5. **Check Python version**:
   ```bash
   python3 --version  # Should be 3.12 or higher
   ```

## Getting Help

If none of these solutions work:

1. Check the logs carefully for specific error messages
2. Review the README.md and QUICKSTART.md
3. Check if it's a known issue on GitHub
4. Open a new issue with:
   - Full error message
   - Command you ran
   - Python version
   - Operating system
   - Relevant parts of your configuration (DO NOT include tokens/keys)

## Security Notes

- Never share your `.env` file or access tokens
- Don't commit `.env` to version control (already in .gitignore)
- Rotate tokens regularly
- Use IAM roles when possible instead of long-lived credentials

# AMMA MinIO Buckets

MinIO is used as S3-compatible cold/object storage.

Recommended buckets:

| Bucket | Purpose |
|---|---|
| `amma-receipts` | Uploaded receipt images and bills |
| `amma-reports` | Exported monthly PDF/CSV reports |
| `amma-analytics-snapshots` | Archived analytics snapshots |
| `amma-agent-archives` | Long-term AI conversation archive, if needed |

Open console:

```text
http://localhost:9001
```

Default local credentials:

```text
user: minio
password: minio123
```

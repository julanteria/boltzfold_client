# Quick Start Guide

Get up and running with BoltzFold Python client in minutes!

## Installation

```bash
pip install boltzfold-client
```

## 5-Minute Tutorial

### 1. Basic Structure Prediction

```python
from boltzfold_client import BoltzFoldClient

# Create client
client = BoltzFoldClient()

# Submit prediction
response = client.submit_prediction(
    model="boltz",
    sequence="MSEQNNTEMTFQIQRIYTKDISFEAPNHFIRVTELPSQYRSGWGDHKD"
)

# Get job URL
print(f"Track at: {client.job_url(response.job_id)}")

# Watch progress
for status in client.watch_job(response.job_id, poll_interval=5):
    print(f"{status.status}: {status.message or ''}")
    if status.status in {"succeeded", "failed"}:
        break

# Download results
if status.succeeded():
    print(f"PDB: {status.pdb_url}")
    print(f"CIF: {status.cif_url}")
```

### 2. Binder Design (Boltz-2)

```python
from boltzfold_client import BoltzFoldClient

client = BoltzFoldClient()

# Predict binder-target complex
response = client.submit_binder_target_prediction(
    binder_sequence="ACDEFGHIKLMNPQRSTVWY",
    target_sequence="MSEQNNTEMTFQIQRIYTKDISFEAPNHFIRVTELPSQYRSGWGDHKD",
)

print(f"Job: {response.job_id}")
```

### 3. Batch Processing

```python
from boltzfold_client import (
    BoltzFoldClient,
    iter_fasta,
    monitor_jobs,
)

client = BoltzFoldClient()

# Submit multiple sequences
jobs = []
for name, sequence in iter_fasta("sequences.fasta"):
    response = client.submit_prediction(
        model="boltz",
        sequence=sequence,
    )
    jobs.append((name, response.job_id))

# Monitor all at once
results = monitor_jobs(client, jobs, poll_interval=5)

# Check results
for name, job_id in jobs:
    status = results[job_id]
    print(f"{name}: {status.status}")
```

### 4. BoltzGen Binder Design

```python
from boltzfold_client import BoltzFoldClient, monitor_job

client = BoltzFoldClient()

response = client.submit_prediction(
    model="boltzgen",
    sequence="A",  # placeholder
    target_file_path="target_structure.pdb",
    length=(70, 140),
    epitope={"chain": "A", "residues": [491, 506, 512]},
    num_designs=20,
)

# Monitor with live display
final_status = monitor_job(client, response.job_id)

if final_status.succeeded():
    print(f"Designs: {final_status.design_bundle_url}")
```

## Common Patterns

### Load Sequences from Files

```python
from boltzfold_client import load_first_sequence, iter_fasta

# Single sequence
seq = load_first_sequence("protein.fasta")

# Multiple sequences
for name, seq in iter_fasta("proteins.fasta"):
    print(f"{name}: {len(seq)} residues")
```

### Async Client

```python
from boltzfold_client import AsyncBoltzFoldClient

async def predict():
    async with AsyncBoltzFoldClient() as client:
        response = await client.submit_prediction(
            model="boltz",
            sequence="ACDEFG...",
        )
        
        async for status in client.watch_job(response.job_id):
            print(status.status)
            if status.status in {"succeeded", "failed"}:
                break

# Run with asyncio
import asyncio
asyncio.run(predict())
```

### Custom Base URL

```python
from boltzfold_client import BoltzFoldClient

# Use different server
client = BoltzFoldClient(
    base_url="https://custom-server.com",
    request_timeout=60.0,
    read_timeout=600.0,
)
```

## Next Steps

- **Full Documentation**: See [README.md](README.md)
- **Examples**: Check out the [examples/](examples/) directory
- **API Reference**: Visit https://boltzfold.com/docs

## Getting Help

- **Issues**: https://github.com/yourusername/boltzfold_client/issues
- **Discussions**: https://github.com/yourusername/boltzfold_client/discussions

## Tips

1. **Use context managers** for automatic cleanup:
   ```python
   with BoltzFoldClient() as client:
       # Your code here
       pass
   # Client automatically closed
   ```

2. **Check job status** before downloading:
   ```python
   status = client.fetch_status(job_id)
   if status.succeeded():
       # Download results
       pass
   ```

3. **Handle errors gracefully**:
   ```python
   try:
       response = client.submit_prediction(...)
   except Exception as e:
       print(f"Error: {e}")
   ```

4. **Batch submissions** for efficiency:
   ```python
   # Better: Submit all first, then monitor
   job_ids = [client.submit_prediction(...).job_id for _ in range(10)]
   results = monitor_jobs(client, dict(enumerate(job_ids)))
   ```

Happy predicting!


# BoltzFold Python Client


Lightweight Python client for the [BoltzFold](https://boltzfold.com) API - protein structure prediction and binder design made simple.

## Features

- **Simple API** - Submit predictions with just a few lines of code
- **Async Support** - Both synchronous and async clients available
- **Job Monitoring** - Built-in utilities for tracking job progress
- **FASTA Helpers** - Convenient utilities for working with sequence files
- **Lightweight** - Minimal dependencies (just `httpx`)
- **Type Hints** - Full typing support for better IDE experience

## Installation

```bash
pip install boltzfold-client
```

Or install from source:

```bash
git clone https://github.com/julanteria/boltzfold_client.git
cd boltzfold_client
pip install -e .
```

## Quick Start

### Basic Protein Structure Prediction

```python
from boltzfold_client import BoltzFoldClient

client = BoltzFoldClient(base_url="https://boltzfold.com")

# Submit a prediction job
response = client.submit_prediction(
    model="boltz",
    sequence="MSEQNNTEMTFQIQRIYTKDISF...",
)

print(f"Job ID: {response.job_id}")
print(f"Job URL: {client.job_url(response.job_id)}")

# Watch job progress
for status in client.watch_job(response.job_id, poll_interval=5):
    print(f"Status: {status.status} - {status.message or ''}")
    if status.status in {"succeeded", "failed"}:
        break

# Get final results
if status.succeeded():
    print(f"Download PDB: {status.pdb_url}")
    print(f"Download CIF: {status.cif_url}")
```

### Binder Design with BoltzGen

```python
from boltzfold_client import BoltzFoldClient

client = BoltzFoldClient()

response = client.submit_prediction(
    model="boltzgen",
    sequence="A",  # placeholder for BoltzGen
    target_file_path="/path/to/target_structure.pdb",
    length="70-140",
    epitope={"chain": "A", "residues": [491, 532, 506]},
    num_designs=20,
)

# Monitor with fancy display
from boltzfold_client import monitor_job

final_status = monitor_job(client, response.job_id, poll_interval=2.0)
if final_status.succeeded():
    print(f"Download designs: {final_status.design_bundle_url}")
```

### Binder vs Target Predictions (Boltz-2)

```python
from boltzfold_client import BoltzFoldClient

client = BoltzFoldClient()

response = client.submit_binder_target_prediction(
    binder_sequence="ACDEFGHIKLMNPQRSTVWY",
    target_sequence="MSEQNNTEMTFQIQRIYTKDISF",
    extra={"job_name": "my_binder_design"},
)
```

### Batch Processing with FASTA Files

```python
from boltzfold_client import (
    BoltzFoldClient,
    iter_fasta,
    load_first_sequence,
    chunked,
    monitor_jobs,
)

client = BoltzFoldClient()

# Load target sequence
target = load_first_sequence("target.fasta")

# Submit batch of binder designs
jobs = []
for name, binder in iter_fasta("binder_designs.fasta"):
    response = client.submit_binder_target_prediction(
        binder_sequence=binder,
        target_sequence=target,
        extra={"job_name": name},
    )
    jobs.append((name, response.job_id))
    print(f"Submitted {name} -> {response.job_id}")

# Monitor all jobs at once
final_statuses = monitor_jobs(client, jobs, poll_interval=5.0)

# Print summary
for name, job_id in jobs:
    status = final_statuses[job_id]
    print(f"{name}: {status.status}")
```

## API Reference

### BoltzFoldClient

Main synchronous client for the BoltzFold API.

#### Methods

- **`submit_prediction(**params)`** - Submit a prediction job
  - `model`: Model to use (`"boltz"`, `"boltzgen"`, `"openfold3"`)
  - `sequence`: Protein sequence
  - `target_file_path`: Path to target structure (for BoltzGen)
  - `target_url`: URL to target structure
  - `length`: Binder length range (e.g., `"70-140"` or `(70, 140)`)
  - `epitope`: Epitope specification (dict with `chain` and `residues`)
  - `num_designs`: Number of designs to generate
  - `binder_sequence`: Binder sequence (for Boltz-2)
  - `target_sequence`: Target sequence (for Boltz-2)
  - `extra`: Additional parameters

- **`submit_binder_target_prediction(...)`** - Convenience method for binder/target jobs

- **`submit_bulk_predictions(payloads)`** - Submit multiple predictions

- **`submit_binder_target_batch(jobs, **common_params)`** - Batch binder/target submission

- **`fetch_status(job_id)`** - Get current job status

- **`watch_job(job_id, poll_interval=5.0, timeout=None)`** - Iterator that polls until completion

- **`job_url(job_id)`** - Get web URL for a job

### AsyncBoltzFoldClient

Async variant of the client using `httpx.AsyncClient`.

```python
from boltzfold_client import AsyncBoltzFoldClient

async with AsyncBoltzFoldClient() as client:
    response = await client.submit_prediction(model="boltz", sequence="ACDE...")
    
    async for status in client.watch_job(response.job_id, poll_interval=5):
        print(f"Status: {status.status}")
        if status.status in {"succeeded", "failed"}:
            break
```

### Monitoring Utilities

- **`monitor_job(client, job_id, ...)`** - Monitor single job with live display
- **`monitor_jobs(client, jobs, ...)`** - Monitor multiple jobs concurrently
- **`format_job_summary(rows)`** - Format job results as a table
- **`print_job_summary(rows)`** - Print formatted job summary

### Sequence Utilities

- **`load_first_sequence(path)`** - Load first sequence from FASTA or plain text
- **`iter_fasta(path)`** - Iterate over all sequences in a FASTA file
- **`chunked(iterable, size)`** - Split an iterable into fixed-size chunks

## Development

### Setup

```bash
git clone https://github.com/yourusername/boltzfold_client.git
cd boltzfold_client
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Building

```bash
python -m build
```

## Models

### Supported Prediction Models

- **Boltz-2**: Protein-ligand and protein-protein structure prediction with affinity estimates
- **BoltzGen**: Binder design (requires target structures, API-only)
- **OpenFold-3**: Protein-only structure prediction

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Links

- **BoltzFold Website**: https://boltzfold.com
- **API Documentation**: https://boltzfold.com/docs
- **Issues**: https://github.com/julanteria/boltzfold_client/issues

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Citation

If you use BoltzFold in your research, please cite:

```bibtex
@software{boltzfold2024,
  title = {BoltzFold: Protein Structure Prediction as a Service},
  author = {Your Name},
  year = {2024},
  url = {https://boltzfold.com}
}
```


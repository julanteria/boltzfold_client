#!/usr/bin/env python3
"""Basic example: Submit a protein structure prediction and monitor progress."""

from boltzfold_client import BoltzFoldClient, monitor_job

# Create client (defaults to https://boltzfold.com)
client = BoltzFoldClient()

# Example protein sequence (truncated for brevity)
sequence = "MSEQNNTEMTFQIQRIYTKDISFEAPNHFIRVTELPSQYRSGWGDHKDVPQGSTYLTFNGD"

# Submit prediction job
print("Submitting prediction job...")
response = client.submit_prediction(
    model="boltz",
    sequence=sequence,
)

print(f"✓ Job submitted: {response.job_id}")
print(f"  Web URL: {client.job_url(response.job_id)}")

# Monitor job with live updates
print("\nMonitoring job progress...")
final_status = monitor_job(client, response.job_id, poll_interval=5.0)

# Check results
if final_status.succeeded():
    print("\n✓ Prediction completed successfully!")
    print(f"  Download PDB: {final_status.pdb_url}")
    print(f"  Download CIF: {final_status.cif_url}")
    if final_status.metrics_url:
        print(f"  Metrics: {final_status.metrics_url}")
else:
    print("\n✗ Prediction failed")
    print(f"  Error: {final_status.message}")

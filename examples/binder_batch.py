#!/usr/bin/env python3
"""Example: Batch processing of binder designs against a target."""

from boltzfold_client import (
    BoltzFoldClient,
    JobSummary,
    iter_fasta,
    load_first_sequence,
    monitor_jobs,
    print_job_summary,
)

# Paths to your data
TARGET_FASTA = "target.fasta"  # Single sequence file
BINDER_DESIGNS = "binder_designs.fasta"  # Multiple binder sequences

# Initialize client
client = BoltzFoldClient()

# Load target sequence
print("Loading target sequence...")
target = load_first_sequence(TARGET_FASTA)
print(f"  Target length: {len(target)} residues")

# Submit batch of binder designs
print(f"\nSubmitting binder designs from {BINDER_DESIGNS}...")
jobs = []
for name, binder in iter_fasta(BINDER_DESIGNS):
    response = client.submit_binder_target_prediction(
        binder_sequence=binder,
        target_sequence=target,
        extra={"job_name": name},
    )
    jobs.append((name, response.job_id))
    print(f"  ✓ Submitted {name} -> {response.job_id}")

print(f"\nSubmitted {len(jobs)} jobs. Monitoring progress...")

# Monitor all jobs concurrently
final_statuses = monitor_jobs(
    client,
    jobs,
    poll_interval=5.0,
    timeout=3600,  # 1 hour timeout
)

# Build summary
summaries = []
for name, job_id in jobs:
    status = final_statuses[job_id]
    summaries.append(JobSummary.from_status(name, status))

# Print results table
print("\nFinal Results:")
print_job_summary(summaries, include_job_url=True)

# Save successful predictions info to file
with open("successful_predictions.txt", "w") as f:
    for summary in summaries:
        if summary.succeeded():
            f.write(f"{summary.name}\t{summary.job_id}\t{summary.pdb_url}\n")

print("\nSuccessful predictions saved to successful_predictions.txt")

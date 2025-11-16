#!/usr/bin/env python3
"""Example: BoltzGen binder design with epitope targeting."""

from boltzfold_client import BoltzFoldClient, monitor_job

# Initialize client
client = BoltzFoldClient()

# BoltzGen parameters
TARGET_PDB = "target_structure.pdb"  # Your target structure
EPITOPE = {
    "chain": "A",
    "residues": [491, 532, 506, 512, 515],  # Key residues to target
}
BINDER_LENGTH = (70, 140)  # Desired binder length range
NUM_DESIGNS = 20  # Number of designs to generate

print("Submitting BoltzGen binder design job...")
response = client.submit_prediction(
    model="boltzgen",
    sequence="A",  # Placeholder for BoltzGen
    target_file_path=TARGET_PDB,
    length=BINDER_LENGTH,
    epitope=EPITOPE,
    num_designs=NUM_DESIGNS,
)

print(f"✓ Job submitted: {response.job_id}")
print(f"  Web URL: {client.job_url(response.job_id)}")
print(f"\nDesigning {NUM_DESIGNS} binders for epitope residues: {EPITOPE['residues']}")

# Monitor with live display
print("\nMonitoring design progress...")
final_status = monitor_job(client, response.job_id, poll_interval=10.0)

# Check results
if final_status.succeeded():
    print("\n✓ Design completed successfully!")
    if final_status.design_bundle_url:
        print(f"  Download all designs: {final_status.design_bundle_url}")
    print(f"\nNext steps:")
    print(f"  1. Download and extract the design bundle")
    print(f"  2. Review designs in PyMOL or similar viewer")
    print(f"  3. Select top candidates for validation")
else:
    print("\n✗ Design failed")
    print(f"  Error: {final_status.message}")

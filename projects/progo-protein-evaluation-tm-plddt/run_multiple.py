# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

#!/usr/bin/env python3
"""
Script to run multiple pipeline configurations
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Configuration
FASTA_FILES = [
    "set07_test.fasta",
    "set08_test.fasta", 
    "test_local.fasta"
]

GROUND_TRUTH_SETS = ["set07", "set08"]

# Optional: Define specific combinations instead of all
SPECIFIC_RUNS = [
    # (fasta_file, ground_truth_set)
    # ("set07_test.fasta", "set07"),  # Match set07 sequences to set07 ground truth
    # ("set08_test.fasta", "set08"),  # Match set08 sequences to set08 ground truth
    # ("set07_test.fasta", "set08"),  # Cross-evaluation
]

def run_pipeline(fasta_file, ground_truth_set):
    """Run the pipeline with given parameters."""
    print(f"\n{'='*60}")
    print(f"Running: {fasta_file} against {ground_truth_set}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    cmd = [
        sys.executable, "-m", "src.main",
        "predict-and-evaluate",
        "--fasta", fasta_file,
        "--ground-truth-set", ground_truth_set
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("SUCCESS!")
        
        # Extract key information from output
        for line in result.stdout.split('\n'):
            if any(keyword in line for keyword in [
                "Skipped", "Output directory created:", 
                "Results saved to", "Pipeline completed"
            ]):
                print(f"  {line.strip()}")
                
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Pipeline failed with exit code {e.returncode}")
        print(f"Error output: {e.stderr}")
        return False
    
    return True

def main():
    """Run multiple pipeline configurations."""
    successful_runs = []
    failed_runs = []
    
    # Use specific runs if defined, otherwise run all combinations
    if SPECIFIC_RUNS:
        runs_to_execute = SPECIFIC_RUNS
    else:
        runs_to_execute = [
            (fasta, gt_set) 
            for fasta in FASTA_FILES 
            for gt_set in GROUND_TRUTH_SETS
        ]
    
    print(f"Planning to execute {len(runs_to_execute)} runs:")
    for fasta, gt_set in runs_to_execute:
        print(f"  - {fasta} → {gt_set}")
    
    # Execute runs
    for fasta, gt_set in runs_to_execute:
        if run_pipeline(fasta, gt_set):
            successful_runs.append((fasta, gt_set))
        else:
            failed_runs.append((fasta, gt_set))
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Total runs: {len(runs_to_execute)}")
    print(f"Successful: {len(successful_runs)}")
    print(f"Failed: {len(failed_runs)}")
    
    if failed_runs:
        print("\nFailed runs:")
        for fasta, gt_set in failed_runs:
            print(f"  - {fasta} → {gt_set}")
    
    # Show output directories
    print("\nOutput directories created:")
    output_dir = Path("data/output")
    if output_dir.exists():
        for dir_path in sorted(output_dir.iterdir()):
            if dir_path.is_dir():
                print(f"  - {dir_path.name}/")
    
if __name__ == "__main__":
    main() 
# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

#!/usr/bin/env python3
"""
Simple command-line runner for PRO-GO_Eval_TopTMscore pipeline

Usage:
    python run_simple.py <fasta_files> <ground_truth_sets>
    
Examples:
    python run_simple.py test.fasta set08
    python run_simple.py "test1.fasta,test2.fasta" "set07,set08"
    python run_simple.py ALL set08
    python run_simple.py test.fasta ALL
"""

import subprocess
import sys
from pathlib import Path

def get_available_files():
    """Get lists of available FASTA files and ground truth sets."""
    fasta_dir = Path("data/input")
    fasta_files = [f.name for f in fasta_dir.glob("*.fasta")] if fasta_dir.exists() else []
    
    gt_dir = Path("data/ground_truth")
    gt_sets = [d.name for d in gt_dir.iterdir() if d.is_dir() and (d / "pdbs").exists()] if gt_dir.exists() else []
    
    return fasta_files, gt_sets

def run_pipeline(fasta_file, ground_truth_set):
    """Run the pipeline with given parameters."""
    print(f"\nRunning: {fasta_file} → {ground_truth_set}")
    
    cmd = [
        sys.executable, "-m", "src.main",
        "predict-and-evaluate",
        "--fasta", fasta_file,
        "--ground-truth-set", ground_truth_set
    ]
    
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    if len(sys.argv) != 3:
        print(__doc__)
        print("\nAvailable files:")
        fasta_files, gt_sets = get_available_files()
        print(f"  FASTA files: {', '.join(fasta_files) if fasta_files else 'None found'}")
        print(f"  Ground truth sets: {', '.join(gt_sets) if gt_sets else 'None found'}")
        sys.exit(1)
    
    fasta_arg = sys.argv[1]
    gt_arg = sys.argv[2]
    
    # Get available files
    available_fastas, available_gts = get_available_files()
    
    # Parse FASTA files
    if fasta_arg.upper() == "ALL":
        fasta_files = available_fastas
    else:
        fasta_files = [f.strip() for f in fasta_arg.split(",")]
        # Validate FASTA files exist
        for f in fasta_files:
            if f not in available_fastas:
                print(f"Error: FASTA file '{f}' not found in data/input/")
                print(f"Available: {', '.join(available_fastas)}")
                sys.exit(1)
    
    # Parse ground truth sets
    if gt_arg.upper() == "ALL":
        gt_sets = available_gts
    else:
        gt_sets = [g.strip() for g in gt_arg.split(",")]
        # Validate ground truth sets exist
        for g in gt_sets:
            if g not in available_gts:
                print(f"Error: Ground truth set '{g}' not found in data/ground_truth/")
                print(f"Available: {', '.join(available_gts)}")
                sys.exit(1)
    
    # Run combinations
    total = len(fasta_files) * len(gt_sets)
    print(f"Running {total} combinations...")
    
    successful = 0
    for fasta in fasta_files:
        for gt in gt_sets:
            if run_pipeline(fasta, gt):
                successful += 1
    
    print(f"\nCompleted: {successful}/{total} successful")

if __name__ == "__main__":
    main() 
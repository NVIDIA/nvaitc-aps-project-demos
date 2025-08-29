# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

#!/usr/bin/env python3
"""
Simple batch runner for PRO-GO_Eval_TopTMscore pipeline
Allows users to specify which FASTA files and ground truth sets to use
"""

import subprocess
import sys
from pathlib import Path

def get_available_files():
    """Get lists of available FASTA files and ground truth sets."""
    # Get FASTA files from data/input/
    fasta_dir = Path("data/input")
    fasta_files = sorted([f.name for f in fasta_dir.glob("*.fasta")]) if fasta_dir.exists() else []
    
    # Get ground truth sets from data/ground_truth/
    gt_dir = Path("data/ground_truth")
    gt_sets = sorted([d.name for d in gt_dir.iterdir() if d.is_dir() and (d / "pdbs").exists()]) if gt_dir.exists() else []
    
    return fasta_files, gt_sets

def run_pipeline(fasta_file, ground_truth_set):
    """Run the pipeline with given parameters."""
    print(f"\nRunning: {fasta_file} → {ground_truth_set}")
    print("-" * 50)
    
    cmd = [
        sys.executable, "-m", "src.main",
        "predict-and-evaluate",
        "--fasta", fasta_file,
        "--ground-truth-set", ground_truth_set
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"✓ Completed: {fasta_file} → {ground_truth_set}")
        return True
    except subprocess.CalledProcessError:
        print(f"✗ Failed: {fasta_file} → {ground_truth_set}")
        return False

def main():
    print("PRO-GO_Eval_TopTMscore Batch Runner")
    print("=" * 50)
    
    # Get available files
    fasta_files, gt_sets = get_available_files()
    
    # Show available options
    print("\nAvailable FASTA files:")
    if fasta_files:
        for i, f in enumerate(fasta_files, 1):
            print(f"  {i}. {f}")
    else:
        print("  No FASTA files found in data/input/")
        return
    
    print("\nAvailable ground truth sets:")
    if gt_sets:
        for i, g in enumerate(gt_sets, 1):
            print(f"  {i}. {g}")
    else:
        print("  No ground truth sets found in data/ground_truth/")
        return
    
    # Get user input
    print("\nEnter the numbers of FASTA files to process (comma-separated, or 'all'):")
    fasta_input = input("> ").strip()
    
    if fasta_input.lower() == 'all':
        selected_fastas = fasta_files
    else:
        try:
            indices = [int(x.strip()) - 1 for x in fasta_input.split(',')]
            selected_fastas = [fasta_files[i] for i in indices if 0 <= i < len(fasta_files)]
        except (ValueError, IndexError):
            print("Invalid input for FASTA files")
            return
    
    print("\nEnter the numbers of ground truth sets to use (comma-separated, or 'all'):")
    gt_input = input("> ").strip()
    
    if gt_input.lower() == 'all':
        selected_gts = gt_sets
    else:
        try:
            indices = [int(x.strip()) - 1 for x in gt_input.split(',')]
            selected_gts = [gt_sets[i] for i in indices if 0 <= i < len(gt_sets)]
        except (ValueError, IndexError):
            print("Invalid input for ground truth sets")
            return
    
    # Confirm runs
    print(f"\nWill run {len(selected_fastas)} × {len(selected_gts)} = {len(selected_fastas) * len(selected_gts)} combinations:")
    for fasta in selected_fastas:
        for gt in selected_gts:
            print(f"  - {fasta} → {gt}")
    
    confirm = input("\nProceed? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled")
        return
    
    # Run combinations
    print("\nStarting batch run...")
    successful = 0
    failed = 0
    
    for fasta in selected_fastas:
        for gt in selected_gts:
            if run_pipeline(fasta, gt):
                successful += 1
            else:
                failed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"Batch run complete: {successful} successful, {failed} failed")
    print(f"Results saved in: data/output/")

if __name__ == "__main__":
    main() 
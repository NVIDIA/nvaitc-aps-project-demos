# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

#!/usr/bin/env python3
"""
Script to compare results across multiple pipeline runs
"""

import json
from pathlib import Path
import pandas as pd

def load_analysis_results(output_dir):
    """Load analysis results from a run directory."""
    json_file = output_dir / "analysis" / "analysis_results.json"
    if json_file.exists():
        with open(json_file) as f:
            return json.load(f)
    return None

def compare_runs():
    """Compare results across all runs in the output directory."""
    output_base = Path("data/output")
    
    # Collect results from all runs
    all_results = []
    
    for run_dir in sorted(output_base.iterdir()):
        if run_dir.is_dir():
            results = load_analysis_results(run_dir)
            if results:
                summary = results['summary']
                all_results.append({
                    'Run': run_dir.name,
                    'Total Structures': summary['total_structures'],
                    'Successful': summary['successful_comparisons'],
                    'Failed': summary['failed_comparisons'],
                    'Best TM-Score': f"{summary['best_overall_score']:.3f}",
                    'Avg TM-Score': f"{summary['average_score']:.3f}",
                    'Skipped Duplicates': summary['skipped_duplicates'],
                    'Reference Matches': summary['exact_reference_matches']
                })
    
    if not all_results:
        print("No analysis results found in data/output/")
        return
    
    # Create DataFrame and display
    df = pd.DataFrame(all_results)
    
    print("\n" + "="*80)
    print("COMPARISON OF ALL RUNS")
    print("="*80)
    print(df.to_string(index=False))
    
    # Save to CSV
    csv_file = output_base / "comparison_summary.csv"
    df.to_csv(csv_file, index=False)
    print(f"\nComparison saved to: {csv_file}")
    
    # Additional analysis
    print("\n" + "="*80)
    print("INSIGHTS")
    print("="*80)
    
    # Best performing runs
    if len(df) > 0:
        best_avg = df.loc[df['Avg TM-Score'].astype(float).idxmax()]
        print(f"Best Average TM-Score: {best_avg['Run']} ({best_avg['Avg TM-Score']})")
        
        best_max = df.loc[df['Best TM-Score'].astype(float).idxmax()]
        print(f"Best Maximum TM-Score: {best_max['Run']} ({best_max['Best TM-Score']})")
        
        # Runs with skipped sequences
        skipped = df[df['Skipped Duplicates'] > 0]
        if not skipped.empty:
            print(f"\nRuns with skipped duplicates ({len(skipped)}):")
            for _, row in skipped.iterrows():
                print(f"  - {row['Run']}: {row['Skipped Duplicates']} skipped")

if __name__ == "__main__":
    try:
        compare_runs()
    except ImportError:
        print("Note: pandas is required for the comparison script")
        print("Install with: pip install pandas") 
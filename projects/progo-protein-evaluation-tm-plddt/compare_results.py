# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

#!/usr/bin/env python3
"""
Simple script to compare results across multiple runs
No external dependencies required
"""

import json
from pathlib import Path

def load_analysis_results(output_dir):
    """Load analysis results from a run directory."""
    json_file = output_dir / "analysis" / "analysis_results.json"
    if json_file.exists():
        with open(json_file) as f:
            return json.load(f)
    return None

def main():
    output_base = Path("data/output")
    
    # Collect results
    results = []
    for run_dir in sorted(output_base.iterdir()):
        if run_dir.is_dir():
            data = load_analysis_results(run_dir)
            if data:
                summary = data['summary']
                results.append({
                    'name': run_dir.name,
                    'total': summary['total_structures'],
                    'success': summary['successful_comparisons'],
                    'failed': summary['failed_comparisons'],
                    'best': summary['best_overall_score'],
                    'avg': summary['average_score'],
                    'skipped': summary.get('skipped_duplicates', 0)  # Handle older runs
                })
    
    if not results:
        print("No results found in data/output/")
        return
    
    # Display results
    print("\nCOMPARISON OF ALL RUNS")
    print("=" * 80)
    print(f"{'Run Name':<30} {'Total':<8} {'Success':<8} {'Failed':<8} {'Best TM':<10} {'Avg TM':<10} {'Skipped':<8}")
    print("-" * 80)
    
    for r in results:
        print(f"{r['name']:<30} {r['total']:<8} {r['success']:<8} {r['failed']:<8} {r['best']:<10.3f} {r['avg']:<10.3f} {r['skipped']:<8}")
    
    # Find best runs
    if results:
        best_avg = max(results, key=lambda x: x['avg'])
        best_max = max(results, key=lambda x: x['best'])
        
        print(f"\nBest average TM-score: {best_avg['name']} ({best_avg['avg']:.3f})")
        print(f"Best maximum TM-score: {best_max['name']} ({best_max['best']:.3f})")

if __name__ == "__main__":
    main() 
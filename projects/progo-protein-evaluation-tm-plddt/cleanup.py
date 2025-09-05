# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

#!/usr/bin/env python3
"""
Cleanup script for PRO-GO_Eval_TopTMscore pipeline.
Removes all output directories from previous runs.
"""

import shutil
from pathlib import Path
import sys

def main():
    """Remove all output directories from data/output/"""
    output_dir = Path("data/output")
    
    if not output_dir.exists():
        print("No output directory found.")
        return
    
    # Count directories to be removed
    dirs_to_remove = [d for d in output_dir.iterdir() if d.is_dir()]
    
    if not dirs_to_remove:
        print("No output directories to clean.")
        return
    
    print(f"Found {len(dirs_to_remove)} output directories:")
    for d in dirs_to_remove:
        print(f"  - {d.name}")
    
    # Ask for confirmation
    response = input(f"\nRemove all {len(dirs_to_remove)} directories? [y/N]: ")
    if response.lower() != 'y':
        print("Cancelled.")
        return
    
    # Remove all directories
    removed_count = 0
    for d in dirs_to_remove:
        try:
            print(f"Removing {d.name}...")
            shutil.rmtree(d)
            removed_count += 1
        except Exception as e:
            print(f"Error removing {d.name}: {e}")
    
    print(f"\nSuccessfully removed {removed_count} output directories.")

if __name__ == "__main__":
    main() 
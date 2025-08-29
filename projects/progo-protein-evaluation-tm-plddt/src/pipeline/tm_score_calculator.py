# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Structure comparison module for ProteinGO pipeline.
Handles structure comparison using Foldseek.
"""

import subprocess
from pathlib import Path
import platform
import os
import shutil
from typing import Dict, Optional, Tuple, List
import re
from tqdm import tqdm
import json
import biotite.structure.io as bsio

from src.utils.logger import get_pipeline_logger

logger = get_pipeline_logger("structure_comparison")

class ComparisonResult:
    """Class to store and parse structure comparison results."""
    
    def __init__(self, tm_score: float, reference_pdb: str):
        self.tm_score = tm_score
        self.reference_pdb = reference_pdb
        
    def to_dict(self) -> Dict:
        """Convert result to dictionary."""
        return {
            "tm_score": self.tm_score,
            "reference_pdb": self.reference_pdb
        }
        
    @classmethod
    def from_output(cls, output_file: Path, reference_pdb: str) -> Optional['ComparisonResult']:
        """Parse Foldseek output file to get TM-score."""
        try:
            with open(output_file, 'r') as f:
                for line in f:
                    if not line.startswith('#'):
                        fields = line.strip().split('\t')
                        if len(fields) >= 3:  # Changed to 3 for query,target,alntmscore format
                            tm_score = float(fields[2])  # TM-score is in the third column
                            return cls(tm_score, reference_pdb)
            return None
        except Exception as e:
            logger.error(f"Error parsing Foldseek output: {e}")
            return None

class TMScoreCalculator:
    """Calculator for TM-scores using Foldseek."""
    
    def __init__(self):
        """Initialize calculator."""
        pass
    
    def _get_foldseek_path(self) -> Optional[Path]:
        """Get path to appropriate Foldseek binary for current platform."""
        # Get base directory (where bin/ is located)
        base_dir = Path(__file__).resolve().parents[2]
        bin_dir = base_dir / "bin"
        
        # Determine platform and architecture
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        # Map of platform to binary name
        binary_map = {
            ("linux", "x86_64"): "foldseek_linux_x64",
            ("linux", "aarch64"): "foldseek_linux_arm64",
            ("darwin", "x86_64"): "foldseek_mac_x64",
            ("darwin", "arm64"): "foldseek_mac_arm64"
        }
        
        binary_name = binary_map.get((system, machine))
        if not binary_name:
            logger.error(f"Unsupported platform: {system} {machine}")
            return None
            
        binary_path = bin_dir / binary_name
        if not binary_path.exists():
            logger.error(f"Foldseek binary not found at {binary_path}")
            return None
            
        # Make binary executable
        binary_path.chmod(0o755)
        return binary_path
    
    def _convert_cif_to_pdb(self, cif_file: Path, output_dir: Path) -> Optional[Path]:
        """Convert CIF file to PDB format with special handling for non-standard residues."""
        try:
            # Read CIF file
            struct = bsio.load_structure(str(cif_file), model=1)
            
            # Create output PDB file path
            pdb_file = output_dir / f"{cif_file.stem}.pdb"
            
            # Process residues before saving
            for chain in struct.get_chains():
                for residue in chain.get_residues():
                    # Handle residue names longer than 3 characters
                    if len(residue.get_name()) > 3:
                        # Map common non-standard residues to their 3-letter codes
                        residue_map = {
                            'HIST': 'HIS',
                            'HISE': 'HIS',
                            'HISD': 'HIS',
                            'HISH': 'HIS',
                            'ARGS': 'ARG',
                            'ARGN': 'ARG',
                            'LYSN': 'LYS',
                            'LYSH': 'LYS',
                            'ASPT': 'ASP',
                            'GLUT': 'GLU',
                            'GLUH': 'GLU',
                            'TYRS': 'TYR',
                            'TYRH': 'TYR',
                            'CYSH': 'CYS',
                            'CYSM': 'CYS',
                            'CYSS': 'CYS',
                            'THRO': 'THR',
                            'THRN': 'THR',
                            'SERS': 'SER',
                            'SERT': 'SER',
                            'PROT': 'PRO',
                            'PRON': 'PRO',
                            'METH': 'MET',
                            'METS': 'MET',
                            'PHEH': 'PHE',
                            'PHEN': 'PHE',
                            'TRPH': 'TRP',
                            'TRPN': 'TRP',
                            'ALAH': 'ALA',
                            'ALAN': 'ALA',
                            'VALH': 'VAL',
                            'VALN': 'VAL',
                            'ILEH': 'ILE',
                            'ILEN': 'ILE',
                            'LEUH': 'LEU',
                            'LEUN': 'LEU',
                            'GLNH': 'GLN',
                            'GLNT': 'GLN',
                            'ASNH': 'ASN',
                            'ASNT': 'ASN',
                            'TPO': 'THR',  # Phosphothreonine
                            'SEP': 'SER',  # Phosphoserine
                            'PTR': 'TYR',  # Phosphotyrosine
                            'MSE': 'MET',  # Selenomethionine
                        }
                        
                        orig_name = residue.get_name()
                        if orig_name in residue_map:
                            residue.name = residue_map[orig_name]
                        else:
                            # For unknown residues, truncate to first 3 characters
                            residue.name = orig_name[:3]
                            logger.warning(f"Truncated residue name {orig_name} to {residue.name}")
            
            # Save as PDB with modified residues
            bsio.save_structure(pdb_file, struct)
            
            # Verify the saved file
            if not pdb_file.exists() or pdb_file.stat().st_size == 0:
                logger.error(f"Failed to save PDB file {pdb_file}")
                return None
                
            return pdb_file
            
        except Exception as e:
            logger.error(f"Failed to convert {cif_file} to PDB: {str(e)}")
            return None
    
    def calculate_tm_score(self, predicted_pdb: Path, reference_pdb: Path) -> Optional[float]:
        """Calculate TM-score between predicted and reference structures using Foldseek."""
        try:
            # Create temporary directories
            tmp_dir = Path("tmp_foldseek")
            tmp_dir.mkdir(parents=True, exist_ok=True)
            
            # Run Foldseek alignment
            cmd = [
                str(self._get_foldseek_path()),
                "easy-search",
                str(predicted_pdb),
                str(reference_pdb),
                str(tmp_dir / "aln"),
                str(tmp_dir),
                "--format-output", "query,target,alntmscore",  # Changed format to get TM-score directly
                "--alignment-type", "1",  # Use TMalign mode
                "--max-seqs", "1000000"  # Set to 1M for complete coverage in research
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Foldseek failed: {result.stderr}")
                return None
                
            # Parse results
            result = ComparisonResult.from_output(tmp_dir / "aln", str(reference_pdb))
            if result:
                return result.tm_score
                
            logger.error("Could not parse Foldseek output")
            return None
            
        except Exception as e:
            logger.error(f"Error running Foldseek: {e}")
            return None
        finally:
            # Cleanup
            if tmp_dir.exists():
                shutil.rmtree(tmp_dir)

    def compare_structures(self, predicted_structures: Dict[str, Path], ground_truth_dir: Path, output_dir: Optional[Path] = None) -> Dict[str, Dict]:
        """
        Compare predicted structures with ground truth structures using Foldseek.
        
        Args:
            predicted_structures: Dictionary mapping sequence IDs to predicted structure paths
            ground_truth_dir: Path to directory containing ground truth structures
            output_dir: Optional output directory for saving detailed results
            
        Returns:
            Dictionary containing comparison results
        """
        results = {}
        
        logger.info(f"Starting structure comparisons for {len(predicted_structures)} structures")
        logger.info(f"Using ground truth directory: {ground_truth_dir}")
        
        if not ground_truth_dir.exists():
            logger.error(f"Ground truth directory not found: {ground_truth_dir}")
            return results
        
        # Create temporary directory for Foldseek
        tmp_dir = Path("tmp_foldseek")
        tmp_dir.mkdir(exist_ok=True)
        
        # Create output directory for detailed results if output_dir is provided
        detailed_results_dir = None
        if output_dir:
            detailed_results_dir = output_dir / "detailed_tm_scores"
            detailed_results_dir.mkdir(parents=True, exist_ok=True)
        elif hasattr(self, 'output_base_dir'):
            detailed_results_dir = self.output_base_dir / "detailed_tm_scores"
            detailed_results_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            for seq_id, pred_structure in predicted_structures.items():
                results[seq_id] = {}
                
                # Run Foldseek comparison
                results_file = tmp_dir / f"results_{seq_id}.m8"
                
                # Get the correct Foldseek binary path
                foldseek_path = self._get_foldseek_path()
                if not foldseek_path:
                    logger.error("Could not find appropriate Foldseek binary")
                    results[seq_id] = {
                        "max_score": 0.0,
                        "avg_score": 0.0,
                        "num_comparisons": 0,
                        "error": "Foldseek binary not found"
                    }
                    continue
                
                cmd = [
                    str(foldseek_path), "easy-search",
                    str(pred_structure),  # Input structure
                    str(ground_truth_dir),  # Ground truth directory
                    str(results_file),  # Output file
                    str(tmp_dir),  # Temporary directory
                    "--format-output", "query,target,alntmscore",  # Output format
                    "--max-seqs", "1000000"  # Set to 1M for complete coverage in research
                ]
                
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        # Parse results
                        scores = []
                        target_scores = []  # Store target-score pairs
                        
                        with open(results_file) as f:
                            for line in f:
                                parts = line.strip().split("\t")
                                if len(parts) >= 3:
                                    query, target, score = parts[0], parts[1], float(parts[2])
                                    scores.append(score)
                                    target_scores.append((target, score))
                                
                        if scores:
                            results[seq_id] = {
                                "max_score": max(scores),
                                "avg_score": sum(scores) / len(scores),
                                "num_comparisons": len(scores)
                            }
                            
                            # Save detailed results file if output directory is available
                            if detailed_results_dir:
                                detailed_file = detailed_results_dir / f"{seq_id}_tm_scores.tsv"
                                with open(detailed_file, 'w') as f:
                                    f.write("query\ttarget\ttm_score\n")
                                    for target, score in sorted(target_scores, key=lambda x: x[1], reverse=True):
                                        f.write(f"{seq_id}\t{target}\t{score:.4f}\n")
                                
                                results[seq_id]["detailed_results_file"] = str(detailed_file)
                                logger.info(f"Saved detailed TM-scores for {seq_id} to {detailed_file}")
                        else:
                            logger.warning(f"No scores found for {seq_id}")
                            results[seq_id] = {
                                "max_score": 0.0,
                                "avg_score": 0.0,
                                "num_comparisons": 0
                            }
                            
                    else:
                        logger.error(f"Foldseek error: {result.stderr}")
                        results[seq_id] = {
                            "max_score": 0.0,
                            "avg_score": 0.0,
                            "num_comparisons": 0,
                            "error": result.stderr
                        }
                        
                except Exception as e:
                    logger.error(f"Error comparing {seq_id}: {str(e)}")
                    results[seq_id] = {
                        "max_score": 0.0,
                        "avg_score": 0.0,
                        "num_comparisons": 0,
                        "error": str(e)
                    }
                    
        finally:
            # Clean up temporary files
            if tmp_dir.exists():
                shutil.rmtree(tmp_dir)
                
        return results

    def compare_with_ground_truth_set(
        self,
        predicted_pdb: Path,
        ground_truth_dir: Path,
        output_dir: Path
    ) -> Dict:
        """
        Compare a predicted structure with a ground truth set.
        
        Args:
            predicted_pdb: Path to predicted structure
            ground_truth_dir: Path to ground truth directory
            output_dir: Directory to save results (not used but kept for compatibility)
            
        Returns:
            Dictionary containing comparison results
        """
        # Compare structures
        result = self.compare_structures(
            {predicted_pdb.stem: predicted_pdb},
            ground_truth_dir
        )
        
        if predicted_pdb.stem in result:
            return {
                "best_match": result[predicted_pdb.stem]
            }
        else:
            return {
                "best_match": None
            }
            
    def batch_calculate(
        self,
        predicted_structures: Dict[str, Path],
        ground_truth_dir: Path,
        output_dir: Path
    ) -> Dict:
        """
        Calculate TM-scores for multiple structures.
        
        Args:
            predicted_structures: Dictionary mapping sequence IDs to structure paths
            ground_truth_dir: Path to ground truth directory
            output_dir: Directory to save results
            
        Returns:
            Dictionary containing all comparison results
        """
        results = {}
        best_overall_result = None
        
        for seq_id, structure_path in predicted_structures.items():
            try:
                # Compare with ground truth set
                comparison_results = self.compare_with_ground_truth_set(
                    structure_path,
                    ground_truth_dir,
                    output_dir
                )
                
                results[seq_id] = comparison_results
                
                # Update best overall result
                if comparison_results["best_match"]:
                    if (best_overall_result is None or 
                        comparison_results["best_match"]["max_score"] > best_overall_result["max_score"]):
                        best_overall_result = comparison_results["best_match"]
                        
            except Exception as e:
                logger.error(f"Error processing {seq_id}: {str(e)}")
                results[seq_id] = {
                    "best_match": None,
                    "error": str(e)
                }
                
        # Add best overall result
        results["best_overall"] = best_overall_result
        
        return results 
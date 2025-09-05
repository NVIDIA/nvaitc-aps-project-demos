# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
pLDDT extraction module for ESMfold predicted structures.
Extracts confidence scores from PDB files and calculates sequence-level statistics.
"""

from pathlib import Path
from typing import List, Dict, Optional, Tuple
import statistics

from src.utils.logger import get_pipeline_logger

logger = get_pipeline_logger("plddt_extractor")

class PLDDTExtractor:
    """Extract and analyze pLDDT confidence scores from ESMfold PDB files."""
    
    def __init__(self):
        """Initialize the pLDDT extractor."""
        pass
    
    def extract_plddt_scores(self, pdb_file: Path) -> List[float]:
        """
        Extract pLDDT scores from an ESMfold PDB file.
        
        In ESMfold PDB files, pLDDT scores are stored in the B-factor column 
        (columns 61-66) of ATOM records.
        
        Args:
            pdb_file: Path to the PDB file
            
        Returns:
            List of pLDDT scores for each residue
        """
        plddt_scores = []
        
        try:
            with open(pdb_file, 'r') as f:
                for line in f:
                    if line.startswith('ATOM'):
                        # Extract B-factor column (columns 61-66, 1-indexed)
                        # In Python 0-indexed: columns 60-66
                        b_factor_str = line[60:66].strip()
                        if b_factor_str:
                            plddt_score = float(b_factor_str)
                            plddt_scores.append(plddt_score)
        except Exception as e:
            logger.error(f"Error extracting pLDDT scores from {pdb_file}: {e}")
            return []
        
        logger.debug(f"Extracted {len(plddt_scores)} pLDDT scores from {pdb_file.name}")
        return plddt_scores
    
    def calculate_sequence_statistics(self, plddt_scores: List[float]) -> Dict:
        """
        Calculate sequence-level pLDDT statistics.
        
        Args:
            plddt_scores: List of per-residue pLDDT scores
            
        Returns:
            Dictionary containing sequence-level statistics
        """
        if not plddt_scores:
            return {
                "avg_plddt": 0.0,
                "min_plddt": 0.0,
                "max_plddt": 0.0,
                "median_plddt": 0.0,
                "std_dev_plddt": 0.0,
                "variance_plddt": 0.0,
                "sequence_length": 0,
                "valid_scores": 0
            }
        
        try:
            stats = {
                "avg_plddt": statistics.mean(plddt_scores),
                "min_plddt": min(plddt_scores),
                "max_plddt": max(plddt_scores),
                "median_plddt": statistics.median(plddt_scores),
                "sequence_length": len(plddt_scores),
                "valid_scores": len(plddt_scores)
            }
            
            # Calculate standard deviation and variance
            if len(plddt_scores) > 1:
                stats["std_dev_plddt"] = statistics.stdev(plddt_scores)
                stats["variance_plddt"] = statistics.variance(plddt_scores)
            else:
                stats["std_dev_plddt"] = 0.0
                stats["variance_plddt"] = 0.0
                
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating pLDDT statistics: {e}")
            return {
                "avg_plddt": 0.0,
                "min_plddt": 0.0,
                "max_plddt": 0.0,
                "median_plddt": 0.0,
                "std_dev_plddt": 0.0,
                "variance_plddt": 0.0,
                "sequence_length": len(plddt_scores),
                "valid_scores": 0
            }
    
    def calculate_threshold_counts(self, plddt_scores: List[float]) -> Dict:
        """
        Calculate how many residues meet each pLDDT threshold.
        
        Args:
            plddt_scores: List of per-residue pLDDT scores
            
        Returns:
            Dictionary with threshold counts and percentages
        """
        if not plddt_scores:
            return {}
        
        thresholds = [i * 10 for i in range(11)]  # [0, 10, 20, ..., 90, 100]
        threshold_counts = {}
        total_residues = len(plddt_scores)
        
        for threshold in thresholds:
            count = sum(1 for score in plddt_scores if score >= threshold)
            percentage = (count / total_residues) * 100 if total_residues > 0 else 0
            
            threshold_counts[f"{threshold}"] = {
                "count": count,
                "percentage": float(percentage),
                "threshold": threshold
            }
        
        return threshold_counts
    
    def extract_and_analyze(self, pdb_file: Path) -> Optional[Dict]:
        """
        Extract pLDDT scores and calculate all statistics for a single PDB file.
        
        Args:
            pdb_file: Path to the PDB file
            
        Returns:
            Dictionary containing all pLDDT analysis results
        """
        if not pdb_file.exists():
            logger.error(f"PDB file not found: {pdb_file}")
            return None
        
        # Extract raw pLDDT scores
        plddt_scores = self.extract_plddt_scores(pdb_file)
        
        if not plddt_scores:
            logger.warning(f"No pLDDT scores found in {pdb_file}")
            return None
        
        # Calculate statistics
        stats = self.calculate_sequence_statistics(plddt_scores)
        threshold_counts = self.calculate_threshold_counts(plddt_scores)
        
        result = {
            "pdb_file": str(pdb_file),
            "sequence_id": pdb_file.stem,
            "statistics": stats,
            "threshold_counts": threshold_counts,
            "raw_scores": plddt_scores  # Include for potential future use
        }
        
        logger.info(f"pLDDT analysis complete for {pdb_file.stem}: avg={stats['avg_plddt']:.2f}")
        return result
    
    def batch_extract(self, predicted_structures: Dict[str, Path]) -> Dict[str, Dict]:
        """
        Extract and analyze pLDDT scores for multiple structures.
        
        Args:
            predicted_structures: Dictionary mapping sequence IDs to PDB file paths
            
        Returns:
            Dictionary containing pLDDT analysis for all structures
        """
        results = {}
        
        logger.info(f"Starting pLDDT analysis for {len(predicted_structures)} structures")
        
        for seq_id, pdb_path in predicted_structures.items():
            try:
                analysis = self.extract_and_analyze(pdb_path)
                if analysis:
                    results[seq_id] = analysis
                else:
                    logger.warning(f"Failed to analyze pLDDT for {seq_id}")
                    results[seq_id] = {
                        "pdb_file": str(pdb_path),
                        "sequence_id": seq_id,
                        "statistics": {
                            "avg_plddt": 0.0,
                            "min_plddt": 0.0,
                            "max_plddt": 0.0,
                            "median_plddt": 0.0,
                            "std_dev_plddt": 0.0,
                            "variance_plddt": 0.0,
                            "sequence_length": 0,
                            "valid_scores": 0
                        },
                        "threshold_counts": {},
                        "error": "Failed to extract pLDDT scores"
                    }
            except Exception as e:
                logger.error(f"Error processing pLDDT for {seq_id}: {e}")
                results[seq_id] = {
                    "pdb_file": str(pdb_path),
                    "sequence_id": seq_id,
                    "error": str(e)
                }
        
        logger.info(f"pLDDT analysis completed for {len(results)} structures")
        return results 
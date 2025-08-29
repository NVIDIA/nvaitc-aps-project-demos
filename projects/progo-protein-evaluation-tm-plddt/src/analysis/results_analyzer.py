# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Results analysis module for ProteinGO pipeline.
Analyzes structure comparison results and generates statistics.
"""

import json
import csv
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
from collections import defaultdict
from Bio import SeqIO

from src.utils.logger import get_pipeline_logger

logger = get_pipeline_logger("results_analyzer")

class ResultsAnalyzer:
    """Analyzer for structure comparison results."""
    
    def __init__(self, ground_truth_set: Optional[str] = None):
        """Initialize analyzer.
        
        Args:
            ground_truth_set: Name of ground truth set to use for reference sequences
        """
        self.reference_sequences = self._load_reference_sequences(ground_truth_set)
        
    def _load_reference_sequences(self, ground_truth_set: Optional[str] = None) -> Dict[str, str]:
        """Load reference sequences from JSON file.
        
        Args:
            ground_truth_set: Name of ground truth set to load reference sequences from
            
        Returns:
            Dictionary mapping reference IDs to sequences
        """
        # Try ground truth specific reference file first
        if ground_truth_set:
            gt_reference_file = Path(__file__).parent.parent.parent / "data" / "ground_truth" / ground_truth_set / "reference_seqs.json"
            if gt_reference_file.exists():
                reference_file = gt_reference_file
                logger.info(f"Using ground truth specific reference sequences from {ground_truth_set}")
            else:
                # Fall back to global reference file
                reference_file = Path(__file__).parent.parent.parent / "data" / "reference_seqs.json"
                if reference_file.exists():
                    logger.info(f"No reference sequences found for {ground_truth_set}, using global reference sequences")
        else:
            # Use global reference file if no ground truth set specified
            reference_file = Path(__file__).parent.parent.parent / "data" / "reference_seqs.json"
            
        try:
            with open(reference_file, 'r') as f:
                data = json.load(f)
                # Handle both formats: array of objects or simple dictionary
                if isinstance(data, list):
                    # Array format: [{"sequence": "...", "id": "...", "description": "..."}]
                    return {item["id"]: item["sequence"] for item in data}
                else:
                    # Dictionary format: {"id": "sequence"}
                    return data
        except Exception as e:
            logger.warning(f"Could not load reference sequences: {e}")
            return {}
        
    def analyze_results(self, results: Dict, fasta_file: Optional[Path] = None, skipped_duplicates: Optional[Dict[str, str]] = None, plddt_results: Optional[Dict[str, Dict]] = None) -> Dict:
        """
        Analyze structure comparison results.
        
        Args:
            results: Dictionary containing comparison results
            fasta_file: Optional path to original FASTA file for sequence matching
            skipped_duplicates: Optional dictionary of sequences skipped due to being duplicates
            plddt_results: Optional dictionary containing pLDDT analysis results
            
        Returns:
            Dictionary containing analysis results
        """
        analysis = {
            "summary": {
                "total_structures": 0,
                "successful_comparisons": 0,
                "failed_comparisons": 0,
                "best_overall_score": 0.0,
                "average_score": 0.0,
                "sequences_with_tm_scores": 0,
                "sequences_without_tm_scores": 0,
                "exact_reference_matches": 0,
                "skipped_duplicates": 0,
                "failed_sequences": []
            },
            "details": {},
            "reference_matches": [],
            "skipped_duplicate_sequences": [],
            "foldseek_parameters": {
                "max_seqs": 1000000,
                "e_value_threshold": "10.0 (default)",
                "note": "max_seqs set to 1M for complete coverage. PDB files with multiple chains are indexed separately by Foldseek (e.g., 9mhg.pdb with chains A,B,C,D,E creates 5 searchable entries)."
            }
        }
        
        # Handle skipped duplicates
        if skipped_duplicates:
            analysis["summary"]["skipped_duplicates"] = len(skipped_duplicates)
            for seq_id, ref_id in skipped_duplicates.items():
                analysis["skipped_duplicate_sequences"].append({
                    "query_id": seq_id,
                    "reference_id": ref_id,
                    "reason": "Exact duplicate of reference sequence - skipped prediction"
                })
                # Also count these as exact reference matches
                analysis["summary"]["exact_reference_matches"] += 1
        
        # Load original sequences if FASTA file provided
        original_sequences = {}
        if fasta_file and fasta_file.exists():
            try:
                for record in SeqIO.parse(str(fasta_file), "fasta"):
                    original_sequences[record.id] = str(record.seq)
            except Exception as e:
                logger.warning(f"Could not load original FASTA file: {e}")
        
        # Count total and analyze each result
        total_score = 0.0
        sequences_with_scores = []
        top_tm_scores = []  # Collect top TM-scores for threshold analysis
        avg_plddt_scores = []  # Collect average pLDDT scores for threshold analysis
        
        for seq_id, result in results.items():
            if seq_id == "best_overall":
                continue
                
            analysis["summary"]["total_structures"] += 1
            
            if result["best_match"] and "error" not in result["best_match"]:
                analysis["summary"]["successful_comparisons"] += 1
                tm_score = result["best_match"]["max_score"]
                total_score += tm_score
                sequences_with_scores.append(seq_id)
                top_tm_scores.append(tm_score)  # Add to list for threshold analysis
                
                # Add pLDDT information if available
                plddt_info = {}
                if plddt_results and seq_id in plddt_results and "statistics" in plddt_results[seq_id]:
                    plddt_stats = plddt_results[seq_id]["statistics"]
                    plddt_info = {
                        "avg_plddt": plddt_stats.get("avg_plddt", 0.0),
                        "min_plddt": plddt_stats.get("min_plddt", 0.0),
                        "max_plddt": plddt_stats.get("max_plddt", 0.0),
                        "median_plddt": plddt_stats.get("median_plddt", 0.0),
                        "std_dev_plddt": plddt_stats.get("std_dev_plddt", 0.0),
                        "sequence_length": plddt_stats.get("sequence_length", 0),
                        "has_plddt": True
                    }
                    avg_plddt_scores.append(plddt_stats.get("avg_plddt", 0.0))
                else:
                    plddt_info = {
                        "avg_plddt": 0.0,
                        "min_plddt": 0.0,
                        "max_plddt": 0.0,
                        "median_plddt": 0.0,
                        "std_dev_plddt": 0.0,
                        "sequence_length": 0,
                        "has_plddt": False
                    }
                
                analysis["details"][seq_id] = {
                    "max_score": tm_score,
                    "avg_score": result["best_match"]["avg_score"],
                    "num_comparisons": result["best_match"]["num_comparisons"],
                    "has_tm_score": True,
                    **plddt_info  # Add pLDDT information
                }
            else:
                analysis["summary"]["failed_comparisons"] += 1
                analysis["summary"]["failed_sequences"].append(seq_id)
                
                # Add pLDDT information for failed sequences if available
                plddt_info = {}
                if plddt_results and seq_id in plddt_results and "statistics" in plddt_results[seq_id]:
                    plddt_stats = plddt_results[seq_id]["statistics"]
                    plddt_info = {
                        "avg_plddt": plddt_stats.get("avg_plddt", 0.0),
                        "min_plddt": plddt_stats.get("min_plddt", 0.0),
                        "max_plddt": plddt_stats.get("max_plddt", 0.0),
                        "median_plddt": plddt_stats.get("median_plddt", 0.0),
                        "std_dev_plddt": plddt_stats.get("std_dev_plddt", 0.0),
                        "sequence_length": plddt_stats.get("sequence_length", 0),
                        "has_plddt": True
                    }
                    avg_plddt_scores.append(plddt_stats.get("avg_plddt", 0.0))
                else:
                    plddt_info = {
                        "avg_plddt": 0.0,
                        "min_plddt": 0.0,
                        "max_plddt": 0.0,
                        "median_plddt": 0.0,
                        "std_dev_plddt": 0.0,
                        "sequence_length": 0,
                        "has_plddt": False
                    }
                
                analysis["details"][seq_id] = {
                    "error": result.get("error", "Unknown error"),
                    "has_tm_score": False,
                    **plddt_info  # Add pLDDT information
                }
        
        # Update counts
        analysis["summary"]["sequences_with_tm_scores"] = len(sequences_with_scores)
        analysis["summary"]["sequences_without_tm_scores"] = analysis["summary"]["failed_comparisons"]
        
        # Calculate threshold counts for top TM-scores (0.0 to 1.0 in 0.1 intervals)
        thresholds = [i/10 for i in range(11)]  # [0.0, 0.1, 0.2, ..., 0.9, 1.0]
        analysis["threshold_counts"] = {}
        for threshold in thresholds:
            count = sum(1 for score in top_tm_scores if score >= threshold)
            percentage = (count / len(top_tm_scores)) * 100 if top_tm_scores else 0
            analysis["threshold_counts"][f"{threshold:.1f}"] = {
                "count": count,
                "percentage": float(percentage),
                "threshold": threshold
            }
        
        # Calculate statistical measures for top TM-scores
        if top_tm_scores:
            analysis["tm_score_statistics"] = self._calculate_statistics(top_tm_scores)
        else:
            analysis["tm_score_statistics"] = {
                "count": 0,
                "mean": 0.0,
                "median": 0.0,
                "std_dev": 0.0,
                "variance": 0.0,
                "min": 0.0,
                "max": 0.0
            }
        
        # pLDDT Analysis - separate from TM-score analysis
        if avg_plddt_scores:
            # Calculate threshold counts for pLDDT scores (0 to 100 in 10-point intervals)
            plddt_thresholds = [i * 10 for i in range(11)]  # [0, 10, 20, ..., 90, 100]
            analysis["plddt_threshold_counts"] = {}
            for threshold in plddt_thresholds:
                count = sum(1 for score in avg_plddt_scores if score >= threshold)
                percentage = (count / len(avg_plddt_scores)) * 100 if avg_plddt_scores else 0
                analysis["plddt_threshold_counts"][f"{threshold}"] = {
                    "count": count,
                    "percentage": float(percentage),
                    "threshold": threshold
                }
            
            # Calculate statistical measures for pLDDT scores
            analysis["plddt_statistics"] = self._calculate_statistics(avg_plddt_scores)
        else:
            analysis["plddt_threshold_counts"] = {}
            analysis["plddt_statistics"] = {
                "count": 0,
                "mean": 0.0,
                "median": 0.0,
                "std_dev": 0.0,
                "variance": 0.0,
                "min": 0.0,
                "max": 0.0
            }
        
        # Check for exact matches with reference sequences
        if original_sequences and self.reference_sequences:
            for seq_id, sequence in original_sequences.items():
                # Skip if already identified as duplicate
                if skipped_duplicates and seq_id in skipped_duplicates:
                    continue
                for ref_id, ref_seq in self.reference_sequences.items():
                    if sequence == ref_seq:
                        analysis["summary"]["exact_reference_matches"] += 1
                        analysis["reference_matches"].append({
                            "query_id": seq_id,
                            "reference_id": ref_id,
                            "sequence_length": len(sequence)
                        })
                        break  # Only count once per sequence
                
        # Calculate averages and best score
        if analysis["summary"]["successful_comparisons"] > 0:
            analysis["summary"]["average_score"] = total_score / analysis["summary"]["successful_comparisons"]
            
        if results.get("best_overall"):
            analysis["summary"]["best_overall_score"] = results["best_overall"]["max_score"]
            
        return analysis
        
    def save_analysis(self, analysis: Dict, output_dir: Path) -> None:
        """
        Save analysis results to file.
        
        Args:
            analysis: Dictionary containing analysis results
            output_dir: Directory to save results
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save JSON results
        json_file = output_dir / "analysis_results.json"
        with open(json_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        logger.info(f"Saved JSON analysis to {json_file}")
        
        # Save CSV results
        csv_file = output_dir / "analysis_results.csv"
        self._save_csv_analysis(analysis, csv_file)
        logger.info(f"Saved CSV analysis to {csv_file}")
        
        # Save scientific analysis
        sci_file = output_dir / "scientific_analysis.txt"
        self._save_scientific_analysis(analysis, sci_file)
        logger.info(f"Saved scientific analysis to {sci_file}")
        
    def _save_csv_analysis(self, analysis: Dict, csv_file: Path) -> None:
        """Save analysis results to CSV file."""
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write summary section
            writer.writerow(["Summary Statistics"])
            writer.writerow(["Metric", "Value"])
            for key, value in analysis["summary"].items():
                if key != "failed_sequences":  # Skip list values
                    writer.writerow([key, value])
            
            # Write TM-score statistics
            if "tm_score_statistics" in analysis:
                writer.writerow([])
                writer.writerow(["TM-Score Statistics"])
                writer.writerow(["Metric", "Value"])
                stats = analysis["tm_score_statistics"]
                writer.writerow(["Highest TM-score", f"{stats['max']:.4f}"])
                writer.writerow(["Lowest TM-score", f"{stats['min']:.4f}"])
                writer.writerow(["Median TM-score", f"{stats['median']:.4f}"])
                writer.writerow(["Average TM-score", f"{stats['mean']:.4f}"])
                writer.writerow(["Variance", f"{stats['variance']:.4f}"])
                writer.writerow(["Standard deviation", f"{stats['std_dev']:.4f}"])
                writer.writerow(["Count", stats['count']])
            
            # Write pLDDT statistics
            if "plddt_statistics" in analysis:
                writer.writerow([])
                writer.writerow(["pLDDT Statistics"])
                writer.writerow(["Metric", "Value"])
                stats = analysis["plddt_statistics"]
                writer.writerow(["Highest pLDDT", f"{stats['max']:.2f}"])
                writer.writerow(["Lowest pLDDT", f"{stats['min']:.2f}"])
                writer.writerow(["Median pLDDT", f"{stats['median']:.2f}"])
                writer.writerow(["Average pLDDT", f"{stats['mean']:.2f}"])
                writer.writerow(["Variance", f"{stats['variance']:.2f}"])
                writer.writerow(["Standard deviation", f"{stats['std_dev']:.2f}"])
                writer.writerow(["Count", stats['count']])
            
            # Write Foldseek parameters
            if "foldseek_parameters" in analysis:
                writer.writerow([])
                writer.writerow(["Foldseek Parameters"])
                writer.writerow(["Parameter", "Value"])
                params = analysis["foldseek_parameters"]
                writer.writerow(["max_seqs", f"{params['max_seqs']:,}"])
                writer.writerow(["E-value threshold", params["e_value_threshold"]])
                writer.writerow(["Chain indexing", "Each chain in multi-chain PDB files is indexed separately"])
                writer.writerow(["Example", "9mhg.pdb with chains A,B,C,D,E creates 5 searchable entries"])
            
            # Write TM-score threshold counts
            if "threshold_counts" in analysis:
                writer.writerow([])
                writer.writerow(["TM-Score Threshold Analysis"])
                writer.writerow(["Threshold", "Count", "Percentage"])
                for threshold_str in sorted(analysis["threshold_counts"].keys(), key=float):
                    data = analysis["threshold_counts"][threshold_str]
                    writer.writerow([
                        f"≥ {threshold_str}",
                        data["count"],
                        f"{data['percentage']:.1f}%"
                    ])
            
            # Write pLDDT threshold counts
            if "plddt_threshold_counts" in analysis:
                writer.writerow([])
                writer.writerow(["pLDDT Threshold Analysis"])
                writer.writerow(["Threshold", "Count", "Percentage"])
                for threshold_str in sorted(analysis["plddt_threshold_counts"].keys(), key=int):
                    data = analysis["plddt_threshold_counts"][threshold_str]
                    writer.writerow([
                        f"≥ {threshold_str}",
                        data["count"],
                        f"{data['percentage']:.1f}%"
                    ])
            
            # Write failed sequences
            if analysis["summary"]["failed_sequences"]:
                writer.writerow([])
                writer.writerow(["Failed Sequences"])
                for seq_id in analysis["summary"]["failed_sequences"]:
                    writer.writerow([seq_id])
            
            # Write skipped duplicate sequences
            if analysis["skipped_duplicate_sequences"]:
                writer.writerow([])
                writer.writerow(["Skipped Duplicate Sequences"])
                writer.writerow(["Query ID", "Reference ID", "Reason"])
                for dup in analysis["skipped_duplicate_sequences"]:
                    writer.writerow([dup["query_id"], dup["reference_id"], dup["reason"]])
            
            # Write reference matches
            if analysis["reference_matches"]:
                writer.writerow([])
                writer.writerow(["Reference Matches"])
                writer.writerow(["Query ID", "Reference ID", "Sequence Length"])
                for match in analysis["reference_matches"]:
                    writer.writerow([match["query_id"], match["reference_id"], match["sequence_length"]])
            
            # Write details section
            writer.writerow([])
            writer.writerow(["Sequence Details"])
            writer.writerow(["Sequence ID", "Max TM-Score", "Avg TM-Score", "Num Comparisons", "Has TM-Score", "Avg pLDDT", "Min pLDDT", "Max pLDDT", "Has pLDDT", "Error"])
            
            for seq_id, details in analysis["details"].items():
                writer.writerow([
                    seq_id,
                    details.get("max_score", ""),
                    details.get("avg_score", ""),
                    details.get("num_comparisons", ""),
                    details.get("has_tm_score", False),
                    details.get("avg_plddt", ""),
                    details.get("min_plddt", ""),
                    details.get("max_plddt", ""),
                    details.get("has_plddt", False),
                    details.get("error", "")
                ])
                
    def _save_scientific_analysis(self, analysis: Dict, sci_file: Path) -> None:
        """Generate and save scientific analysis."""
        interpretation = []
        
        # Header
        interpretation.append("Scientific Analysis of Protein Structure Predictions")
        interpretation.append("=" * 50)
        interpretation.append("")
        
        # Summary statistics
        summary = analysis["summary"]
        interpretation.append(f"Total sequences analyzed: {summary['total_structures']}")
        interpretation.append(f"Sequences with TM-scores: {summary['sequences_with_tm_scores']}")
        interpretation.append(f"Sequences without TM-scores (failed): {summary['sequences_without_tm_scores']}")
        interpretation.append(f"Skipped duplicate sequences: {summary['skipped_duplicates']}")
        interpretation.append(f"Exact matches to reference sequences: {summary['exact_reference_matches']}")
        interpretation.append("")
        
        # Foldseek parameters
        if "foldseek_parameters" in analysis:
            interpretation.append("Foldseek Search Parameters:")
            params = analysis["foldseek_parameters"]
            interpretation.append(f"- max_seqs: {params['max_seqs']:,}")
            interpretation.append(f"- E-value threshold: {params['e_value_threshold']}")
            interpretation.append("")
            interpretation.append("Note: PDB files containing multiple chains are indexed separately by Foldseek.")
            interpretation.append("For example, a file with 5 chains creates 5 searchable entries.")
            interpretation.append("")
        
        # Score analysis
        if summary['successful_comparisons'] > 0:
            interpretation.append("Structure Quality Metrics:")
            interpretation.append(f"- Best overall TM-score: {summary['best_overall_score']:.3f}")
            interpretation.append(f"- Average TM-score: {summary['average_score']:.3f}")
            interpretation.append("")
            
            # Add detailed TM-score statistics
            if "tm_score_statistics" in analysis:
                stats = analysis["tm_score_statistics"]
                interpretation.append("Statistical Analysis of Top TM-Scores:")
                interpretation.append(f"- Highest TM-score: {stats['max']:.4f}")
                interpretation.append(f"- Lowest TM-score: {stats['min']:.4f}")
                interpretation.append(f"- Median TM-score: {stats['median']:.4f}")
                interpretation.append(f"- Average TM-score: {stats['mean']:.4f}")
                interpretation.append(f"- Variance: {stats['variance']:.4f}")
                interpretation.append(f"- Standard deviation: {stats['std_dev']:.4f}")
                interpretation.append("")
            
            # Quality assessment for TM-scores
            avg_score = summary['average_score']
            if avg_score >= 0.9:
                quality = "excellent - structures are nearly identical to ground truth"
            elif avg_score >= 0.8:
                quality = "very good - structures show high similarity to ground truth"
            elif avg_score >= 0.7:
                quality = "good - structures show moderate to high similarity"
            elif avg_score >= 0.6:
                quality = "moderate - structures show some similarity"
            else:
                quality = "poor - structures show limited similarity to ground truth"
                
            interpretation.append(f"Overall TM-score quality assessment: {quality}")
            
            # TM-score threshold analysis
            if "threshold_counts" in analysis:
                interpretation.append("")
                interpretation.append("TM-Score Distribution (sequences meeting or exceeding threshold):")
                for threshold_str in sorted(analysis["threshold_counts"].keys(), key=float):
                    data = analysis["threshold_counts"][threshold_str]
                    interpretation.append(f"- TM-score ≥ {threshold_str}: {data['count']} sequences ({data['percentage']:.1f}%)")
        
        # pLDDT Analysis - separate section
        if "plddt_statistics" in analysis and analysis["plddt_statistics"]["count"] > 0:
            interpretation.append("")
            interpretation.append("Protein Confidence Analysis (pLDDT):")
            plddt_stats = analysis["plddt_statistics"]
            interpretation.append(f"- Average pLDDT: {plddt_stats['mean']:.2f}")
            interpretation.append(f"- Highest pLDDT: {plddt_stats['max']:.2f}")
            interpretation.append(f"- Lowest pLDDT: {plddt_stats['min']:.2f}")
            interpretation.append(f"- Median pLDDT: {plddt_stats['median']:.2f}")
            interpretation.append(f"- Standard deviation: {plddt_stats['std_dev']:.2f}")
            interpretation.append("")
            
            # pLDDT quality assessment
            avg_plddt = plddt_stats['mean']
            if avg_plddt >= 90:
                plddt_quality = "very high confidence - structures are highly reliable"
            elif avg_plddt >= 70:
                plddt_quality = "confident - structures are generally reliable"
            elif avg_plddt >= 50:
                plddt_quality = "low confidence - structures may contain significant errors"
            else:
                plddt_quality = "very low confidence - structures are likely unreliable"
                
            interpretation.append(f"Overall pLDDT confidence assessment: {plddt_quality}")
            
            # pLDDT threshold analysis
            if "plddt_threshold_counts" in analysis:
                interpretation.append("")
                interpretation.append("pLDDT Confidence Distribution (sequences meeting or exceeding threshold):")
                for threshold_str in sorted(analysis["plddt_threshold_counts"].keys(), key=int):
                    data = analysis["plddt_threshold_counts"][threshold_str]
                    interpretation.append(f"- pLDDT ≥ {threshold_str}: {data['count']} sequences ({data['percentage']:.1f}%)")
        
        # Failed sequences
        if summary['failed_sequences']:
            interpretation.append("\nFailed Sequences:")
            for seq_id in summary['failed_sequences']:
                error = analysis['details'][seq_id].get('error', 'Unknown error')
                interpretation.append(f"- {seq_id}: {error}")
        
        # Skipped duplicate sequences
        if analysis['skipped_duplicate_sequences']:
            interpretation.append("\nSkipped Duplicate Sequences:")
            for dup in analysis['skipped_duplicate_sequences']:
                interpretation.append(f"- {dup['query_id']} matches {dup['reference_id']} (skipped prediction)")
        
        # Reference matches
        if analysis['reference_matches']:
            interpretation.append("\nReference Sequence Matches:")
            for match in analysis['reference_matches']:
                interpretation.append(f"- {match['query_id']} matches {match['reference_id']} (length: {match['sequence_length']})")
        
        # Save to file
        with open(sci_file, 'w') as f:
            f.write('\n'.join(interpretation))
        
    def _load_reference_seqs(self, reference_seqs_file: Optional[Path] = None) -> Dict[str, str]:
        """Load reference sequences from JSON file."""
        if reference_seqs_file:
            try:
                with open(reference_seqs_file) as f:
                    data = json.load(f)
                return {entry["sequence"]: entry for entry in data}
            except Exception as e:
                logger.error(f"Warning: Failed to load reference sequences: {str(e)}")
                return {}
        else:
            return None
            
    def _load_input_sequences(self, input_fasta: Optional[Path] = None) -> Dict[str, str]:
        """Load sequences from input FASTA file."""
        if input_fasta:
            try:
                sequences = {}
                for record in SeqIO.parse(str(input_fasta), "fasta"):
                    sequences[record.id] = str(record.seq)
                return sequences
            except Exception as e:
                logger.error(f"Warning: Failed to load input sequences: {str(e)}")
                return {}
        else:
            return None
            
    def _load_results(self, summary_file: Path) -> Dict:
        """Load structure comparison results from summary file."""
        try:
            with open(summary_file) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load results: {e}")
            return {}
            
    def _calculate_threshold_counts(self, scores: List[float], thresholds: List[float]) -> Dict[float, int]:
        """Calculate how many scores exceed each threshold."""
        counts = defaultdict(int)
        for threshold in thresholds:
            counts[threshold] = sum(1 for score in scores if score >= threshold)
        return dict(counts)
        
    def _calculate_statistics(self, tm_scores: List[float]) -> Dict:
        """Calculate statistical measures for TM-scores."""
        return {
            "count": len(tm_scores),
            "mean": float(np.mean(tm_scores)),
            "median": float(np.median(tm_scores)),
            "std_dev": float(np.std(tm_scores)),
            "variance": float(np.var(tm_scores)),
            "min": float(np.min(tm_scores)),
            "max": float(np.max(tm_scores))
        }
        
    def _analyze_thresholds(self, tm_scores: List[float]) -> Dict:
        """Analyze TM-scores against different thresholds."""
        thresholds = {
            "0.5": 0.5,  # Minimal structural similarity
            "0.6": 0.6,  # Moderate structural similarity
            "0.7": 0.7,  # Good structural similarity
            "0.8": 0.8,  # High structural similarity
            "0.9": 0.9   # Very high structural similarity
        }
        
        results = {}
        for name, threshold in thresholds.items():
            count = sum(1 for score in tm_scores if score >= threshold)
            percentage = (count / len(tm_scores)) * 100 if tm_scores else 0
            results[name] = {
                "count": count,
                "percentage": float(percentage)
            }
            
        return results
        
    def run_analysis(self, summary_file: Path, reference_seqs_file: Optional[Path] = None, input_fasta: Optional[Path] = None) -> None:
        """Run the analysis on structure comparison results."""
        self.results = self._load_results(summary_file)
        if not self.results:
            logger.error("No results to analyze")
            return
            
        # Extract TM-scores
        tm_scores = []
        for result in self.results.values():
            if result.get("best_match") and result["best_match"].get("tm_score"):
                tm_scores.append(result["best_match"]["tm_score"])
                
        if not tm_scores:
            logger.error("No valid TM-scores found in results")
            return
            
        # Calculate statistics
        self.analysis = {
            "statistics": self._calculate_statistics(tm_scores),
            "threshold_analysis": self._analyze_thresholds(tm_scores),
            "scientific_interpretation": self._generate_interpretation(tm_scores)
        }
        
    def _generate_interpretation(self, tm_scores: List[float]) -> str:
        """Generate scientific interpretation of results."""
        stats = self._calculate_statistics(tm_scores)
        thresholds = self._analyze_thresholds(tm_scores)
        
        interpretation = []
        
        # Overall assessment
        interpretation.append(f"Analysis of {stats['count']} protein structure predictions:")
        
        # Statistical summary
        interpretation.append("\nStatistical Summary:")
        interpretation.append(f"- Mean TM-score: {stats['mean']:.4f}")
        interpretation.append(f"- Median TM-score: {stats['median']:.4f}")
        interpretation.append(f"- Standard deviation: {stats['std_dev']:.4f}")
        interpretation.append(f"- Range: {stats['min']:.4f} to {stats['max']:.4f}")
        
        # Quality distribution
        interpretation.append("\nQuality Distribution:")
        for threshold, data in thresholds.items():
            interpretation.append(f"- {data['percentage']:.1f}% of structures have TM-score ≥ {threshold}")
            
        # Overall quality assessment
        mean_score = stats['mean']
        if mean_score >= 0.9:
            quality = "excellent"
        elif mean_score >= 0.8:
            quality = "very good"
        elif mean_score >= 0.7:
            quality = "good"
        elif mean_score >= 0.6:
            quality = "moderate"
        else:
            quality = "poor"
            
        interpretation.append(f"\nOverall Quality Assessment: {quality.capitalize()}")
        
        return "\n".join(interpretation)
        
    def save_results(self, output_dir: Path) -> None:
        """Save analysis results to files."""
        if not self.analysis:
            logger.error("No analysis results to save")
            return
            
        try:
            # Save JSON results
            json_file = output_dir / "analysis_results.json"
            with open(json_file, 'w') as f:
                json.dump(self.analysis, f, indent=2)
                
            # Save CSV summary
            csv_file = output_dir / "analysis_results.csv"
            with open(csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Metric", "Value"])
                
                # Write statistics
                for metric, value in self.analysis["statistics"].items():
                    writer.writerow([metric, f"{value:.4f}" if isinstance(value, float) else value])
                    
                # Write threshold analysis
                writer.writerow([])
                writer.writerow(["Threshold", "Count", "Percentage"])
                for threshold, data in self.analysis["threshold_analysis"].items():
                    writer.writerow([
                        f"TM-score ≥ {threshold}",
                        data["count"],
                        f"{data['percentage']:.1f}%"
                    ])
                    
            # Save scientific interpretation
            text_file = output_dir / "scientific_analysis.txt"
            with open(text_file, 'w') as f:
                f.write(self.analysis["scientific_interpretation"])
                
            logger.info(f"Analysis results saved to {output_dir}")
            
        except Exception as e:
            logger.error(f"Failed to save analysis results: {e}")
        
    def analyze_results_legacy(self) -> Dict:
        """
        Analyze structure comparison results and generate comprehensive statistics.
        
        Returns:
            Dictionary containing:
            - Threshold counts
            - Statistical measures
            - Reference sequence matches
            - Error/missing sequence information
        """
        summary = self._load_results()
        
        # Extract TM-scores and track sequences
        tm_scores = []
        missing_scores = []
        reference_matches = []
        
        for seq_id, results in summary.items():
            if results.get("best_match") and results["best_match"].get("tm_score") is not None:
                tm_scores.append(results["best_match"]["tm_score"])
            else:
                missing_scores.append(seq_id)
                
            # Check if sequence exists in reference set
            if self.reference_sequences is not None:
                sequence = self.reference_sequences.get(seq_id)
                if sequence:
                    reference_matches.append({
                        "sequence_id": seq_id,
                        "reference_id": seq_id,
                        "description": "Exact match to reference sequence"
                    })
        
        # Calculate threshold counts
        thresholds = [i/10 for i in range(11)]  # 0.0, 0.1, ..., 1.0
        threshold_counts = self._calculate_threshold_counts(tm_scores, thresholds)
        
        # Calculate statistics
        statistics = self._calculate_statistics(tm_scores)
        
        results = {
            "total_sequences": len(summary),
            "sequences_with_scores": len(tm_scores),
            "missing_scores": {
                "count": len(missing_scores),
                "sequences": missing_scores
            },
            "reference_matches": {
                "count": len(reference_matches),
                "matches": reference_matches
            },
            "threshold_counts": threshold_counts,
            "statistics": statistics
        }
        
        # Add scientific analysis
        results["scientific_analysis"] = self._generate_scientific_analysis(results)
        
        return results
        
    def save_analysis_legacy(self, output_file: Path):
        """
        Run analysis and save results to file.
        
        Args:
            output_file: Path to save analysis results
        """
        results = self.analyze_results_legacy()
        
        # Save JSON results
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
            
        # Save CSV results
        csv_file = output_file.with_suffix('.csv')
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write basic statistics
            writer.writerow(['Metric', 'Value'])
            writer.writerow(['Total Sequences', results['total_sequences']])
            writer.writerow(['Sequences with Scores', results['sequences_with_scores']])
            writer.writerow(['Missing Scores', results['missing_scores']['count']])
            writer.writerow([])
            
            # Write statistical measures
            writer.writerow(['Statistical Measure', 'Value'])
            for key, value in results['statistics'].items():
                writer.writerow([key.capitalize(), f"{value:.4f}"])
            writer.writerow([])
            
            # Write threshold counts
            writer.writerow(['TM-score Threshold', 'Count', 'Percentage'])
            for threshold, count in results['threshold_counts'].items():
                percentage = (count / results['total_sequences']) * 100
                writer.writerow([f">= {threshold:.1f}", count, f"{percentage:.1f}%"])
            writer.writerow([])
            
            # Write reference matches if any
            if results['reference_matches']['count'] > 0:
                writer.writerow(['Reference Matches'])
                writer.writerow(['Sequence ID', 'Reference ID', 'Description'])
                for match in results['reference_matches']['matches']:
                    writer.writerow([match['sequence_id'], match['reference_id'], match['description']])
                    
        # Save scientific analysis
        analysis_file = output_file.parent / "scientific_analysis.txt"
        with open(analysis_file, 'w') as f:
            analysis = results["scientific_analysis"]
            f.write(f"{analysis['title']}\n")
            f.write("=" * len(analysis['title']) + "\n\n")
            
            for section in analysis["sections"]:
                f.write(f"{section['name']}:\n")
                if isinstance(section["points"][0], dict):
                    # Special handling for structure quality distribution
                    for point in section["points"]:
                        f.write(f"- {point['score']}: {point['count']}\n")
                        f.write(f"  ({point['interpretation']})\n")
                else:
                    for point in section["points"]:
                        f.write(f"- {point}\n")
                f.write("\n")
            
        print(f"Analysis results saved to:")
        print(f"- JSON: {output_file}")
        print(f"- CSV: {csv_file}")
        print(f"- Scientific Analysis: {analysis_file}")
        
        # Print summary to console
        print("\nAnalysis Summary:")
        print(f"Total sequences: {results['total_sequences']}")
        print(f"Sequences with scores: {results['sequences_with_scores']}")
        print(f"Missing scores: {results['missing_scores']['count']}")
        
        if results['reference_matches']['count'] > 0:
            print("\nReference Matches:")
            for match in results['reference_matches']['matches']:
                print(f"- {match['sequence_id']} matches {match['reference_id']} ({match['description']})")
        
        print("\nStatistics:")
        for key, value in results['statistics'].items():
            print(f"{key}: {value:.4f}")
            
        print("\nThreshold counts:")
        for threshold, count in results['threshold_counts'].items():
            print(f"TM-score >= {threshold:.1f}: {count}") 
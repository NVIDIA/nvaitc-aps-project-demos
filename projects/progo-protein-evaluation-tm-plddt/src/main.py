# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Main entry point for the protein structure prediction and evaluation pipeline.
"""

import argparse
import sys
from pathlib import Path
import json
import re
import shutil
import datetime

from src.pipeline.esmfold_predictor import ESMfoldPredictor
from src.pipeline.tm_score_calculator import TMScoreCalculator
from src.pipeline.plddt_extractor import PLDDTExtractor
from src.analysis.results_analyzer import ResultsAnalyzer
from src.utils.logger import get_pipeline_logger, setup_run_logging

logger = get_pipeline_logger("pipeline.main")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Protein structure prediction and evaluation pipeline")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Predict and evaluate command
    predict_eval = subparsers.add_parser("predict-and-evaluate", help="Predict structures and evaluate against ground truth")
    predict_eval.add_argument(
        "--fasta",
        type=str,
        required=True,
        help="Path to input FASTA file"
    )
    predict_eval.add_argument(
        "--ground-truth-set",
        type=str,
        required=True,
        help="Name of ground truth set to use for evaluation"
    )
    
    # Evaluate only command
    evaluate = subparsers.add_parser("evaluate", help="Evaluate existing predictions against ground truth")
    evaluate.add_argument(
        "--predictions",
        type=str,
        required=True,
        help="Directory containing predicted PDB structures"
    )
    evaluate.add_argument(
        "--ground-truth-set",
        type=str,
        required=True,
        help="Name of ground truth set to use for evaluation"
    )
    
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
        
    return args

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to be safe for directory names.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for use as directory name
    """
    # Remove extension and path
    name = Path(filename).stem
    # Replace problematic characters with underscores
    name = re.sub(r'[^\w\-]', '_', name)
    # Remove multiple underscores
    name = re.sub(r'_+', '_', name)
    # Remove leading/trailing underscores
    name = name.strip('_')
    return name

def get_unique_output_dir(base_dir: Path, name: str) -> Path:
    """
    Get a unique output directory path, adding suffix if necessary.
    
    Args:
        base_dir: Base directory for outputs
        name: Desired directory name
        
    Returns:
        Unique directory path
    """
    output_dir = base_dir / name
    if not output_dir.exists():
        return output_dir
    
    # Add numeric suffix if directory exists
    counter = 1
    while True:
        output_dir = base_dir / f"{name}_run{counter}"
        if not output_dir.exists():
            return output_dir
        counter += 1

def resolve_fasta_path(fasta_arg: str) -> Path:
    """
    Resolve FASTA file path by checking multiple locations.
    
    Args:
        fasta_arg: FASTA filename or path from command line
        
    Returns:
        Resolved Path object
        
    Raises:
        FileNotFoundError: If file cannot be found in any location
    """
    # List of paths to check
    possible_paths = [
        Path(fasta_arg),  # Try as-is first
        Path("data/input") / fasta_arg,  # Check in data/input
        Path(fasta_arg).name,  # Try just the filename in current directory
    ]
    
    for path in possible_paths:
        if path.exists() and path.is_file():
            logger.info(f"Found FASTA file at: {path}")
            return path.resolve()
    
    # If not found, provide helpful error message
    searched_locations = "\n  - ".join(str(p) for p in possible_paths)
    raise FileNotFoundError(
        f"Could not find FASTA file '{fasta_arg}' in any of these locations:\n  - {searched_locations}"
    )

def resolve_predictions_path(predictions_arg: str) -> Path:
    """
    Resolve predictions directory path by checking multiple locations.
    
    Args:
        predictions_arg: Predictions directory name or path from command line
        
    Returns:
        Resolved Path object
        
    Raises:
        NotADirectoryError: If path cannot be found or is not a directory
    """
    # List of paths to check
    possible_paths = [
        Path(predictions_arg),  # Try as-is first
        Path("data/output") / predictions_arg / "predicted_structures",  # Check in output directory
        Path("data/output") / predictions_arg / "predictions",  # Alternative name
    ]
    
    for path in possible_paths:
        if path.exists() and path.is_dir():
            logger.info(f"Found predictions directory at: {path}")
            return path.resolve()
    
    # If not found, provide helpful error message
    searched_locations = "\n  - ".join(str(p) for p in possible_paths)
    raise NotADirectoryError(
        f"Could not find predictions directory '{predictions_arg}' in any of these locations:\n  - {searched_locations}"
    )

def main():
    """Main pipeline function."""
    try:
        # Parse arguments
        args = parse_args()
        
        # Determine output directory name based on command and input
        base_output_dir = Path("data/output")
        
        if args.command == "predict-and-evaluate":
            # Resolve FASTA file path
            try:
                input_file = resolve_fasta_path(args.fasta)
            except FileNotFoundError as e:
                logger.error(str(e))
                sys.exit(1)
            
            # Use resolved FASTA path for output directory name
            run_name = sanitize_filename(input_file.name)
        elif args.command == "evaluate":
            # Resolve predictions directory path
            try:
                predictions_dir = resolve_predictions_path(args.predictions)
            except NotADirectoryError as e:
                logger.error(str(e))
                sys.exit(1)
                
            # Use predictions directory name for output
            run_name = f"eval_{sanitize_filename(predictions_dir.parent.name)}"
        
        # Get unique output directory
        output_dir = get_unique_output_dir(base_output_dir, run_name)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up run-specific logging
        setup_run_logging(output_dir)
        logger.info(f"Output directory created: {output_dir}")
        
        # Copy input FASTA file to run directory for self-contained runs
        if args.command == "predict-and-evaluate":
            input_fasta_copy = output_dir / "input.fasta"
            shutil.copy2(input_file, input_fasta_copy)
            logger.info(f"Copied input FASTA to run directory: {input_fasta_copy}")
        
        # Create run metadata file for complete self-containment
        run_metadata = {
            "command": args.command,
            "ground_truth_set": args.ground_truth_set,
            "run_directory": str(output_dir),
            "run_name": run_name,
            "timestamp": Path(__file__).stat().st_mtime,  # Will be replaced with actual timestamp
        }
        
        if args.command == "predict-and-evaluate":
            run_metadata.update({
                "original_fasta_path": str(input_file),
                "fasta_filename": input_file.name,
                "copied_fasta_path": str(input_fasta_copy)
            })
        elif args.command == "evaluate":
            run_metadata.update({
                "predictions_directory": str(predictions_dir),
                "original_predictions_arg": args.predictions
            })
        
        # Save run metadata
        run_metadata["timestamp"] = datetime.datetime.now().isoformat()
        metadata_file = output_dir / "run_metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(run_metadata, f, indent=2)
        logger.info(f"Saved run metadata to: {metadata_file}")
        
        # Initialize components
        predictor = ESMfoldPredictor(ground_truth_set=args.ground_truth_set)
        calculator = TMScoreCalculator()
        plddt_extractor = PLDDTExtractor()
        analyzer = ResultsAnalyzer(ground_truth_set=args.ground_truth_set)
        
        if args.command == "predict-and-evaluate":
            # Set up paths
            ground_truth_dir = Path("data/ground_truth") / args.ground_truth_set / "pdbs"
            
            # Run predictions
            logger.info("=== Starting Structure Prediction ===")
            predicted_structures, skipped_duplicates = predictor.predict_structures(
                input_file,
                output_dir / "predicted_structures"
            )
            
            # Convert predicted_structures to dictionary
            structure_dict = {}
            for structure_path in predicted_structures:
                structure_dict[structure_path.stem] = structure_path
                
        elif args.command == "evaluate":
            # Set up paths
            ground_truth_dir = Path("data/ground_truth") / args.ground_truth_set / "pdbs"
            
            # Get predicted structures
            structure_dict = {}
            for structure_path in predictions_dir.glob("*.pdb"):
                structure_dict[structure_path.stem] = structure_path
            
            # No skipped duplicates in evaluate mode
            skipped_duplicates = {}
        
        # pLDDT Analysis
        logger.info("=== Starting pLDDT Analysis ===")
        plddt_results = plddt_extractor.batch_extract(structure_dict)
        
        # Structure comparison for both commands
        if ground_truth_dir.exists():
            logger.info("=== Starting Structure Comparison ===")
            
            # Pass output directory to the calculator
            calculator.output_base_dir = output_dir
            
            # Use batch_calculate for consistent results format
            comparison_results = calculator.batch_calculate(
                structure_dict,
                ground_truth_dir,
                None  # Not used, detailed results are saved in output_dir/detailed_tm_scores
            )
            
            # Results analysis
            logger.info("=== Starting Results Analysis ===")
            
            # Get FASTA file path for reference sequence matching
            fasta_path = None
            if args.command == "predict-and-evaluate":
                fasta_path = input_file
            
            analysis_results = analyzer.analyze_results(
                comparison_results, 
                fasta_path, 
                skipped_duplicates,
                plddt_results  # Pass pLDDT results to analyzer
            )
            
            # Save analysis
            analyzer.save_analysis(analysis_results, output_dir / "analysis")
            
            # Save raw comparison results too
            results_file = output_dir / "comparison_results.json"
            with open(results_file, "w") as f:
                json.dump(comparison_results, f, indent=2)
            
            # Save pLDDT results
            plddt_file = output_dir / "plddt_results.json"
            with open(plddt_file, "w") as f:
                json.dump(plddt_results, f, indent=2)
            
            logger.info(f"Results saved to {output_dir}")
        else:
            logger.error(f"Ground truth directory not found: {ground_truth_dir}")
            sys.exit(1)
        
        logger.info("Pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    main() 
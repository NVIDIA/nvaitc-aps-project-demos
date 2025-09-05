# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
ESMFold structure prediction module for ProteinGO pipeline.
"""

import os
import json
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dotenv import dotenv_values
from Bio import SeqIO

from src.utils.logger import get_pipeline_logger

logger = get_pipeline_logger("esmfold_predictor")

class ESMfoldPredictor:
    """Handler for ESMFold structure predictions."""
    
    def __init__(self, ground_truth_set: Optional[str] = None):
        """Initialize predictor with API configuration.
        
        Args:
            ground_truth_set: Name of ground truth set to use for reference sequences
        """
        env_file = Path(__file__).parent.parent.parent / 'config' / '.env'
        config = dotenv_values(env_file)
        self.api_key = config.get('NVIDIA_API_KEY')
        logger.info(f"Loaded API key from {env_file}")
        
        if not self.api_key:
            logger.warning("NVIDIA API key not found in environment variables")
            logger.warning("Structure prediction will be skipped")
            
        self.api_url = "https://health.api.nvidia.com/v1/biology/nvidia/esmfold"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
        
        # Load reference sequences for duplicate checking
        self.reference_sequences = self._load_reference_sequences(ground_truth_set)
        
    def _load_reference_sequences(self, ground_truth_set: Optional[str] = None) -> Dict[str, str]:
        """Load reference sequences from JSON file.
        
        Args:
            ground_truth_set: Name of ground truth set to load reference sequences from
            
        Returns:
            Dictionary mapping sequences to reference IDs
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
                # Create a mapping from sequence to reference ID for quick lookup
                seq_to_ref = {}
                
                if isinstance(data, list):
                    # Array format: [{"sequence": "...", "id": "...", "description": "..."}]
                    for item in data:
                        seq_to_ref[item["sequence"]] = item["id"]
                else:
                    # Dictionary format: {"id": "sequence"}
                    for ref_id, sequence in data.items():
                        seq_to_ref[sequence] = ref_id
                        
                logger.info(f"Loaded {len(seq_to_ref)} reference sequences for duplicate checking from {reference_file.name}")
                return seq_to_ref
        except FileNotFoundError:
            logger.info("No reference_seqs.json file found, duplicate checking disabled")
            return {}
        except Exception as e:
            logger.warning(f"Could not load reference sequences: {e}")
            return {}
        
    def _load_api_key(self) -> str:
        """Load API key from environment file."""
        env_file = Path("config/.env")
        if not env_file.exists():
            raise FileNotFoundError("API key file not found")
            
        try:
            with open(env_file) as f:
                for line in f:
                    if line.startswith("NVIDIA_API_KEY="):
                        api_key = line.strip().split("=")[1].strip('"')
                        logger.info("Loaded API key from config/.env")
                        return api_key
                        
            raise ValueError("API key not found in .env file")
            
        except Exception as e:
            raise RuntimeError(f"Failed to load API key: {str(e)}")
            
    def predict_structure(self, sequence: str, output_file: Path) -> Optional[Path]:
        """
        Predict structure for a single sequence.
        
        Args:
            sequence: Amino acid sequence
            output_file: Path to save PDB file
            
        Returns:
            Path to output file if successful, None otherwise
        """
        if not self.api_key:
            logger.warning("Skipping structure prediction - no API key available")
            return None
            
        try:
            # Log request details
            logger.info(f"API URL: {self.api_url}")
            logger.info(f"Headers: {self.headers}")
            logger.info(f"Requesting structure prediction for sequence of length {len(sequence)}")
            
            # Make API request
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={"sequence": sequence}
            )
            
            # Check response
            if response.status_code == 200:
                # Parse the JSON response
                try:
                    result = response.json()
                    pdb_content = result.get('pdbs', [''])[0]  # Get the first PDB from the list
                    
                    # If the PDB content has escaped newlines, unescape them
                    if '\\n' in pdb_content:
                        pdb_content = pdb_content.replace('\\n', '\n')
                        
                except (json.JSONDecodeError, KeyError, IndexError):
                    # If JSON parsing fails, try to use the text directly
                    pdb_content = response.text
                    # Still try to unescape if needed
                    if '\\n' in pdb_content:
                        pdb_content = pdb_content.replace('\\n', '\n')
                
                # Save PDB file
                output_file.parent.mkdir(parents=True, exist_ok=True)
                with open(output_file, "w") as f:
                    f.write(pdb_content)
                    
                # Log success
                file_size = output_file.stat().st_size
                logger.info(f"Structure prediction saved to {output_file}")
                logger.info(f"PDB file size: {file_size} bytes")
                
                return output_file
                
            else:
                logger.error(f"API request failed with status {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error predicting structure: {str(e)}")
            return None
            
    def predict_structures(self, fasta_file: Path, output_dir: Path) -> Tuple[List[Path], Dict[str, str]]:
        """
        Predict structures for all sequences in a FASTA file.
        Skips sequences that are exact duplicates of reference sequences.
        
        Args:
            fasta_file: Path to input FASTA file
            output_dir: Directory to save PDB files
            
        Returns:
            Tuple of:
            - List of paths to predicted structure files
            - Dictionary of skipped sequences {seq_id: reference_id}
        """
        predicted_structures = []
        skipped_duplicates = {}
        
        try:
            # Create output directory
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Process each sequence
            for i, record in enumerate(SeqIO.parse(str(fasta_file), "fasta"), 1):
                sequence = str(record.seq)
                
                # Check if sequence is a duplicate of a reference sequence
                if sequence in self.reference_sequences:
                    reference_id = self.reference_sequences[sequence]
                    skipped_duplicates[record.id] = reference_id
                    logger.info(f"Skipping {record.id} - exact match to reference sequence {reference_id}")
                    continue
                
                # Generate output file path
                output_file = output_dir / f"{record.id}.pdb"
                if not record.id:
                    output_file = output_dir / f"test_protein_{i}.pdb"
                    
                # Predict structure
                result = self.predict_structure(sequence, output_file)
                if result:
                    predicted_structures.append(result)
                    
            # Log summary
            if skipped_duplicates:
                logger.info(f"Skipped {len(skipped_duplicates)} duplicate sequences")
                for seq_id, ref_id in skipped_duplicates.items():
                    logger.info(f"  - {seq_id} matches {ref_id}")
                    
            return predicted_structures, skipped_duplicates
            
        except Exception as e:
            logger.error(f"Error processing FASTA file: {str(e)}")
            return predicted_structures, skipped_duplicates 
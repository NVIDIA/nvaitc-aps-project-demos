# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
FASTA file handling utility for ProteinGO pipeline.
Provides functions for reading, writing, and validating FASTA files.
"""

from pathlib import Path
from typing import Dict, List, Tuple
import logging
from src.utils.logger import get_pipeline_logger

logger = get_pipeline_logger("fasta_handler")

class FastaSequence:
    """Class representing a single FASTA sequence."""
    def __init__(self, identifier: str, sequence: str):
        self.identifier = identifier
        self.sequence = sequence.upper()  # Convert to uppercase
        
    @property
    def length(self) -> int:
        return len(self.sequence)
    
    def validate(self) -> bool:
        """Validate the sequence contains only valid amino acid characters."""
        valid_chars = set('ACDEFGHIKLMNPQRSTVWY')
        sequence_chars = set(self.sequence)
        invalid_chars = sequence_chars - valid_chars
        
        if invalid_chars:
            logger.warning(f"Invalid characters found in sequence {self.identifier}: {invalid_chars}")
            return False
        return True
    
    def to_fasta_format(self) -> str:
        """Convert the sequence to FASTA format."""
        return f">{self.identifier}\n{self.sequence}\n"

class FastaHandler:
    """Handler for FASTA file operations."""
    
    @staticmethod
    def read_fasta(file_path: Path) -> Dict[str, FastaSequence]:
        """
        Read sequences from a FASTA file.
        
        Args:
            file_path: Path to the FASTA file
            
        Returns:
            Dict mapping sequence IDs to FastaSequence objects
        """
        sequences = {}
        logger.info(f"Reading FASTA file: {file_path}")
        
        try:
            with open(file_path, "r") as file:
                current_id = None
                current_seq = []
                
                for line in file:
                    line = line.strip()
                    if not line:
                        continue
                        
                    if line.startswith(">"):
                        if current_id:
                            sequences[current_id] = FastaSequence(
                                current_id, 
                                "".join(current_seq)
                            )
                        current_id = line[1:]
                        current_seq = []
                    else:
                        current_seq.append(line)
                        
                if current_id:
                    sequences[current_id] = FastaSequence(
                        current_id, 
                        "".join(current_seq)
                    )
                    
            logger.info(f"Successfully read {len(sequences)} sequences from {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to read sequences from {file_path}")
            logger.error(f"Error: {str(e)}")
            raise
            
        return sequences
    
    @staticmethod
    def write_fasta(sequences: Dict[str, FastaSequence], file_path: Path) -> None:
        """
        Write sequences to a FASTA file.
        
        Args:
            sequences: Dict mapping sequence IDs to FastaSequence objects
            file_path: Path where to write the FASTA file
        """
        logger.info(f"Writing {len(sequences)} sequences to {file_path}")
        
        try:
            with open(file_path, "w") as file:
                for seq in sequences.values():
                    file.write(seq.to_fasta_format())
                    
            logger.info(f"Successfully wrote sequences to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to write sequences to {file_path}")
            logger.error(f"Error: {str(e)}")
            raise
    
    @staticmethod
    def filter_sequences(
        sequences: Dict[str, FastaSequence], 
        max_length: int = None,
        validate: bool = True
    ) -> Dict[str, FastaSequence]:
        """
        Filter sequences based on various criteria.
        
        Args:
            sequences: Dict mapping sequence IDs to FastaSequence objects
            max_length: Maximum allowed sequence length
            validate: Whether to validate sequence characters
            
        Returns:
            Dict of filtered sequences
        """
        filtered_sequences = {}
        
        for seq_id, seq in sequences.items():
            # Check sequence length
            if max_length and seq.length > max_length:
                logger.warning(f"Sequence {seq_id} exceeds maximum length: {seq.length} > {max_length}")
                continue
                
            # Validate sequence characters
            if validate and not seq.validate():
                logger.warning(f"Sequence {seq_id} contains invalid characters")
                continue
                
            filtered_sequences[seq_id] = seq
            
        logger.info(f"Filtered {len(sequences) - len(filtered_sequences)} sequences")
        return filtered_sequences 
# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
FASTA file handling module for ProteinGO pipeline.
"""

from pathlib import Path
from typing import Dict
from Bio import SeqIO

class FastaHandler:
    """Handler for FASTA file operations."""
    
    def read_fasta(self, fasta_file: Path) -> Dict[str, str]:
        """
        Read sequences from a FASTA file.
        
        Args:
            fasta_file: Path to FASTA file
            
        Returns:
            Dictionary mapping sequence IDs to sequences
        """
        sequences = {}
        
        for record in SeqIO.parse(str(fasta_file), "fasta"):
            sequences[record.id] = str(record.seq)
            
        return sequences 
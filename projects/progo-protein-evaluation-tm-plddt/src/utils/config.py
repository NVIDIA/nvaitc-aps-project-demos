# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Configuration module for ProteinGO pipeline.
Handles environment variables and pipeline settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables from .env file
env_file = Path(__file__).parent.parent.parent / 'config' / '.env'
logger.info(f"Loading environment variables from: {env_file}")
load_dotenv(env_file)

# API Configuration
NVIDIA_API_KEY = os.getenv('NVIDIA_API_KEY')
logger.info(f"Loaded NVIDIA_API_KEY: {NVIDIA_API_KEY}")
INVOKE_URL = "https://health.api.nvidia.com/v1/biology/nvidia/esmfold"

# Directory Configuration
ROOT_DIR = Path(__file__).parent.parent.parent
DATA_DIR = ROOT_DIR / 'data'
INPUT_DIR = DATA_DIR / 'input'
GROUND_TRUTH_DIR = DATA_DIR / 'ground_truth'
OUTPUT_DIR = DATA_DIR / 'output'
LOG_DIR = ROOT_DIR / 'logs'

# Ensure directories exist
for directory in [INPUT_DIR, GROUND_TRUTH_DIR, OUTPUT_DIR, LOG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Pipeline Configuration
MAX_SEQUENCE_LENGTH = 1000  # Maximum sequence length for ESMFold
BATCH_SIZE = 10  # Number of sequences to process in parallel
TIMEOUT = 300  # API timeout in seconds

# Logging Configuration
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

def validate_config():
    """Validate the configuration settings."""
    if not NVIDIA_API_KEY:
        raise ValueError("NVIDIA_API_KEY not found in environment variables")
    
    if not all(dir.exists() for dir in [INPUT_DIR, GROUND_TRUTH_DIR, OUTPUT_DIR, LOG_DIR]):
        raise ValueError("Required directories do not exist")
    
    return True 
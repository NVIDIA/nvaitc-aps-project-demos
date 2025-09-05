# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Logging configuration for ProteinGO pipeline.
"""

import logging
from pathlib import Path
from datetime import datetime

# Global variable to store run-specific log directory
_run_log_dir = None

def setup_logger(name: str, log_file: Path = None) -> logging.Logger:
    """
    Set up a logger with console and file handlers.
    
    Args:
        name: Name for the logger
        log_file: Optional specific log file path
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Remove any existing handlers
    logger.handlers = []
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create file handler for central logs
    if log_file is None:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"{name}_{timestamp}.log"
    
    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Add a divider to the log
    logger.info("=" * 60)
    logger.info(f"Starting new logging session for {name}")
    logger.info(f"Log file location: {log_file}")
    logger.info("=" * 60)
    
    return logger

def get_pipeline_logger(name: str) -> logging.Logger:
    """
    Get a logger configured for the pipeline.
    
    Args:
        name: Name for the logger
        
    Returns:
        Configured logger instance
    """
    return setup_logger(name)

def setup_run_logging(output_dir: Path) -> None:
    """
    Set up run-specific logging by adding file handlers to all existing loggers.
    This should be called after the output directory is created.
    
    Args:
        output_dir: The output directory for the current run
    """
    global _run_log_dir
    _run_log_dir = output_dir / "logs"
    _run_log_dir.mkdir(parents=True, exist_ok=True)
    
    # Get the timestamp for consistent naming
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Get all existing loggers
    loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
    
    # Add the main pipeline log
    pipeline_log = _run_log_dir / f"pipeline_run_{timestamp}.log"
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Add file handler to each logger
    for logger in loggers:
        if logger.handlers:  # Only add to configured loggers
            # Create a combined log file for the run
            run_handler = logging.FileHandler(pipeline_log)
            run_handler.setFormatter(formatter)
            logger.addHandler(run_handler)
    
    # Log the setup
    main_logger = logging.getLogger("pipeline.main")
    if main_logger.handlers:
        main_logger.info(f"Run-specific logging initialized in: {_run_log_dir}")
        main_logger.info(f"Combined log file: {pipeline_log}")

def log_error_with_traceback(logger: logging.Logger, error: Exception, context: str = ""):
    """
    Log an error with its full traceback and context.
    
    Args:
        logger: Logger instance
        error: Exception to log
        context: Additional context about where/when the error occurred
    """
    import traceback
    error_msg = f"Error occurred{f' in {context}' if context else ''}"
    logger.error(error_msg)
    logger.error(f"Error type: {type(error).__name__}")
    logger.error(f"Error message: {str(error)}")
    logger.error("Traceback:")
    logger.error(traceback.format_exc()) 
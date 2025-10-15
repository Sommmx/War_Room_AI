"""
War_RoomAI Data Loader Module

This module handles loading and parsing of metrics and log data from various sources.
It provides functions to load CSV metrics files and parse log files from a directory.

Author: War_RoomAI Team
Version: 1.0.0
"""

import pandas as pd
import glob
import os
from typing import List, Optional
import logging
from config import BASE_DATE

# Configure logging for this module
logger = logging.getLogger(__name__)


def load_metrics(filepath: str) -> pd.DataFrame:
    """
    Load metrics data from a CSV file.
    
    Expected CSV format: timestamp, service, metric_name, value (tab-separated)
    
    Args:
        filepath: Path to the metrics CSV file
        
    Returns:
        pd.DataFrame: Loaded metrics data with parsed timestamps
        
    Raises:
        FileNotFoundError: If the metrics file doesn't exist
        ValueError: If the file format is invalid or data cannot be parsed
        pd.errors.EmptyDataError: If the file is empty
    """
    logger.info(f"Loading metrics from: {filepath}")
    
    # Validate file exists
    if not os.path.exists(filepath):
        error_msg = f"Metrics file not found: {filepath}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    # Check if file is empty
    if os.path.getsize(filepath) == 0:
        error_msg = f"Metrics file is empty: {filepath}"
        logger.error(error_msg)
        raise pd.errors.EmptyDataError(error_msg)
    
    try:
        # Load CSV with tab separator and no header
        df = pd.read_csv(
            filepath, 
            sep='\t', 
            header=None, 
            names=['time_stamp', 'service', 'metric_name', 'value'],
            dtype={'time_stamp': str, 'service': str, 'metric_name': str, 'value': float}
        )
        
        logger.info(f"Successfully loaded {len(df)} metric records")
        
        # Validate required columns are present
        required_columns = ['time_stamp', 'service', 'metric_name', 'value']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            error_msg = f"Missing required columns: {missing_columns}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Parse timestamps
        try:
            df['time_stamp'] = pd.to_datetime(df['time_stamp'], format='%d-%m-%Y %H:%M', errors='coerce')
            
            # Check for parsing failures
            invalid_timestamps = df['time_stamp'].isna().sum()
            if invalid_timestamps > 0:
                logger.warning(f"Failed to parse {invalid_timestamps} timestamps")
                # Remove rows with invalid timestamps
                df = df.dropna(subset=['time_stamp'])
                
        except Exception as e:
            error_msg = f"Failed to parse timestamps: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Validate numeric values
        try:
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            invalid_values = df['value'].isna().sum()
            if invalid_values > 0:
                logger.warning(f"Found {invalid_values} invalid numeric values")
                df = df.dropna(subset=['value'])
        except Exception as e:
            error_msg = f"Failed to parse numeric values: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Sort by timestamp
        df = df.sort_values(by='time_stamp')
        
        logger.info(f"Processed metrics data: {len(df)} valid records")
        return df
        
    except pd.errors.EmptyDataError:
        error_msg = f"Metrics file is empty: {filepath}"
        logger.error(error_msg)
        raise
    except Exception as e:
        error_msg = f"Failed to load metrics from {filepath}: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)


def load_logs(folder_path: str) -> pd.DataFrame:
    """
    Load log data from all .log files in a directory.
    
    Expected log format: timestamp | level | message (pipe-separated)
    
    Args:
        folder_path: Path to directory containing log files
        
    Returns:
        pd.DataFrame: Combined log data from all files with parsed timestamps
        
    Raises:
        FileNotFoundError: If the folder doesn't exist
        ValueError: If no log files found or data cannot be parsed
    """
    logger.info(f"Loading logs from directory: {folder_path}")
    
    # Validate directory exists
    if not os.path.exists(folder_path):
        error_msg = f"Log directory not found: {folder_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    if not os.path.isdir(folder_path):
        error_msg = f"Path is not a directory: {folder_path}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Find all log files
    log_pattern = os.path.join(folder_path, "*.log")
    log_files = glob.glob(log_pattern)
    
    if not log_files:
        error_msg = f"No .log files found in directory: {folder_path}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"Found {len(log_files)} log files: {[os.path.basename(f) for f in log_files]}")
    
    logs = []
    base_date = pd.to_datetime(BASE_DATE)
    
    for file_path in log_files:
        try:
            logger.debug(f"Processing log file: {file_path}")
            
            # Check if file is empty
            if os.path.getsize(file_path) == 0:
                logger.warning(f"Skipping empty log file: {file_path}")
                continue
            
            # Load log file
            df = pd.read_csv(
                file_path, 
                sep="|", 
                names=['timestamp', 'level', 'message'],
                dtype={'timestamp': str, 'level': str, 'message': str}
            )
            
            # Validate required columns
            required_columns = ['timestamp', 'level', 'message']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.warning(f"Skipping {file_path}: missing columns {missing_columns}")
                continue
            
            # Parse timestamps
            try:
                df['timestamp'] = pd.to_datetime(df['timestamp'].str.strip(), format='%H:%M:%S', errors='coerce')
                
                # Reconstruct full timestamps using base date
                df['timestamp'] = df['timestamp'].apply(
                    lambda t: base_date + pd.Timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
                    if pd.notnull(t) else pd.NaT
                )
                
                # Remove rows with invalid timestamps
                invalid_timestamps = df['timestamp'].isna().sum()
                if invalid_timestamps > 0:
                    logger.warning(f"Removing {invalid_timestamps} invalid timestamps from {file_path}")
                    df = df.dropna(subset=['timestamp'])
                
            except Exception as e:
                logger.warning(f"Failed to parse timestamps in {file_path}: {str(e)}")
                continue
            
            # Add service name based on filename
            service_name = os.path.basename(file_path).replace('.log', '')
            df['service'] = service_name
            
            # Clean up message column (remove extra whitespace)
            df['message'] = df['message'].str.strip()
            
            logs.append(df)
            logger.debug(f"Successfully processed {len(df)} log entries from {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to process log file {file_path}: {str(e)}")
            # Continue processing other files even if one fails
            continue
    
    if not logs:
        error_msg = f"No valid log data found in directory: {folder_path}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    try:
        # Combine all log dataframes
        combined_logs = pd.concat(logs, ignore_index=True)
        logger.info(f"Successfully loaded {len(combined_logs)} log records from {len(logs)} files")
        
        # Sort by timestamp
        combined_logs = combined_logs.sort_values(by='timestamp')
        
        return combined_logs
        
    except Exception as e:
        error_msg = f"Failed to combine log data: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
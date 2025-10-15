"""
War_RoomAI Anomaly Detector Module

This module contains functions for detecting anomalies in metrics data and
identifying warning-level log entries. It compares metric values against
configured thresholds and filters log entries by severity level.

Author: War_RoomAI Team
Version: 1.0.0
"""

import pandas as pd
import logging
from typing import List, Dict, Any
from config import thresholds, get_threshold

# Configure logging for this module
logger = logging.getLogger(__name__)


def metric_anomaly(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect metric anomalies by comparing values against configured thresholds.
    
    This function iterates through all metric records and identifies those
    that exceed the configured threshold values for their respective metrics
    and services.
    
    Args:
        df: DataFrame containing metric data with columns:
            - time_stamp: Timestamp of the metric
            - service: Service name (e.g., 'frontend', 'api', 'database')
            - metric_name: Name of the metric (e.g., 'cpu_pct', 'latency_ms')
            - value: Numeric value of the metric
            
    Returns:
        pd.DataFrame: DataFrame containing only the anomalous metric records
        
    Raises:
        ValueError: If input DataFrame is empty or missing required columns
        TypeError: If input is not a pandas DataFrame
    """
    logger.info("Starting metric anomaly detection")
    
    # Validate input
    if not isinstance(df, pd.DataFrame):
        error_msg = "Input must be a pandas DataFrame"
        logger.error(error_msg)
        raise TypeError(error_msg)
    
    if df.empty:
        logger.warning("Input DataFrame is empty - no anomalies to detect")
        return pd.DataFrame(columns=['time_stamp', 'service', 'metric_name', 'value'])
    
    # Validate required columns
    required_columns = ['time_stamp', 'service', 'metric_name', 'value']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        error_msg = f"Missing required columns: {missing_columns}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"Analyzing {len(df)} metric records for anomalies")
    
    anomalies = []
    processed_count = 0
    error_count = 0
    
    try:
        for index, row in df.iterrows():
            try:
                metric = row['metric_name']
                value = row['value']
                service = row['service']
                
                # Skip if any required field is null/NaN
                if pd.isna(metric) or pd.isna(value) or pd.isna(service):
                    logger.debug(f"Skipping row {index}: missing required data")
                    continue
                
                # Get threshold for this metric and service
                threshold_value = get_threshold(metric, service)
                
                if threshold_value is None:
                    logger.debug(f"No threshold configured for metric '{metric}' and service '{service}'")
                    continue
                
                # Check if value exceeds threshold
                if value > threshold_value:
                    logger.debug(f"Anomaly detected: {service}.{metric} = {value} > {threshold_value}")
                    anomalies.append(row)
                
                processed_count += 1
                
            except Exception as e:
                error_count += 1
                logger.warning(f"Error processing row {index}: {str(e)}")
                continue
        
        # Convert anomalies list to DataFrame
        anomalies_df = pd.DataFrame(anomalies) if anomalies else pd.DataFrame(columns=required_columns)
        
        logger.info(f"Metric anomaly detection completed: {len(anomalies_df)} anomalies found from {processed_count} processed records")
        
        if error_count > 0:
            logger.warning(f"Encountered {error_count} errors during processing")
        
        return anomalies_df
        
    except Exception as e:
        error_msg = f"Unexpected error during metric anomaly detection: {str(e)}"
        logger.error(error_msg)
        raise


def log_warn(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract warning-level log entries from log data.
    
    This function filters log entries to find those with WARNING level
    and returns them as a DataFrame for further analysis.
    
    Args:
        df: DataFrame containing log data with columns:
            - timestamp: Timestamp of the log entry
            - level: Log level (INFO, WARN, ERROR, etc.)
            - message: Log message content
            - service: Service name
            
    Returns:
        pd.DataFrame: DataFrame containing only WARNING level log entries
        
    Raises:
        ValueError: If input DataFrame is empty or missing required columns
        TypeError: If input is not a pandas DataFrame
    """
    logger.info("Starting warning log analysis")
    
    # Validate input
    if not isinstance(df, pd.DataFrame):
        error_msg = "Input must be a pandas DataFrame"
        logger.error(error_msg)
        raise TypeError(error_msg)
    
    if df.empty:
        logger.warning("Input DataFrame is empty - no warnings to extract")
        return pd.DataFrame(columns=['timestamp', 'level', 'message', 'service'])
    
    # Validate required columns
    required_columns = ['timestamp', 'level', 'message', 'service']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        error_msg = f"Missing required columns: {missing_columns}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"Analyzing {len(df)} log records for warnings")
    
    try:
        # Filter for WARNING level logs (case-insensitive)
        warn_logs = df[df['level'].str.contains('WARN', case=False, na=False)]
        
        logger.info(f"Found {len(warn_logs)} warning-level log entries")
        
        # Return a copy to avoid modifying the original DataFrame
        return warn_logs.copy()
        
    except Exception as e:
        error_msg = f"Error during warning log analysis: {str(e)}"
        logger.error(error_msg)
        raise


def get_anomaly_summary(anomalies_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate a summary of detected anomalies for reporting.
    
    Args:
        anomalies_df: DataFrame containing anomaly records
        
    Returns:
        Dict containing summary statistics about the anomalies
    """
    if anomalies_df.empty:
        return {
            'total_anomalies': 0,
            'services_affected': [],
            'metrics_affected': [],
            'anomaly_by_service': {},
            'anomaly_by_metric': {}
        }
    
    try:
        summary = {
            'total_anomalies': len(anomalies_df),
            'services_affected': anomalies_df['service'].unique().tolist(),
            'metrics_affected': anomalies_df['metric_name'].unique().tolist(),
            'anomaly_by_service': anomalies_df['service'].value_counts().to_dict(),
            'anomaly_by_metric': anomalies_df['metric_name'].value_counts().to_dict()
        }
        
        logger.info(f"Anomaly summary: {summary['total_anomalies']} total anomalies across {len(summary['services_affected'])} services")
        return summary
        
    except Exception as e:
        logger.error(f"Error generating anomaly summary: {str(e)}")
        return {'error': str(e)}
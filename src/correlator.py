"""
War_RoomAI Correlator Module

This module handles correlation between metric anomalies and log errors
that occur within a specified time window. It identifies potential
relationships between system metrics and log events for root cause analysis.

Author: War_RoomAI Team
Version: 1.0.0
"""

import pandas as pd
import logging
from typing import List, Dict, Any, Optional
from config import correlation_window

# Configure logging for this module
logger = logging.getLogger(__name__)


def correlate(metric_anomalies: pd.DataFrame, log_anomalies: pd.DataFrame) -> pd.DataFrame:
    """
    Correlate metric anomalies with log errors that occur within the correlation window.
    
    This function finds metric anomalies and log errors that occur within
    the configured time window (default 5 seconds) and creates correlation
    records linking them together.
    
    Args:
        metric_anomalies: DataFrame containing metric anomaly records with columns:
            - time_stamp: Timestamp of the metric anomaly
            - service: Service name
            - metric_name: Name of the metric
            - value: Metric value
        log_anomalies: DataFrame containing log error records with columns:
            - timestamp: Timestamp of the log entry
            - level: Log level
            - message: Log message
            - service: Service name
            
    Returns:
        pd.DataFrame: DataFrame containing correlated events with columns:
            - timestamp: Timestamp of the correlation
            - metric_service: Service name from metric anomaly
            - metric_name: Name of the metric
            - metric_value: Value of the metric
            - log_service: Service name from log error
            - log_message: Log message content
            
    Raises:
        ValueError: If input DataFrames are invalid or missing required columns
        TypeError: If inputs are not pandas DataFrames
    """
    logger.info("Starting correlation analysis between metric anomalies and log errors")
    
    # Validate inputs
    if not isinstance(metric_anomalies, pd.DataFrame):
        error_msg = "metric_anomalies must be a pandas DataFrame"
        logger.error(error_msg)
        raise TypeError(error_msg)
    
    if not isinstance(log_anomalies, pd.DataFrame):
        error_msg = "log_anomalies must be a pandas DataFrame"
        logger.error(error_msg)
        raise TypeError(error_msg)
    
    # Handle empty DataFrames
    if metric_anomalies.empty:
        logger.warning("No metric anomalies provided - no correlations possible")
        return pd.DataFrame(columns=['timestamp', 'metric_service', 'metric_name', 'metric_value', 'log_service', 'log_message'])
    
    if log_anomalies.empty:
        logger.warning("No log anomalies provided - no correlations possible")
        return pd.DataFrame(columns=['timestamp', 'metric_service', 'metric_name', 'metric_value', 'log_service', 'log_message'])
    
    # Validate required columns for metric anomalies
    metric_required_columns = ['time_stamp', 'service', 'metric_name', 'value']
    metric_missing_columns = [col for col in metric_required_columns if col not in metric_anomalies.columns]
    if metric_missing_columns:
        error_msg = f"metric_anomalies missing required columns: {metric_missing_columns}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Validate required columns for log anomalies
    log_required_columns = ['timestamp', 'service', 'message']
    log_missing_columns = [col for col in log_required_columns if col not in log_anomalies.columns]
    if log_missing_columns:
        error_msg = f"log_anomalies missing required columns: {log_missing_columns}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"Correlating {len(metric_anomalies)} metric anomalies with {len(log_anomalies)} log errors")
    logger.info(f"Using correlation window of {correlation_window} seconds")
    
    correlated = []
    processed_pairs = 0
    error_count = 0
    
    try:
        for m_index, m_row in metric_anomalies.iterrows():
            try:
                # Extract metric anomaly data
                metric_timestamp = m_row['time_stamp']
                metric_service = m_row['service']
                metric_name = m_row['metric_name']
                metric_value = m_row['value']
                
                # Skip if timestamp is null/NaN
                if pd.isna(metric_timestamp):
                    logger.debug(f"Skipping metric anomaly at row {m_index}: invalid timestamp")
                    continue
                
                for l_index, l_row in log_anomalies.iterrows():
                    try:
                        # Extract log error data
                        log_timestamp = l_row['timestamp']
                        log_service = l_row['service']
                        log_message = l_row['message']
                        
                        # Skip if timestamp is null/NaN
                        if pd.isna(log_timestamp):
                            logger.debug(f"Skipping log error at row {l_index}: invalid timestamp")
                            continue
                        
                        # Calculate time difference in seconds
                        time_diff = abs((metric_timestamp - log_timestamp).total_seconds())
                        
                        # Check if events occur within correlation window
                        if time_diff <= correlation_window:
                            correlation_record = {
                                'timestamp': metric_timestamp,  # Use metric timestamp as reference
                                'metric_service': metric_service,
                                'metric_name': metric_name,
                                'metric_value': metric_value,
                                'log_service': log_service,
                                'log_message': log_message,
                                'time_diff_seconds': time_diff
                            }
                            correlated.append(correlation_record)
                            
                            logger.debug(f"Correlation found: {metric_service}.{metric_name} ({metric_value}) "
                                        f"and {log_service} log error within {time_diff:.2f}s")
                        
                        processed_pairs += 1
                        
                    except Exception as e:
                        error_count += 1
                        logger.warning(f"Error processing log anomaly at row {l_index}: {str(e)}")
                        continue
                        
            except Exception as e:
                error_count += 1
                logger.warning(f"Error processing metric anomaly at row {m_index}: {str(e)}")
                continue
        
        # Convert correlations to DataFrame
        correlated_df = pd.DataFrame(correlated) if correlated else pd.DataFrame(columns=['timestamp', 'metric_service', 'metric_name', 'metric_value', 'log_service', 'log_message'])
        
        logger.info(f"Correlation analysis completed: {len(correlated_df)} correlations found from {processed_pairs} event pairs")
        
        if error_count > 0:
            logger.warning(f"Encountered {error_count} errors during correlation processing")
        
        return correlated_df
        
    except Exception as e:
        error_msg = f"Unexpected error during correlation analysis: {str(e)}"
        logger.error(error_msg)
        raise


def get_correlation_summary(correlated_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate a summary of correlation results for reporting.
    
    Args:
        correlated_df: DataFrame containing correlation records
        
    Returns:
        Dict containing summary statistics about the correlations
    """
    if correlated_df.empty:
        return {
            'total_correlations': 0,
            'services_involved': [],
            'metrics_involved': [],
            'correlations_by_service': {},
            'correlations_by_metric': {},
            'avg_time_diff': 0.0
        }
    
    try:
        summary = {
            'total_correlations': len(correlated_df),
            'services_involved': list(set(correlated_df['metric_service'].tolist() + correlated_df['log_service'].tolist())),
            'metrics_involved': correlated_df['metric_name'].unique().tolist(),
            'correlations_by_service': correlated_df['metric_service'].value_counts().to_dict(),
            'correlations_by_metric': correlated_df['metric_name'].value_counts().to_dict(),
            'avg_time_diff': correlated_df['time_diff_seconds'].mean() if 'time_diff_seconds' in correlated_df.columns else 0.0
        }
        
        logger.info(f"Correlation summary: {summary['total_correlations']} correlations across {len(summary['services_involved'])} services")
        return summary
        
    except Exception as e:
        logger.error(f"Error generating correlation summary: {str(e)}")
        return {'error': str(e)}


def filter_correlations_by_service(correlated_df: pd.DataFrame, service_name: str) -> pd.DataFrame:
    """
    Filter correlations to only include those involving a specific service.
    
    Args:
        correlated_df: DataFrame containing correlation records
        service_name: Name of the service to filter by
        
    Returns:
        pd.DataFrame: Filtered correlations involving the specified service
    """
    if correlated_df.empty:
        return correlated_df
    
    try:
        # Filter for correlations where either metric_service or log_service matches
        filtered = correlated_df[
            (correlated_df['metric_service'] == service_name) | 
            (correlated_df['log_service'] == service_name)
        ]
        
        logger.info(f"Filtered correlations for service '{service_name}': {len(filtered)} matches")
        return filtered
        
    except Exception as e:
        logger.error(f"Error filtering correlations by service '{service_name}': {str(e)}")
        return pd.DataFrame(columns=correlated_df.columns)
"""
War_RoomAI Main Module

This module serves as the entry point for the War_RoomAI incident detection and 
root cause analysis system. It orchestrates the entire analysis pipeline from 
data loading through anomaly detection to root cause analysis.

Author: War_RoomAI Team
Version: 1.0.0
"""

import logging
import os
import sys
from typing import Optional
import pandas as pd

from data_loader import load_metrics, load_logs
from anomaly_detector import metric_anomaly, log_warn
from correlator import correlate
from root_cause import analyze_root_cause


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(__file__), "../logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.FileHandler(os.path.join(log_dir, 'war_roomai.log')),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Logging initialized successfully")


def main() -> None:
    """
    Main entry point for War_RoomAI analysis pipeline.
    
    Orchestrates the complete incident detection workflow:
    1. Load metrics and log data
    2. Detect anomalies and warnings
    3. Correlate metric anomalies with log errors
    4. Perform root cause analysis
    
    Raises:
        SystemExit: If critical errors occur during processing
    """
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting War_RoomAI analysis pipeline")
        
        # Define data directory path
        DATA_DIR = os.path.join(os.path.dirname(__file__), "../data")
        
        # Validate data directory exists
        if not os.path.exists(DATA_DIR):
            logger.error(f"Data directory not found: {DATA_DIR}")
            raise FileNotFoundError(f"Data directory not found: {DATA_DIR}")
        
        logger.info(f"Loading data from directory: {DATA_DIR}")
        
        # Load metrics data
        try:
            metrics_file = os.path.join(DATA_DIR, "metrics.csv")
            metrics = load_metrics(metrics_file)
            logger.info(f"Successfully loaded {len(metrics)} metric records")
        except Exception as e:
            logger.error(f"Failed to load metrics: {str(e)}")
            raise
        
        # Load log data
        try:
            logs = load_logs(DATA_DIR)
            logger.info(f"Successfully loaded {len(logs)} log records")
        except Exception as e:
            logger.error(f"Failed to load logs: {str(e)}")
            raise
        
        # Extract error-level log anomalies
        try:
            log_anomalies = logs[logs['level'].str.contains('ERROR', case=False, na=False)]
            logger.info(f"Found {len(log_anomalies)} error-level log entries")
        except Exception as e:
            logger.error(f"Failed to filter error logs: {str(e)}")
            raise
        
        # Display warnings
        logger.info("Analyzing warning logs...")
        try:
            warnings_df = log_warn(pd.DataFrame(logs))
            if not warnings_df.empty:
                logger.warning(f"Found {len(warnings_df)} warning entries")
                print("------------------WARNINGS--------------------")
                print(warnings_df)
            else:
                logger.info("No warnings found")
        except Exception as e:
            logger.error(f"Failed to analyze warnings: {str(e)}")
            # Continue processing even if warning analysis fails
        
        # Detect metric anomalies
        logger.info("Detecting metric anomalies...")
        try:
            metric_anomalies = metric_anomaly(metrics)
            if not metric_anomalies.empty:
                logger.warning(f"Found {len(metric_anomalies)} metric anomalies")
                print("------------------METRIC ANOMALIES--------------------------")
                print(metric_anomalies)
            else:
                logger.info("No metric anomalies detected")
        except Exception as e:
            logger.error(f"Failed to detect metric anomalies: {str(e)}")
            raise
        
        # Display log anomalies
        if not log_anomalies.empty:
            print("--------------------------------------------------------")
            print(log_anomalies)
        
        # Correlate anomalies
        logger.info("Correlating metric anomalies with log errors...")
        try:
            correlated = correlate(metric_anomalies, log_anomalies)
            if not correlated.empty:
                logger.info(f"Found {len(correlated)} correlated events")
            else:
                logger.info("No correlations found between metrics and logs")
        except Exception as e:
            logger.error(f"Failed to correlate anomalies: {str(e)}")
            raise
        
        # Perform root cause analysis
        logger.info("Performing root cause analysis...")
        try:
            analyze_root_cause(correlated)
        except Exception as e:
            logger.error(f"Failed to perform root cause analysis: {str(e)}")
            raise
        
        logger.info("War_RoomAI analysis pipeline completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error in main pipeline: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

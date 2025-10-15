"""
War_RoomAI Configuration Module

This module contains all configuration parameters for the War_RoomAI system,
including threshold values for anomaly detection, correlation settings,
and service-specific recommendations.

Author: War_RoomAI Team
Version: 1.0.0
"""

from typing import Dict, Any, Union
import os
import logging

# Configure logging for this module
logger = logging.getLogger(__name__)

# Threshold values for anomaly detection
# CPU percentage threshold - alerts when CPU usage exceeds this value
thresholds = {
    'cpu_pct': 85,  # CPU percentage threshold
    'latency_ms': {  # Latency thresholds per service (in milliseconds)
        'frontend': 350,
        'api': 350,
        'database': 200
    }
}

# Correlation window in seconds - how close in time metric anomalies and log errors must be
correlation_window = 5

# Base date for log timestamp reconstruction
BASE_DATE = "2025-10-12"

# API configuration for recommendations
API_CONFIG = {
    'base_url': 'http://localhost:5000',  # Mock server for testing
    'recommendations_endpoint': '/api/v1/recommendations',
    'timeout': 3,  # seconds (reduced for faster demo)
    'retry_attempts': 0,  # fast-fail to LLM for demo
    'retry_delay': 1,  # seconds
    'fallback_enabled': True  # Use local recommendations if API fails
}

# API headers and authentication (if needed)
API_HEADERS = {
    'Content-Type': 'application/json',
    'User-Agent': 'War_RoomAI/1.0.0'
}

# API authentication (uncomment and configure if needed)
# API_AUTH = {
#     'api_key': 'your-api-key-here',
#     'auth_type': 'bearer'  # or 'api_key'
# }

# Service-specific recommendations for root cause analysis (fallback)
recommendations = {
    'api': "Check API latency and backend dependencies. Possible timeout or overload.",
    'database': "Database CPU or query latency spikes — consider indexing or connection pooling.",
    'frontend': "Frontend response time high — check for slow API calls or JavaScript rendering bottlenecks."
}

# LLM (OpenAI) configuration for dynamic recommendations (WOW factor)
LLM_CONFIG: Dict[str, Any] = {
    'enabled': os.environ.get('LLM_ENABLED', 'true').lower() in ('1', 'true', 'yes'),
    'provider': os.environ.get('LLM_PROVIDER', 'openai'),
    'api_key': os.environ.get('OPENAI_API_KEY', ''),
    'api_base': os.environ.get('OPENAI_API_BASE', 'https://api.openai.com'),
    'model': os.environ.get('OPENAI_MODEL', 'gpt-4o-mini'),
    'timeout': float(os.environ.get('LLM_TIMEOUT', '12')),  # seconds
    'max_tokens': int(os.environ.get('LLM_MAX_TOKENS', '300')),
    'llm_only': os.environ.get('LLM_ONLY', 'false').lower() in ('1', 'true', 'yes'),
}


def validate_config() -> bool:
    """
    Validate configuration parameters for correctness and completeness.
    
    Returns:
        bool: True if configuration is valid, False otherwise
        
    Raises:
        ValueError: If configuration contains invalid values
    """
    logger.info("Validating configuration parameters...")
    
    try:
        # Validate CPU threshold
        if not isinstance(thresholds['cpu_pct'], (int, float)) or thresholds['cpu_pct'] <= 0 or thresholds['cpu_pct'] > 100:
            raise ValueError(f"Invalid CPU threshold: {thresholds['cpu_pct']}. Must be between 0 and 100.")
        
        # Validate latency thresholds
        if not isinstance(thresholds['latency_ms'], dict):
            raise ValueError("Latency thresholds must be a dictionary")
        
        for service, threshold in thresholds['latency_ms'].items():
            if not isinstance(threshold, (int, float)) or threshold <= 0:
                raise ValueError(f"Invalid latency threshold for {service}: {threshold}. Must be positive number.")
        
        # Validate correlation window
        if not isinstance(correlation_window, (int, float)) or correlation_window <= 0:
            raise ValueError(f"Invalid correlation window: {correlation_window}. Must be positive number.")
        
        # Validate base date format
        from datetime import datetime
        try:
            datetime.strptime(BASE_DATE, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid base date format: {BASE_DATE}. Expected YYYY-MM-DD format.")
        
        # Validate recommendations
        if not isinstance(recommendations, dict):
            raise ValueError("Recommendations must be a dictionary")
        
        for service, recommendation in recommendations.items():
            if not isinstance(recommendation, str) or not recommendation.strip():
                raise ValueError(f"Invalid recommendation for {service}: must be non-empty string")
        
        # Validate API configuration
        if not isinstance(API_CONFIG, dict):
            raise ValueError("API_CONFIG must be a dictionary")
        
        required_api_keys = ['base_url', 'recommendations_endpoint', 'timeout', 'retry_attempts', 'retry_delay', 'fallback_enabled']
        for key in required_api_keys:
            if key not in API_CONFIG:
                raise ValueError(f"API_CONFIG missing required key: {key}")
        
        if not isinstance(API_CONFIG['timeout'], (int, float)) or API_CONFIG['timeout'] <= 0:
            raise ValueError(f"Invalid API timeout: {API_CONFIG['timeout']}. Must be positive number.")
        
        if not isinstance(API_CONFIG['retry_attempts'], int) or API_CONFIG['retry_attempts'] < 0:
            raise ValueError(f"Invalid retry attempts: {API_CONFIG['retry_attempts']}. Must be non-negative integer.")
        
        if not isinstance(API_CONFIG['fallback_enabled'], bool):
            raise ValueError(f"Invalid fallback_enabled: {API_CONFIG['fallback_enabled']}. Must be boolean.")
        
        logger.info("Configuration validation successful")
        return True
        
    except Exception as e:
        logger.error(f"Configuration validation failed: {str(e)}")
        raise


def get_threshold(metric_name: str, service: str = None) -> Union[int, float, None]:
    """
    Get threshold value for a specific metric and service.
    
    Args:
        metric_name: Name of the metric (e.g., 'cpu_pct', 'latency_ms')
        service: Service name (required for latency_ms metric)
        
    Returns:
        Threshold value or None if not found
        
    Raises:
        ValueError: If metric_name is invalid or service is required but not provided
    """
    if metric_name not in thresholds:
        logger.warning(f"Unknown metric: {metric_name}")
        return None
    
    threshold = thresholds[metric_name]
    
    if isinstance(threshold, dict):
        if service is None:
            raise ValueError(f"Service name required for metric '{metric_name}'")
        return threshold.get(service)
    else:
        return threshold


def get_recommendation(service: str) -> str:
    """
    Get recommendation for a specific service.
    
    Args:
        service: Service name
        
    Returns:
        Recommendation string or default message if service not found
    """
    return recommendations.get(service, "No predefined recommendation available for this service.")


# Validate configuration on module import
try:
    validate_config()
except Exception as e:
    logger.error(f"Configuration validation failed on import: {str(e)}")
    raise
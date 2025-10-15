"""
War_RoomAI API Service Module

This module handles API communication for fetching recommendations and other
external data sources. It includes retry logic, error handling, and fallback
mechanisms for robust operation.

Author: War_RoomAI Team
Version: 1.0.0
"""

import requests
import logging
import time
from typing import Dict, Any, Optional, List
from config import API_CONFIG, API_HEADERS, LLM_CONFIG

# Configure logging for this module
logger = logging.getLogger(__name__)


class APIError(Exception):
    """Custom exception for API-related errors."""
    pass


class RecommendationsAPI:
    """
    API client for fetching service recommendations.
    
    This class handles communication with the recommendations API,
    including retry logic, error handling, and fallback mechanisms.
    """
    
    def __init__(self):
        """Initialize the API client with configuration."""
        self.base_url = API_CONFIG['base_url']
        self.endpoint = API_CONFIG['recommendations_endpoint']
        self.timeout = API_CONFIG['timeout']
        self.retry_attempts = API_CONFIG['retry_attempts']
        self.retry_delay = API_CONFIG['retry_delay']
        self.fallback_enabled = API_CONFIG['fallback_enabled']
        self.headers = API_HEADERS.copy()
        
        # Add authentication headers if configured
        # if API_AUTH:
        #     if API_AUTH['auth_type'] == 'bearer':
        #         self.headers['Authorization'] = f"Bearer {API_AUTH['api_key']}"
        #     elif API_AUTH['auth_type'] == 'api_key':
        #         self.headers['X-API-Key'] = API_AUTH['api_key']
        
        logger.info(f"Initialized RecommendationsAPI with base URL: {self.base_url}")
    
    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Make HTTP request with retry logic and error handling.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL for the request
            **kwargs: Additional arguments for requests
            
        Returns:
            requests.Response: Response object
            
        Raises:
            APIError: If all retry attempts fail
        """
        last_exception = None
        
        for attempt in range(self.retry_attempts + 1):
            try:
                logger.debug(f"Making {method} request to {url} (attempt {attempt + 1}/{self.retry_attempts + 1})")
                
                response = requests.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    timeout=self.timeout,
                    **kwargs
                )
                
                # Check for HTTP errors
                response.raise_for_status()
                
                logger.debug(f"Request successful: {response.status_code}")
                return response
                
            except requests.exceptions.Timeout as e:
                last_exception = e
                logger.warning(f"Request timeout on attempt {attempt + 1}: {str(e)}")
                
            except requests.exceptions.ConnectionError as e:
                last_exception = e
                logger.warning(f"Connection error on attempt {attempt + 1}: {str(e)}")
                
            except requests.exceptions.HTTPError as e:
                last_exception = e
                logger.warning(f"HTTP error on attempt {attempt + 1}: {str(e)}")
                
            except requests.exceptions.RequestException as e:
                last_exception = e
                logger.warning(f"Request error on attempt {attempt + 1}: {str(e)}")
                
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error on attempt {attempt + 1}: {str(e)}")
            
            # Wait before retry (except on last attempt)
            if attempt < self.retry_attempts:
                logger.info(f"Retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)
        
        # All retries failed
        error_msg = f"All {self.retry_attempts + 1} attempts failed. Last error: {str(last_exception)}"
        logger.error(error_msg)
        raise APIError(error_msg)
    
    def get_recommendations(self, service: str, anomaly_count: int, 
                          metric_name: str = None, metric_value: float = None) -> Optional[str]:
        """
        Fetch recommendation for a specific service from the API.
        
        Args:
            service: Service name (e.g., 'api', 'database', 'frontend')
            anomaly_count: Number of anomalies detected for this service
            metric_name: Name of the metric that triggered the anomaly
            metric_value: Value of the metric that exceeded threshold
            
        Returns:
            str: Recommendation text from API, or None if API call fails
            
        Raises:
            APIError: If API call fails and fallback is disabled
        """
        try:
            # Prepare request data
            request_data = {
                'service': service,
                'anomaly_count': anomaly_count,
                'timestamp': time.time()
            }
            
            if metric_name:
                request_data['metric_name'] = metric_name
            if metric_value is not None:
                request_data['metric_value'] = metric_value
            
            # Construct full URL
            url = f"{self.base_url}{self.endpoint}"
            
            logger.info(f"Fetching recommendation for service '{service}' with {anomaly_count} anomalies")
            
            # Make API request
            response = self._make_request('POST', url, json=request_data)
            
            # Parse response
            try:
                response_data = response.json()
                
                if 'recommendation' in response_data:
                    recommendation = response_data['recommendation']
                    logger.info(f"Successfully fetched recommendation for {service}: {recommendation[:100]}...")
                    return recommendation
                else:
                    logger.warning(f"API response missing 'recommendation' field: {response_data}")
                    return None
                    
            except ValueError as e:
                logger.error(f"Failed to parse JSON response: {str(e)}")
                return None
                
        except APIError as e:
            logger.error(f"API call failed for service '{service}': {str(e)}")
            
            if not self.fallback_enabled:
                raise
            
            logger.info("Fallback enabled - will use local recommendations")
            return None


class LLMProvider:
    """
    Lightweight LLM client (OpenAI-compatible) for dynamic recommendations.
    Uses environment-configured settings in LLM_CONFIG. Gracefully no-ops if
    not configured or disabled.
    """

    def __init__(self) -> None:
        self.enabled: bool = bool(LLM_CONFIG.get('enabled'))
        self.api_key: str = str(LLM_CONFIG.get('api_key') or '')
        self.api_base: str = str(LLM_CONFIG.get('api_base') or 'https://api.openai.com')
        self.model: str = str(LLM_CONFIG.get('model') or 'gpt-4o-mini')
        self.timeout: float = float(LLM_CONFIG.get('timeout') or 12)
        self.max_tokens: int = int(LLM_CONFIG.get('max_tokens') or 300)

        if not self.enabled or not self.api_key:
            logger.info("LLM provider disabled or missing API key; skipping LLM recommendations")

    def recommend(self, context: Dict[str, Any]) -> Optional[str]:
        """
        Generate a recommendation using the LLM with provided context.
        Returns None if disabled/misconfigured or on any request error.
        """
        if not self.enabled or not self.api_key:
            return None

        try:
            import requests

            url = f"{self.api_base}/v1/chat/completions"
            headers = {
                'Authorization': f"Bearer {self.api_key}",
                'Content-Type': 'application/json'
            }
            system_prompt = (
                "You are an expert SRE assistant. Given service anomalies, logs, and metrics, "
                "produce one concise, actionable remediation recommendation (1-2 sentences). "
                "Avoid generic advice; be specific based on context."
            )
            user_prompt = (
                f"Service: {context.get('service')}\n"
                f"Anomaly count: {context.get('anomaly_count')}\n"
                f"Metric name: {context.get('metric_name')}\n"
                f"Metric value: {context.get('metric_value')}\n"
                f"Recent log message: {context.get('log_message') or 'N/A'}\n"
                f"Correlations: {context.get('correlations') or []}"
            )

            payload = {
                'model': self.model,
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                'temperature': 0.2,
                'max_tokens': self.max_tokens
            }

            resp = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            content = (
                data.get('choices', [{}])[0]
                    .get('message', {})
                    .get('content')
            )
            if not content:
                logger.warning("LLM response missing content")
                return None
            return content.strip()
        except Exception as e:
            logger.warning(f"LLM recommendation failed: {str(e)}")
            return None
    
    def get_bulk_recommendations(self, services_data: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Fetch recommendations for multiple services in a single API call.
        
        Args:
            services_data: List of dictionaries containing service information
            
        Returns:
            Dict mapping service names to recommendations
        """
        try:
            url = f"{self.base_url}{self.endpoint}/bulk"
            
            logger.info(f"Fetching bulk recommendations for {len(services_data)} services")
            
            response = self._make_request('POST', url, json={'services': services_data})
            
            try:
                response_data = response.json()
                
                if 'recommendations' in response_data:
                    recommendations = response_data['recommendations']
                    logger.info(f"Successfully fetched {len(recommendations)} bulk recommendations")
                    return recommendations
                else:
                    logger.warning(f"API response missing 'recommendations' field: {response_data}")
                    return {}
                    
            except ValueError as e:
                logger.error(f"Failed to parse JSON response: {str(e)}")
                return {}
                
        except APIError as e:
            logger.error(f"Bulk API call failed: {str(e)}")
            
            if not self.fallback_enabled:
                raise
            
            logger.info("Fallback enabled - will use local recommendations")
            return {}
    
    def health_check(self) -> bool:
        """
        Check if the API is available and responding.
        
        Returns:
            bool: True if API is healthy, False otherwise
        """
        try:
            url = f"{self.base_url}/health"
            response = self._make_request('GET', url)
            
            if response.status_code == 200:
                logger.info("API health check passed")
                return True
            else:
                logger.warning(f"API health check failed with status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.warning(f"API health check failed: {str(e)}")
            return False


def get_recommendation_with_fallback(service: str, anomaly_count: int, 
                                   metric_name: str = None, metric_value: float = None) -> str:
    """
    Get recommendation for a service, trying API first and falling back to local config.
    
    Args:
        service: Service name
        anomaly_count: Number of anomalies
        metric_name: Metric name (optional)
        metric_value: Metric value (optional)
        
    Returns:
        str: Recommendation text
    """
    logger.info(f"Getting recommendation for service '{service}'")
    
    # Try API first (unless LLM-only mode)
    if not LLM_CONFIG.get('llm_only'):
        try:
            api_client = RecommendationsAPI()
            api_recommendation = api_client.get_recommendations(
                service=service,
                anomaly_count=anomaly_count,
                metric_name=metric_name,
                metric_value=metric_value
            )
            
            if api_recommendation:
                logger.info(f"Using API recommendation for {service}")
                return api_recommendation
                
        except Exception as e:
            logger.warning(f"API recommendation failed for {service}: {str(e)}")
    
    # Try LLM next (WOW factor)
    try:
        llm = LLMProvider()
        llm_rec = llm.recommend({
            'service': service,
            'anomaly_count': anomaly_count,
            'metric_name': metric_name,
            'metric_value': metric_value,
        })
        if llm_rec:
            logger.info(f"Using LLM recommendation for {service}")
            return llm_rec
    except Exception as e:
        logger.warning(f"LLM recommendation path failed for {service}: {str(e)}")

    # Fallback to local recommendations
    logger.info(f"Using fallback recommendation for {service}")
    from config import get_recommendation
    return get_recommendation(service)


def get_bulk_recommendations_with_fallback(services_data: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Get recommendations for multiple services, trying API first and falling back to local config.
    
    Args:
        services_data: List of service data dictionaries
        
    Returns:
        Dict mapping service names to recommendations
    """
    logger.info(f"Getting bulk recommendations for {len(services_data)} services")
    
    # Try API first (unless LLM-only mode)
    if not LLM_CONFIG.get('llm_only'):
        try:
            api_client = RecommendationsAPI()
            api_recommendations = api_client.get_bulk_recommendations(services_data)
            
            if api_recommendations:
                logger.info(f"Using API bulk recommendations for {len(api_recommendations)} services")
                return api_recommendations
                
        except Exception as e:
            logger.warning(f"API bulk recommendations failed: {str(e)}")
    
    # Try LLM per-service (best effort)
    results: Dict[str, str] = {}
    try:
        llm = LLMProvider()
        for item in services_data:
            service = item.get('service')
            if not service:
                continue
            rec = llm.recommend({
                'service': service,
                'anomaly_count': item.get('anomaly_count'),
                'metric_name': item.get('metric_name'),
                'metric_value': item.get('metric_value'),
            })
            if rec:
                results[service] = rec
        if results:
            logger.info(f"Using LLM recommendations for {len(results)} services")
            return results
    except Exception as e:
        logger.warning(f"Bulk LLM recommendations failed: {str(e)}")

    # Fallback to local recommendations
    logger.info("Using fallback recommendations")
    from config import get_recommendation
    
    fallback_recommendations = {}
    for service_data in services_data:
        service = service_data.get('service')
        if service:
            fallback_recommendations[service] = get_recommendation(service)
    
    return fallback_recommendations


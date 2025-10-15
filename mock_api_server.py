"""
Mock API Server for Testing War_RoomAI Recommendations

This is a simple Flask-based mock API server for testing the recommendations
API integration. It simulates various scenarios including success, errors,
and timeouts.

Usage:
    python mock_api_server.py

Author: War_RoomAI Team
Version: 1.0.0
"""

from flask import Flask, request, jsonify
import random
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Mock recommendations database
MOCK_RECOMMENDATIONS = {
    'api': [
        "Check API latency and backend dependencies. Possible timeout or overload.",
        "Investigate API gateway configuration and load balancer settings.",
        "Review API rate limiting and throttling policies.",
        "Check for database connection pool exhaustion affecting API performance."
    ],
    'database': [
        "Database CPU or query latency spikes — consider indexing or connection pooling.",
        "Review slow query logs and optimize database performance.",
        "Check database connection limits and consider scaling.",
        "Investigate potential deadlocks or long-running transactions."
    ],
    'frontend': [
        "Frontend response time high — check for slow API calls or JavaScript rendering bottlenecks.",
        "Review frontend bundle size and optimize asset loading.",
        "Check for memory leaks in JavaScript applications.",
        "Investigate CDN performance and caching strategies."
    ]
}

# Simulate API behavior modes
API_MODE = 'normal'  # 'normal', 'slow', 'error', 'timeout'


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'timestamp': time.time()})


@app.route('/api/v1/recommendations', methods=['POST'])
def get_recommendation():
    """Get recommendation for a single service."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        service = data.get('service')
        anomaly_count = data.get('anomaly_count', 0)
        metric_name = data.get('metric_name')
        metric_value = data.get('metric_value')
        
        logger.info(f"Received recommendation request for service: {service}, anomalies: {anomaly_count}")
        
        # Simulate different API behaviors
        if API_MODE == 'slow':
            time.sleep(2)  # Simulate slow response
        elif API_MODE == 'timeout':
            time.sleep(15)  # Simulate timeout
        elif API_MODE == 'error':
            return jsonify({'error': 'Internal server error'}), 500
        
        if not service:
            return jsonify({'error': 'Service name is required'}), 400
        
        # Get recommendation based on service and anomaly count
        if service in MOCK_RECOMMENDATIONS:
            recommendations = MOCK_RECOMMENDATIONS[service]
            
            # Select recommendation based on anomaly count
            if anomaly_count >= 10:
                recommendation = recommendations[0]  # High severity
            elif anomaly_count >= 5:
                recommendation = recommendations[1]  # Medium severity
            elif anomaly_count >= 2:
                recommendation = recommendations[2]  # Low severity
            else:
                recommendation = recommendations[3]  # Very low severity
            
            # Add contextual information
            if metric_name and metric_value:
                recommendation += f" (Detected {metric_name}: {metric_value})"
            
            return jsonify({
                'recommendation': recommendation,
                'service': service,
                'anomaly_count': anomaly_count,
                'severity': 'high' if anomaly_count >= 10 else 'medium' if anomaly_count >= 5 else 'low'
            })
        else:
            return jsonify({'error': f'Unknown service: {service}'}), 404
            
    except Exception as e:
        logger.error(f"Error processing recommendation request: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/v1/recommendations/bulk', methods=['POST'])
def get_bulk_recommendations():
    """Get recommendations for multiple services."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        services = data.get('services', [])
        
        if not services:
            return jsonify({'error': 'Services list is required'}), 400
        
        logger.info(f"Received bulk recommendation request for {len(services)} services")
        
        # Simulate different API behaviors
        if API_MODE == 'slow':
            time.sleep(3)  # Simulate slow response
        elif API_MODE == 'timeout':
            time.sleep(15)  # Simulate timeout
        elif API_MODE == 'error':
            return jsonify({'error': 'Internal server error'}), 500
        
        recommendations = {}
        
        for service_data in services:
            service = service_data.get('service')
            anomaly_count = service_data.get('anomaly_count', 0)
            metric_name = service_data.get('metric_name')
            metric_value = service_data.get('metric_value')
            
            if service in MOCK_RECOMMENDATIONS:
                service_recommendations = MOCK_RECOMMENDATIONS[service]
                
                # Select recommendation based on anomaly count
                if anomaly_count >= 10:
                    recommendation = service_recommendations[0]
                elif anomaly_count >= 5:
                    recommendation = service_recommendations[1]
                elif anomaly_count >= 2:
                    recommendation = service_recommendations[2]
                else:
                    recommendation = service_recommendations[3]
                
                # Add contextual information
                if metric_name and metric_value:
                    recommendation += f" (Detected {metric_name}: {metric_value})"
                
                recommendations[service] = recommendation
        
        return jsonify({
            'recommendations': recommendations,
            'total_services': len(services),
            'processed_services': len(recommendations)
        })
        
    except Exception as e:
        logger.error(f"Error processing bulk recommendation request: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/mode', methods=['POST'])
def set_api_mode():
    """Set API behavior mode for testing."""
    global API_MODE
    
    data = request.get_json()
    mode = data.get('mode', 'normal')
    
    if mode in ['normal', 'slow', 'error', 'timeout']:
        API_MODE = mode
        logger.info(f"API mode set to: {mode}")
        return jsonify({'mode': API_MODE, 'message': f'API mode set to {mode}'})
    else:
        return jsonify({'error': 'Invalid mode. Use: normal, slow, error, timeout'}), 400


@app.route('/api/mode', methods=['GET'])
def get_api_mode():
    """Get current API behavior mode."""
    return jsonify({'mode': API_MODE})


if __name__ == '__main__':
    print("Starting Mock API Server for War_RoomAI Testing")
    print("Available endpoints:")
    print("  GET  /health - Health check")
    print("  POST /api/v1/recommendations - Single service recommendation")
    print("  POST /api/v1/recommendations/bulk - Bulk recommendations")
    print("  POST /api/mode - Set API behavior mode")
    print("  GET  /api/mode - Get current API mode")
    print("\nAPI Modes:")
    print("  normal - Normal operation")
    print("  slow - Simulate slow responses")
    print("  error - Return server errors")
    print("  timeout - Simulate timeouts")
    print("\nStarting server on http://localhost:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=True)


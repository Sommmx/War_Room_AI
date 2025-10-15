"""
War_RoomAI Root Cause Analysis Module

This module performs root cause analysis on correlated metric anomalies and log errors.
It identifies the most problematic services and provides actionable recommendations
for incident resolution.

Author: War_RoomAI Team
Version: 1.0.0
"""

import pandas as pd
import logging
from typing import Dict, Any, List, Optional
from config import recommendations, get_recommendation
from api_service import get_recommendation_with_fallback, get_bulk_recommendations_with_fallback

# Configure logging for this module
logger = logging.getLogger(__name__)


def analyze_root_cause(correlated_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform root cause analysis on correlated metric anomalies and log errors.
    
    This function analyzes the correlation data to identify which services
    are most affected by anomalies and provides targeted recommendations
    for each service based on the type and frequency of issues.
    
    Args:
        correlated_df: DataFrame containing correlation records with columns:
            - timestamp: Timestamp of the correlation
            - metric_service: Service name from metric anomaly
            - metric_name: Name of the metric
            - metric_value: Value of the metric
            - log_service: Service name from log error
            - log_message: Log message content
            
    Returns:
        Dict containing root cause analysis results:
            - service_rankings: Services ranked by anomaly count
            - recommendations: Service-specific recommendations
            - summary_stats: Summary statistics
            
    Raises:
        ValueError: If input DataFrame is invalid or missing required columns
        TypeError: If input is not a pandas DataFrame
    """
    logger.info("Starting root cause analysis")
    
    # Validate input
    if not isinstance(correlated_df, pd.DataFrame):
        error_msg = "Input must be a pandas DataFrame"
        logger.error(error_msg)
        raise TypeError(error_msg)
    
    # Handle empty DataFrame
    if correlated_df.empty:
        logger.warning("No correlation data provided - no root cause analysis possible")
        print('No correlation found')
        return {
            'service_rankings': pd.DataFrame(columns=['metric_service', 'anomaly_count']),
            'recommendations': {},
            'summary_stats': {
                'total_correlations': 0,
                'services_affected': 0,
                'metrics_involved': 0
            }
        }
    
    # Validate required columns
    required_columns = ['metric_service', 'metric_name', 'log_service', 'log_message']
    missing_columns = [col for col in required_columns if col not in correlated_df.columns]
    if missing_columns:
        error_msg = f"Missing required columns: {missing_columns}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"Analyzing {len(correlated_df)} correlation records for root cause")
    
    try:
        # Group by service and count anomalies
        service_rankings = correlated_df.groupby('metric_service').size().reset_index(name='anomaly_count')
        service_rankings = service_rankings.sort_values(by='anomaly_count', ascending=False)
        
        logger.info(f"Found anomalies in {len(service_rankings)} services")
        
        # Display root cause analysis results
        print('------------ROOT CAUSE ANALYSIS-----------------------')
        print(service_rankings)
        
        # Generate recommendations for each affected service
        service_recommendations = {}
        print("\nRecommendations by Service:")
        
        # Prepare data for bulk API call
        services_data = []
        for _, row in service_rankings.iterrows():
            service = row['metric_service']
            anomaly_count = row['anomaly_count']
            
            # Get metric details for this service
            service_correlations = correlated_df[correlated_df['metric_service'] == service]
            metric_name = service_correlations['metric_name'].iloc[0] if not service_correlations.empty else None
            metric_value = service_correlations['metric_value'].mean() if not service_correlations.empty else None
            
            services_data.append({
                'service': service,
                'anomaly_count': anomaly_count,
                'metric_name': metric_name,
                'metric_value': metric_value
            })
        
        # Fetch recommendations per service (REST → LLM → local)
        for service_data in services_data:
            service = service_data['service']
            anomaly_count = service_data['anomaly_count']
            try:
                recommendation = get_recommendation_with_fallback(
                    service=service,
                    anomaly_count=anomaly_count,
                    metric_name=service_data.get('metric_name'),
                    metric_value=service_data.get('metric_value')
                )
                service_recommendations[service] = {
                    'recommendation': recommendation,
                    'anomaly_count': anomaly_count
                }
                print(f" - {service.capitalize()}: {recommendation}")
                logger.info(f"Generated recommendation for {service}: {anomaly_count} anomalies")
            except Exception as e:
                logger.warning(f"Failed to get recommendation for service '{service}': {str(e)}")
                service_recommendations[service] = {
                    'recommendation': "No predefined recommendation available.",
                    'anomaly_count': anomaly_count
                }
                print(f" - {service.capitalize()}: No predefined recommendation available.")
        
        # Generate summary statistics
        summary_stats = {
            'total_correlations': len(correlated_df),
            'services_affected': len(service_rankings),
            'metrics_involved': len(correlated_df['metric_name'].unique()),
            'most_problematic_service': service_rankings.iloc[0]['metric_service'] if not service_rankings.empty else None,
            'highest_anomaly_count': service_rankings.iloc[0]['anomaly_count'] if not service_rankings.empty else 0
        }
        
        logger.info(f"Root cause analysis completed: {summary_stats['services_affected']} services affected, "
                   f"{summary_stats['total_correlations']} total correlations")
        
        return {
            'service_rankings': service_rankings,
            'recommendations': service_recommendations,
            'summary_stats': summary_stats
        }
        
    except Exception as e:
        error_msg = f"Error during root cause analysis: {str(e)}"
        logger.error(error_msg)
        raise


def get_service_impact_summary(correlated_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate a detailed impact summary for each service.
    
    Args:
        correlated_df: DataFrame containing correlation records
        
    Returns:
        Dict containing detailed impact analysis by service
    """
    if correlated_df.empty:
        return {}
    
    try:
        service_impact = {}
        
        for service in correlated_df['metric_service'].unique():
            service_data = correlated_df[correlated_df['metric_service'] == service]
            
            impact_summary = {
                'total_anomalies': len(service_data),
                'metrics_affected': service_data['metric_name'].unique().tolist(),
                'avg_metric_value': service_data['metric_value'].mean(),
                'max_metric_value': service_data['metric_value'].max(),
                'log_services_involved': service_data['log_service'].unique().tolist(),
                'unique_log_messages': len(service_data['log_message'].unique())
            }
            
            service_impact[service] = impact_summary
            
        logger.info(f"Generated impact summary for {len(service_impact)} services")
        return service_impact
        
    except Exception as e:
        logger.error(f"Error generating service impact summary: {str(e)}")
        return {}


def prioritize_services(service_rankings: pd.DataFrame, impact_threshold: int = 1) -> List[str]:
    """
    Prioritize services based on anomaly count and impact threshold.
    
    Args:
        service_rankings: DataFrame with service rankings
        impact_threshold: Minimum anomaly count to consider a service high priority
        
    Returns:
        List of service names ordered by priority
    """
    if service_rankings.empty:
        return []
    
    try:
        # Filter services above threshold
        high_priority = service_rankings[service_rankings['anomaly_count'] >= impact_threshold]
        
        # Return service names in priority order
        priority_list = high_priority['metric_service'].tolist()
        
        logger.info(f"Identified {len(priority_list)} high-priority services (threshold: {impact_threshold})")
        return priority_list
        
    except Exception as e:
        logger.error(f"Error prioritizing services: {str(e)}")
        return []


def generate_incident_report(correlated_df: pd.DataFrame) -> str:
    """
    Generate a formatted incident report based on root cause analysis.
    
    Args:
        correlated_df: DataFrame containing correlation records
        
    Returns:
        String containing formatted incident report
    """
    if correlated_df.empty:
        return "No incidents detected - system operating normally."
    
    try:
        analysis_results = analyze_root_cause(correlated_df)
        
        report = []
        report.append("=== WAR ROOM AI INCIDENT REPORT ===")
        report.append(f"Analysis Time: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Correlations: {analysis_results['summary_stats']['total_correlations']}")
        report.append(f"Services Affected: {analysis_results['summary_stats']['services_affected']}")
        report.append("")
        
        if analysis_results['summary_stats']['most_problematic_service']:
            report.append("MOST PROBLEMATIC SERVICE:")
            report.append(f"  Service: {analysis_results['summary_stats']['most_problematic_service']}")
            report.append(f"  Anomaly Count: {analysis_results['summary_stats']['highest_anomaly_count']}")
            report.append("")
        
        report.append("SERVICE RANKINGS:")
        for _, row in analysis_results['service_rankings'].iterrows():
            report.append(f"  {row['metric_service']}: {row['anomaly_count']} anomalies")
        
        report.append("")
        report.append("RECOMMENDATIONS:")
        for service, data in analysis_results['recommendations'].items():
            report.append(f"  {service.capitalize()}: {data['recommendation']}")
        
        report_text = "\n".join(report)
        logger.info("Generated incident report")
        return report_text
        
    except Exception as e:
        logger.error(f"Error generating incident report: {str(e)}")
        return f"Error generating incident report: {str(e)}"
from config import recommendations
import os


def analyze_root_cause(correlated_df):
    if correlated_df.empty:
        print('No correlation found')
        return
    
    print('------------ROOT CAUSE ANALYSIS-----------------------')
    root_cause_summary = correlated_df.groupby('metric_service').size().reset_index(name = 'anomaly_count')
    root_cause_summary = root_cause_summary.sort_values(by='anomaly_count', ascending=False)
    print(root_cause_summary)

    print("\n💡 Recommendations by Service:")
    for _, row in root_cause_summary.iterrows():
        service = row['metric_service']
        suggestion = recommendations.get(service, "No predefined recommendation.")
        print(f" - {service.capitalize()}: {suggestion}")
import pandas as pd
import glob
import os



thresholds = {
    'cpu_pct': 85,
    'latency_ms': {
        'frontend': 350,
        'api': 350,
        'database': 200
    }
}





correlation_window = 5


metrics_df = pd.read_csv('data/metrics.csv',sep = '\t',header=None, names = ['time_stamp','service','metric_name', 'value'])
metrics_df['time_stamp'] = pd.to_datetime(metrics_df['time_stamp'], format= '%d-%m-%Y %H:%M')
metrics_df = metrics_df.sort_values(by='time_stamp', ascending=True)







def metric_anamoly(df, thresholds):
    anamolies = []
    for _, row in df.iterrows():
        metric = row['metric_name']
        value = row['value']
        service = row['service']
        if metric in thresholds:
            threshold = thresholds[metric]
            if isinstance(threshold,dict):
                threshold_value = threshold.get(service, None)
            else:
                threshold_value = threshold
            if threshold_value is not None and value > threshold_value:
                anamolies.append(row)
    return pd.DataFrame(anamolies)




log_files = glob.glob("data/*.log")
logs = []

for file in log_files:
    df = pd.read_csv(file,sep="|", names=['timestamp', 'level', 'message'])
    df['timestamp'] = pd.to_datetime(df['timestamp'].str.strip(), format='%H:%M:%S', errors='coerce')
    base_date = pd.to_datetime("2025-10-12")
    df['timestamp'] = df['timestamp'].apply(lambda t: base_date + pd.Timedelta(hours=t.hour, minutes=t.minute, seconds=t.second))
    df['service'] = os.path.basename(file).replace('.log','')
    logs.append(df)

logs_df = pd.concat(logs, ignore_index=True)

log_anomalies = logs_df[logs_df['level'].str.contains('ERROR', case=False, na=False)]
# print(log_anomalies)
# print("------------------------------------------------------------------------")
# print(metric_anamoly(metrics_df,thresholds))
metric_anamolies = metric_anamoly(metrics_df,thresholds)



correlated = []

for _,m_row in metric_anamolies.iterrows():
    for _, l_row in log_anomalies.iterrows():
        time_diff = abs((m_row['time_stamp'] - l_row['timestamp']).total_seconds())
        if time_diff < correlation_window:
            correlated.append({
                'timestamp':m_row['time_stamp'],
                'metric_service':m_row['service'],
                'metric_name': m_row['metric_name'],
                'metric_value':m_row['value'],
                'log_service':l_row['service'],
                'log_message':l_row['message']
                })
            
correlated_df = pd.DataFrame(correlated)

# print(correlated_df.shape[0])


print("\n=== 🔍 Root Cause Analysis ===")

    # Count how many anomalies per service
root_cause_summary = correlated_df.groupby('metric_service').size().reset_index(name='anomaly_count')
root_cause_summary = root_cause_summary.sort_values(by='anomaly_count', ascending=False)
# probable_root = root_cause_summary.iloc[0]['metric_service']
# print(f"\n🚨 Probable Root Cause Service: {probable_root.upper()}")
print(root_cause_summary)

    # Example recommendations
recommendations = {
        'api': "Check API latency and backend dependencies. Possible timeout or overload.",
        'database': "Database CPU or query latency spikes — consider indexing or connection pooling.",
        'frontend': "Frontend response time high — check for slow API calls or JavaScript rendering bottlenecks."
    }

print("\n💡 Recommendations by Service:")
for _, row in root_cause_summary.iterrows():
    service = row['metric_service']
    suggestion = recommendations.get(service, "No predefined recommendation.")
    print(f" - {service.capitalize()}: {suggestion}")
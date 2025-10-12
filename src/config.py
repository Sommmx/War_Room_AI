thresholds = {
    'cpu_pct': 85,
    'latency_ms': {
        'frontend': 350,
        'api': 350,
        'database': 200
    }
}

correlation_window = 5
BASE_DATE = "2025-10-12"


recommendations = {
        'api': "Check API latency and backend dependencies. Possible timeout or overload.",
        'database': "Database CPU or query latency spikes — consider indexing or connection pooling.",
        'frontend': "Frontend response time high — check for slow API calls or JavaScript rendering bottlenecks."
    }
"""
Example file showing how to instrument your Python applications with Prometheus metrics.
Add this to your Python applications to expose metrics that Prometheus can scrape.
"""
#req txt: prometheus-client 
from prometheus_client import Counter, Histogram, Gauge, Summary, start_http_server
import time
import random

# Create metrics
# Counter - counts how many times something happens
requests_total = Counter('http_requests_total', 'Total HTTP Requests', ['method', 'endpoint'])

# Histogram - tracks the distribution of a value
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration in seconds',
                            ['method', 'endpoint'])

# Gauge - value that can go up and down
in_progress = Gauge('http_requests_in_progress', 'Number of in-progress HTTP requests')

# Summary - similar to histogram but calculates quantiles on the server
request_size = Summary('http_request_size_bytes', 'HTTP request size in bytes')

# Example of how to use these metrics in your application
def process_request(method, endpoint, size):
    # Increment the requests counter
    requests_total.labels(method=method, endpoint=endpoint).inc()
    
    # Use a gauge to track in-progress requests
    in_progress.inc()
    
    # Track request size
    request_size.observe(size)
    
    # Use a histogram to track request duration
    start = time.time()
    try:
        # Your actual request processing logic here
        time.sleep(random.uniform(0.1, 0.5))  # Simulate work
    finally:
        # Record request duration
        duration = time.time() - start
        request_duration.labels(method=method, endpoint=endpoint).observe(duration)
        
        # Decrement the in-progress gauge
        in_progress.dec()

# Example of how to start the metrics server in your application
def start_metrics_server(port=8000):
    # Start up the server to expose the metrics
    start_http_server(port)
    print(f"Metrics server started on port {port}")

# Usage example:
if __name__ == "__main__":
    # Start the metrics server
    start_metrics_server()
    
    # Simulate some requests
    while True:
        process_request(
            random.choice(['GET', 'POST', 'PUT', 'DELETE']),
            random.choice(['/api/data', '/api/users', '/health']),
            random.randint(200, 15000)
        )
        time.sleep(1)

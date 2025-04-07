#!/usr/bin/env python3
from abc import abstractmethod
import os
import socket
import time
import statistics
import requests
import logging
from prometheus_client import Gauge, Counter, Summary
import schedule
from k8s.health import HealthCheck, health_status

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('network-test')

config = {}

METRICS = {
    'http_request_time': Summary('http_request_time_seconds', 'HTTP request time in seconds', ['url', 'status_code']),
    'http_request_errors': Counter('http_request_errors_total', 'Total HTTP request errors', ['url']),
    'http_response_size': Gauge('http_response_size_bytes', 'HTTP response size in bytes', ['url', 'status_code']),
    'http_request_min': Gauge('http_request_min_ms', 'Minimum HTTP request time in milliseconds', ['url']),
    'http_request_max': Gauge('http_request_max_ms', 'Maximum HTTP request time in milliseconds', ['url']),
    'http_request_avg': Gauge('http_request_avg_ms', 'Average HTTP request time in milliseconds', ['url']),
    'http_request_stddev': Gauge('http_request_stddev_ms', 'Standard deviation of HTTP request time', ['url']),

    'tcp_connection_time': Gauge('tcp_connection_time_ms', 'TCP connection time in milliseconds', ['target', 'port']),
    'tcp_connection_errors': Counter('tcp_connection_errors_total', 'Total TCP connection errors', ['target', 'port']),
    'tcp_connection_min': Gauge('tcp_connection_min_ms', 'Minimum TCP connection time in milliseconds', ['target', 'port']),
    'tcp_connection_max': Gauge('tcp_connection_max_ms', 'Maximum TCP connection time in milliseconds', ['target', 'port']),
    'tcp_connection_avg': Gauge('tcp_connection_avg_ms', 'Average TCP connection time in milliseconds', ['target', 'port']),
    'tcp_connection_stddev': Gauge('tcp_connection_stddev_ms', 'Standard deviation of TCP connection time', ['target', 'port']),
}

class NetworkTest:

  def __init__(self, config):
      self.config = config

  def http_request(self, url, timeout=5):
      """Test HTTP request speed"""
      try:
          start_time = time.time()
          response = requests.get(url, timeout=timeout)
          elapsed = time.time() - start_time
          
          METRICS['http_request_time'].labels(url=url, status_code=response.status_code).observe(elapsed)
          METRICS['http_response_size'].labels(url=url, status_code=response.status_code).set(len(response.content))
          
          return {
              "elapsed": elapsed,
              "status_code": response.status_code,
              "content_size": len(response.content)
          }
      except requests.exceptions.RequestException as e:
          logger.error(f"Error requesting {url} - {str(e)}")
          METRICS['http_request_errors'].labels(url=url).inc()
          return None

  def run_http_test(self, url, count=5, quiet=False):
      """Run multiple HTTP tests and calculate statistics"""
      if not quiet:
          logger.info(f"Running HTTP request test to {url}")
      results = []
      
      for i in range(count):
          result = self.http_request(url)
          if result is not None:
              elapsed_ms = result["elapsed"] * 1000
              results.append(elapsed_ms)
              if not quiet:
                  logger.info(f"Request {i+1}/{count}: {elapsed_ms:.2f} ms, Status: {result['status_code']}, Size: {result['content_size']} bytes")
          time.sleep(0.5)  # Delay between requests
      
      if results:
          # Update Prometheus metrics with statistics
          METRICS['http_request_min'].labels(url=url).set(min(results))
          METRICS['http_request_max'].labels(url=url).set(max(results))
          METRICS['http_request_avg'].labels(url=url).set(statistics.mean(results))
          if len(results) > 1:
              METRICS['http_request_stddev'].labels(url=url).set(statistics.stdev(results))
          
          if not quiet:
              logger.info(f"\nHTTP Results for {url}:")
              logger.info(f"  Min: {min(results):.2f} ms")
              logger.info(f"  Max: {max(results):.2f} ms")
              logger.info(f"  Avg: {statistics.mean(results):.2f} ms")
              if len(results) > 1:
                  logger.info(f"  Std Dev: {statistics.stdev(results):.2f} ms")
      else:
          if not quiet:
              logger.warning(f"No successful HTTP requests to {url}")
      
      return results
  
  def ping_host(self, host, port=80, timeout=5):
    """Test TCP connection speed to a host:port"""
    start_time = time.time()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        s.close()
        elapsed = time.time() - start_time
        METRICS['tcp_connection_time'].labels(target=host, port=port).set(elapsed * 1000)
        return elapsed
    except (socket.timeout, socket.error) as e:
        logger.error(f"Error connecting to {host}:{port} - {str(e)}")
        METRICS['tcp_connection_errors'].labels(target=host, port=port).inc()
        return None

  def run_ping_test(self, host, port, count=10, quiet=False):
    """Run multiple ping tests and calculate statistics"""
    if not quiet:
        logger.info(f"Running TCP connection test to {host}:{port}")
    results = []
    
    for i in range(count):
        result = self.ping_host(host, port)
        if result is not None:
            results.append(result * 1000)  # Convert to ms
            if not quiet:
                logger.info(f"Ping {i+1}/{count}: {result * 1000:.2f} ms")
        time.sleep(0.2)  # Short delay between pings
    
    if results:
        # Update Prometheus metrics with statistics
        METRICS['tcp_connection_min'].labels(target=host, port=port).set(min(results))
        METRICS['tcp_connection_max'].labels(target=host, port=port).set(max(results))
        METRICS['tcp_connection_avg'].labels(target=host, port=port).set(statistics.mean(results))
        if len(results) > 1:
            METRICS['tcp_connection_stddev'].labels(target=host, port=port).set(statistics.stdev(results))
        
        if not quiet:
            logger.info(f"\nResults for {host}:{port}:")
            logger.info(f"  Min: {min(results):.2f} ms")
            logger.info(f"  Max: {max(results):.2f} ms")
            logger.info(f"  Avg: {statistics.mean(results):.2f} ms")
            if len(results) > 1:
                logger.info(f"  Std Dev: {statistics.stdev(results):.2f} ms")
    else:
        if not quiet:
            logger.warning(f"No successful connections to {host}:{port}")
    
    return results

  def run_scheduled_tests(self):
      """Run tests based on configuration"""
      logger.info("Starting scheduled network tests")
      
      self._run_scheduled_tests()
      
      health_status["last_test_run"] = time.time()

  @abstractmethod
  def _run_scheduled_tests(self):
      raise NotImplementedError()
      
  def run_scheduler(self):
      """Set up and run the scheduler for periodic tests"""
      interval = self.config.get('interval_seconds', 60)
      
      health_check = HealthCheck(config=self.config)
      health_check.start()

      self.run_scheduled_tests()

      logger.info(f"Setting up scheduled tests to run every {interval} seconds")
      
      schedule.every(interval).seconds.do(self.run_scheduled_tests)
      
      while True:
          schedule.run_pending()
          time.sleep(1)
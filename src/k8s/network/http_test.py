#!/usr/bin/env python3
import argparse
import logging
import time
import sys
import threading
import os

from k8s.health import HealthCheck
from k8s.network.test import NetworkTest

logger = logging.getLogger('network-test')

class HttpNetworkTest(NetworkTest):
    
    def _run_scheduled_tests(self):
      # HTTP tests
      for url in self.config.get('http_targets', []):
          self.run_http_test(url, config.get('http_count', 5), quiet=True)


def load_config_from_env():
    """Load configuration from environment variables"""
    global config
    config = {
        'http_targets': [],
        'interval_seconds': int(os.environ.get('NETWORK_TEST_INTERVAL', 60)),
    }
    
    # Load HTTP targets (comma-separated list of URLs)
    http_targets = os.environ.get('HTTP_TARGETS', '')
    if http_targets:
        config['http_targets'] = [url.strip() for url in http_targets.split(',')]
        config['http_count'] = int(os.environ.get('HTTP_COUNT', 3))

def main():
    parser = argparse.ArgumentParser(description='Kubernetes Network Speed Test with Prometheus Metrics')
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Test command')
    
    # HTTP test
    http_parser = subparsers.add_parser('http', help='Test HTTP requests')
    http_parser.add_argument('--url', help='URL to test')
    http_parser.add_argument('--count', type=int, default=5, help='Number of tests to run (default: 5)')
    
    # Daemon mode for continuous monitoring
    daemon_parser = subparsers.add_parser('daemon', help='Run as a daemon for continuous monitoring')
    daemon_parser.add_argument('--port', type=int, default=8000, help='Port for Prometheus metrics (default: 8000)')
    
    args = parser.parse_args()

    load_config_from_env()
    test = HttpNetworkTest(config)

    if args.command == 'http':
        test.run_http_test(args.url, args.count)
    elif args.command == 'daemon':
        # Start scheduler in a separate thread
        scheduler_thread = threading.Thread(target=test.run_scheduler)
        scheduler_thread.daemon = True
        scheduler_thread.start()
        
        # Keep main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
          
            logger.info("Shutting down...")
            sys.exit(0)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
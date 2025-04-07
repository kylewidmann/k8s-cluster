#!/usr/bin/env python3
import argparse
import time
import sys
import logging
import threading
import os

from k8s.network.test import NetworkTest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('network-test')

class PingNetworkTest(NetworkTest):

  def _run_scheduled_tests(self):
    """Run tests based on configuration"""
    logger.info("Starting scheduled network tests")
    
    # TCP tests
    for target in self.config.get('tcp_targets', []):
        self.run_ping_test(
            target['host'], 
            target.get('port', 80), 
            target.get('count', 5),
            quiet=True
        )

def load_config_from_env():
    """Load configuration from environment variables"""
    config = {
        'tcp_targets': [],
        'http_targets': [],
        'k8s_services': [],
        'nodes': [],
        'interval_seconds': int(os.environ.get('NETWORK_TEST_INTERVAL', 60)),
    }
    
    # Load TCP targets (comma-separated list of host:port)
    tcp_targets = os.environ.get('TCP_TARGETS', '')
    if tcp_targets:
        for target in tcp_targets.split(','):
            parts = target.strip().split(':')
            host = parts[0]
            port = int(parts[1]) if len(parts) > 1 else 80
            config['tcp_targets'].append({
                'host': host,
                'port': port,
                'count': int(os.environ.get('TCP_COUNT', 5))
            })
    
    return config

def main():
    parser = argparse.ArgumentParser(description='Kubernetes Network Speed Test with Prometheus Metrics')
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Test command')
    
    # TCP ping test
    ping_parser = subparsers.add_parser('ping', help='Test TCP connections')
    ping_parser.add_argument('host', help='Hostname or IP to test')
    ping_parser.add_argument('--port', type=int, default=80, help='Port to connect to (default: 80)')
    ping_parser.add_argument('--count', type=int, default=10, help='Number of tests to run (default: 10)')
    
    # Daemon mode for continuous monitoring
    daemon_parser = subparsers.add_parser('daemon', help='Run as a daemon for continuous monitoring')
    daemon_parser.add_argument('--port', type=int, default=8000, help='Port for Prometheus metrics (default: 8000)')
    
    args = parser.parse_args()

    config = load_config_from_env()
    test = PingNetworkTest(config)
    
    if args.command == 'ping':
        test.run_ping_test(args.host, args.port, args.count)
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
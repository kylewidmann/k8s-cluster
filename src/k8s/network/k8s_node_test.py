#!/usr/bin/env python3
import argparse
import socket
import time
import statistics
import sys
import requests
import logging
from concurrent.futures import ThreadPoolExecutor
from prometheus_client import start_http_server, Gauge, Counter, Summary
import threading
import schedule
import os

from k8s.network.test import NetworkTest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('network-test')

class NodeNetworkTest(NetworkTest):
    
    def _run_scheduled_tests(self):
      """Run tests based on configuration"""
      logger.info("Starting scheduled network tests")
      config = self.config
      
      # Node tests
      nodes = config.get('nodes', [])
      if nodes:
          self.scan_k8s_nodes(
              nodes, 
              config.get('node_port', 22),
              config.get('node_count', 3),
              quiet=True
          )

    def scan_k8s_nodes(self, nodes, port=22, count=5, quiet=False):
        """Test connectivity to multiple K8s nodes in parallel"""
        if not quiet:
            logger.info(f"Testing connectivity to {len(nodes)} Kubernetes nodes...")
        results = {}
        
        with ThreadPoolExecutor(max_workers=min(10, len(nodes))) as executor:
            future_to_node = {executor.submit(self.run_ping_test, node, port, count, quiet): node for node in nodes}
            for future in future_to_node:
                node = future_to_node[future]
                try:
                    data = future.result()
                    results[node] = data
                except Exception as exc:
                    logger.error(f'{node} generated an exception: {exc}')
        
        return results

def load_config_from_env():
    """Load configuration from environment variables"""
    config = {
        'nodes': [],
        'interval_seconds': int(os.environ.get('NETWORK_TEST_INTERVAL', 60)),
    }
    
    # Load nodes (comma-separated list of node IPs)
    nodes = os.environ.get('K8S_NODES', '')
    if nodes:
        config['nodes'] = [node.strip() for node in nodes.split(',')]
        config['node_port'] = int(os.environ.get('NODE_PORT', 22))
        config['node_count'] = int(os.environ.get('NODE_COUNT', 3))
    
    return config

def main():
    parser = argparse.ArgumentParser(description='Kubernetes Network Speed Test with Prometheus Metrics')
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Test command')
    
    # K8s nodes test
    nodes_parser = subparsers.add_parser('nodes', help='Test connections to multiple K8s nodes')
    nodes_parser.add_argument('--nodes', required=True, help='Comma-separated list of node IPs')
    nodes_parser.add_argument('--port', type=int, default=22, help='Port to connect to (default: 22)')
    nodes_parser.add_argument('--count', type=int, default=5, help='Number of tests per node (default: 5)')
    
    # Daemon mode for continuous monitoring
    subparsers.add_parser('daemon', help='Run as a daemon for continuous monitoring')
    
    args = parser.parse_args()

    config = load_config_from_env()
    test = NodeNetworkTest(config)    

    if args.command == 'nodes':
        node_list = [node.strip() for node in args.nodes.split(',')]
        test.scan_k8s_nodes(node_list, args.port, args.count)
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
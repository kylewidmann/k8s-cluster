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

class ServiceNetworkTest(NetworkTest):

  def _run_scheduled_tests(self):
      """Run tests based on configuration"""
      logger.info("Starting scheduled network tests")
      
      # K8s service tests
      for service in self.config.get('k8s_services', []):
          self.test_k8s_service(
              service['name'], 
              service.get('namespace', 'default'),
              service.get('port', 80),
              service.get('count', 5),
              quiet=True
          )

  def test_k8s_service(self, service_name, namespace="default", port=80, count=10, quiet=False):
      """Test connectivity to a Kubernetes service"""
      host = f"{service_name}.{namespace}.svc.cluster.local"
      return self.run_ping_test(host, port, count, quiet)

def load_config_from_env():
    """Load configuration from environment variables"""
    config = {
        'k8s_services': [],
        'interval_seconds': int(os.environ.get('NETWORK_TEST_INTERVAL', 60)),
    }
    
    # Load K8s services (comma-separated list of service:namespace:port)
    k8s_services = os.environ.get('K8S_SERVICES', '')
    if k8s_services:
        for service_str in k8s_services.split(','):
            parts = service_str.strip().split(':')
            svc_parts = parts[0].split('.')
            service_name = svc_parts[0]
            namespace = svc_parts[1] if len(svc_parts) > 1 else 'default'
            port = int(parts[1]) if len(parts) > 1 else 80
            config['k8s_services'].append({
                'name': service_name,
                'namespace': namespace,
                'port': port,
                'count': int(os.environ.get('SERVICE_COUNT', 5))
            })

    return config

def main():
    parser = argparse.ArgumentParser(description='Kubernetes Network Speed Test with Prometheus Metrics')
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Test command')
    
    # K8s service test
    k8s_parser = subparsers.add_parser('service', help='Test connections to a K8s service')
    k8s_parser.add_argument('service', help='Service name')
    k8s_parser.add_argument('--namespace', default='default', help='Namespace (default: default)')
    k8s_parser.add_argument('--port', type=int, default=80, help='Port to connect to (default: 80)')
    k8s_parser.add_argument('--count', type=int, default=10, help='Number of tests to run (default: 10)')
    
    # Daemon mode for continuous monitoring
    daemon_parser = subparsers.add_parser('daemon', help='Run as a daemon for continuous monitoring')
    daemon_parser.add_argument('--port', type=int, default=8000, help='Port for Prometheus metrics (default: 8000)')
    
    args = parser.parse_args()

    config = load_config_from_env()
    print(config)
    test = ServiceNetworkTest(config)
    
    if args.command == 'service':
        test.test_k8s_service(args.service, args.namespace, args.port, args.count)
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
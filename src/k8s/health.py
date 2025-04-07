import logging
import threading
import time

from fastapi import FastAPI, Response, status
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest, make_asgi_app, start_http_server
import uvicorn


# Global health status
health_status = {
    "status": "healthy",
    "last_check": time.time(),
    "last_test_run": None,
    "errors": []
}

logger = logging.getLogger('health')

# Create FastAPI app
app = FastAPI(title="Health API", description="Health check API for network test daemon")

class HealthCheck:
    def __init__(self, port=8080, config=None):
        self.app = app
        self.port = port
        self.config = config
        self.setup_routes()
    
    def setup_routes(self):
        @self.app.get("/health")
        @self.app.get("/healthz")
        async def health_check(response: Response):
            # Update last check time
            health_status["last_check"] = time.time()
            
            # Check if tests have run recently (within 2x interval)
            current_time = time.time()
            interval = self.config.get('interval_seconds', 60)
            
            if health_status["last_test_run"] is None or (current_time - health_status["last_test_run"]) > (interval * 2):
                health_status["status"] = "unhealthy"
                health_status["errors"].append("Tests not running within expected interval")
                response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            else:
                health_status["status"] = "healthy"
                health_status["errors"] = []
                response.status_code = status.HTTP_200_OK
            
            return health_status
            
        @self.app.get("/status")
        async def detailed_status():
            """Return detailed status including test results and configuration"""
            return {
                "health": health_status,
                "config": {k: v for k, v in self.config.items() if k != "password"},
                "targets": self.config.get("http_targets", []),
                "uptime": time.time() - self.config.get("start_time", time.time())
            }

        @app.get("/metrics")
        async def metrics():
          """Expose Prometheus metrics"""
          return PlainTextResponse(
              generate_latest(REGISTRY),
              media_type=CONTENT_TYPE_LATEST
          )
        
    def start(self):
      """Start FastAPI health check server"""
      # Run server in a separate thread
      server_thread = threading.Thread(
          target=uvicorn.run,
          kwargs={
              "app": app,
              "host": "0.0.0.0",
              "port": self.port,
              "log_level": "error"  # Reduce log noise
          }
      )
      server_thread.daemon = True
      server_thread.start()
      
      logger.info(f"Started FastAPI health check server on port {self.port}")
      return self
    
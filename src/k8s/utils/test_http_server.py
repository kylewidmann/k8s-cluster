from flask import Flask, request, jsonify
import time
import socket
import random
import threading
import argparse

app = Flask(__name__)

# Track some basic stats
request_stats = {
    "total_requests": 0,
    "start_time": time.time(),
    "paths": {}
}

@app.route('/health')
def health():
    """Simple health check endpoint"""
    update_stats(request.path)
    return jsonify({
        "status": "healthy",
        "timestamp": time.time()
    })

@app.route('/echo', methods=['GET', 'POST'])
def echo():
    """Echo back request information"""
    update_stats(request.path)
    
    # Collect request information
    info = {
        "method": request.method,
        "headers": dict(request.headers),
        "args": dict(request.args),
        "remote_addr": request.remote_addr,
        "timestamp": time.time()
    }
    
    # Add body if present
    if request.is_json:
        info["json"] = request.get_json()
    elif request.form:
        info["form"] = dict(request.form)
    elif request.data:
        info["data"] = request.data.decode('utf-8', errors='replace')
        
    return jsonify(info)

@app.route('/delay/<float:seconds>')
def delay(seconds):
    """Respond after a specified delay"""
    update_stats(request.path)
    
    # Cap maximum delay for safety
    seconds = min(seconds, 30.0)
    
    # Sleep for the specified time
    time.sleep(seconds)
    
    return jsonify({
        "delayed_for": seconds,
        "timestamp": time.time()
    })

@app.route('/random/<int:size>')
def random_data(size):
    """Return random data of specified size in bytes"""
    update_stats(request.path)
    
    # Cap maximum size for safety
    size = min(size, 10 * 1024 * 1024)  # 10MB max
    
    # Generate random bytes
    random_bytes = bytearray(random.getrandbits(8) for _ in range(size))
    
    return random_bytes

@app.route('/stats')
def stats():
    """Return basic usage statistics"""
    update_stats(request.path)
    
    uptime = time.time() - request_stats["start_time"]
    
    return jsonify({
        "total_requests": request_stats["total_requests"],
        "uptime_seconds": uptime,
        "requests_per_second": request_stats["total_requests"] / uptime if uptime > 0 else 0,
        "hostname": socket.gethostname(),
        "paths": request_stats["paths"]
    })

def update_stats(path):
    """Update request statistics"""
    request_stats["total_requests"] += 1
    request_stats["paths"][path] = request_stats["paths"].get(path, 0) + 1

def main():
    parser = argparse.ArgumentParser(description='Simple HTTP Service for Network Testing')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to listen on')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    print(f"Starting HTTP service on {args.host}:{args.port}")
    print("Available endpoints:")
    print("  /health - Health check endpoint")
    print("  /echo - Echo back request information")
    print("  /delay/<seconds> - Respond after specified delay")
    print("  /random/<size> - Return random data of specified size in bytes")
    print("  /stats - Return usage statistics")
    
    app.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == "__main__":
    main()
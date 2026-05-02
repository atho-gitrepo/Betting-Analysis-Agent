#!/usr/bin/env python3
"""
Process manager to run both Analytics Service and Streamlit Dashboard
with automatic restart and health checks - Railway compatible
"""

import subprocess
import time
import logging
import signal
import sys
import os
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | ProcessManager | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/process_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ServiceManager:
    def __init__(self):
        self.processes = {}
        self.running = True
        # Get Railway port (default to 8080 for local testing)
        self.port = os.getenv('PORT', '8080')
        logger.info(f"Using port: {self.port}")
        self.setup_signal_handlers()
    
    def setup_signal_handlers(self):
        """Handle shutdown signals gracefully"""
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)
    
    def shutdown(self, signum, frame):
        """Stop all processes on shutdown"""
        logger.info("Received shutdown signal. Stopping all services...")
        self.running = False
        for name, process in self.processes.items():
            if process and process.poll() is None:
                logger.info(f"Stopping {name}...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        sys.exit(0)
    
    def start_streamlit(self):
        """Start Streamlit dashboard on Railway's PORT"""
        try:
            cmd = [
                "streamlit", "run", "dashboard.py",
                f"--server.port={self.port}",
                "--server.address=0.0.0.0",
                "--server.headless=true",
                "--server.enableCORS=false",
                "--server.enableXsrfProtection=false",
                "--logger.level=info",
                "--browser.gatherUsageStats=false"
            ]
            
            logger.info(f"Starting Streamlit on port {self.port}")
            
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Log output in real-time (non-blocking)
            import threading
            def log_output():
                for line in proc.stdout:
                    logger.info(f"[Dashboard] {line.strip()}")
            
            threading.Thread(target=log_output, daemon=True).start()
            return proc
        except Exception as e:
            logger.error(f"Failed to start dashboard: {e}")
            return None
    
    def run_analytics(self):
        """Run analytics service once"""
        try:
            logger.info("Running analytics service...")
            cmd = ["python", "analytics_service.py"]
            
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Log output in real-time
            for line in proc.stdout:
                logger.info(f"[Analytics] {line.strip()}")
            
            return proc.wait()
        except Exception as e:
            logger.error(f"Analytics service failed: {e}")
            return 1
    
    def run_analytics_scheduled(self, interval_hours=6):
        """Run analytics service on a schedule"""
        # Run immediately on start
        logger.info("Running initial analytics...")
        self.run_analytics()
        
        # Then run on schedule
        while self.running:
            logger.info(f"Next analytics run in {interval_hours} hours")
            for _ in range(interval_hours * 3600):
                if not self.running:
                    break
                time.sleep(1)
            
            if self.running:
                logger.info(f"Running scheduled analytics at {datetime.now()}")
                self.run_analytics()
    
    def check_dashboard_health(self):
        """Check if dashboard is responding"""
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('127.0.0.1', int(self.port)))
            sock.close()
            return result == 0
        except:
            return False
    
    def start(self):
        """Start all services"""
        logger.info("=" * 50)
        logger.info("Starting Betting Analytics System")
        logger.info(f"Railway PORT={self.port}")
        logger.info("=" * 50)
        
        # Create logs directory
        os.makedirs("/app/logs", exist_ok=True)
        
        # Start Streamlit dashboard
        logger.info("Starting Streamlit Dashboard...")
        dashboard_proc = self.start_streamlit()
        if dashboard_proc:
            self.processes['dashboard'] = dashboard_proc
            logger.info(f"✅ Dashboard starting on port {self.port}")
        else:
            logger.error("❌ Failed to start dashboard")
            if not self.running:
                return
        
        # Wait for dashboard to be ready
        logger.info("Waiting for dashboard to be ready...")
        for i in range(30):  # Wait up to 30 seconds
            time.sleep(1)
            if self.check_dashboard_health():
                logger.info("✅ Dashboard is healthy and responding")
                break
            if i % 5 == 0:
                logger.info(f"Waiting for dashboard... ({i+1}/30)")
        
        # Start scheduled analytics in background thread
        import threading
        scheduler_thread = threading.Thread(
            target=self.run_analytics_scheduled,
            args=(6,),  # Run every 6 hours
            daemon=True
        )
        scheduler_thread.start()
        logger.info("✅ Scheduled analytics configured (every 6 hours)")
        
        # Monitor dashboard and restart if needed
        logger.info("Monitoring services (will auto-restart if crashed)...")
        while self.running:
            if self.processes.get('dashboard') and self.processes['dashboard'].poll() is not None:
                logger.warning("⚠️ Dashboard crashed! Restarting...")
                self.processes['dashboard'] = self.start_streamlit()
                if self.processes['dashboard']:
                    logger.info("✅ Dashboard restarted")
                else:
                    logger.error("❌ Failed to restart dashboard")
            
            # Health check logging (every 5 minutes)
            if int(time.time()) % 300 < 30:  # Log every ~5 minutes
                if self.check_dashboard_health():
                    logger.debug("Health check: OK")
                else:
                    logger.warning("Health check: Dashboard not responding")
            
            time.sleep(30)
        
        logger.info("Service manager stopped")

if __name__ == "__main__":
    manager = ServiceManager()
    manager.start()
#!/usr/bin/env python3
"""
Process manager to run both Analytics Service and Streamlit Dashboard
with automatic restart and health checks
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
                process.wait(timeout=5)
        sys.exit(0)
    
    def start_streamlit(self):
        """Start Streamlit dashboard"""
        try:
            cmd = [
                "streamlit", "run", "dashboard.py",
                "--server.port=8501",
                "--server.address=0.0.0.0",
                "--server.headless=true",
                "--server.enableCORS=false",
                "--server.enableXsrfProtection=false",
                "--logger.level=info"
            ]
            
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Log output in real-time
            for line in proc.stdout:
                logger.info(f"[Dashboard] {line.strip()}")
            
            return proc
        except Exception as e:
            logger.error(f"Failed to start dashboard: {e}")
            return None
    
    def run_analytics(self):
        """Run analytics service once"""
        try:
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
            
            return proc.wait()  # Wait for completion
        except Exception as e:
            logger.error(f"Analytics service failed: {e}")
            return 1
    
    def run_analytics_scheduled(self, interval_hours=6):
        """Run analytics service on a schedule"""
        while self.running:
            logger.info(f"Running scheduled analytics (every {interval_hours} hours)")
            exit_code = self.run_analytics()
            logger.info(f"Analytics completed with exit code: {exit_code}")
            
            # Wait for next run
            for _ in range(interval_hours * 3600):
                if not self.running:
                    break
                time.sleep(1)
    
    def start(self):
        """Start all services"""
        logger.info("=" * 50)
        logger.info("Starting Betting Analytics System")
        logger.info("=" * 50)
        
        # Create logs directory
        os.makedirs("/app/logs", exist_ok=True)
        
        # Start Streamlit dashboard
        logger.info("Starting Streamlit Dashboard...")
        dashboard_proc = self.start_streamlit()
        if dashboard_proc:
            self.processes['dashboard'] = dashboard_proc
            logger.info("✅ Dashboard started successfully")
        else:
            logger.error("❌ Failed to start dashboard")
        
        # Wait for dashboard to initialize
        time.sleep(5)
        
        # Run analytics once immediately
        logger.info("Running initial analytics...")
        self.run_analytics()
        
        # Start scheduled analytics in background thread
        import threading
        scheduler_thread = threading.Thread(
            target=self.run_analytics_scheduled,
            args=(6,),  # Run every 6 hours
            daemon=True
        )
        scheduler_thread.start()
        logger.info("Scheduled analytics configured (every 6 hours)")
        
        # Monitor dashboard and restart if needed
        logger.info("Monitoring services...")
        while self.running:
            if self.processes.get('dashboard') and self.processes['dashboard'].poll() is not None:
                logger.warning("Dashboard crashed! Restarting...")
                self.processes['dashboard'] = self.start_streamlit()
                if self.processes['dashboard']:
                    logger.info("✅ Dashboard restarted")
                else:
                    logger.error("❌ Failed to restart dashboard")
            
            time.sleep(30)
        
        logger.info("Service manager stopped")

if __name__ == "__main__":
    manager = ServiceManager()
    manager.start()
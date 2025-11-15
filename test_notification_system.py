#!/usr/bin/env python3
"""
Test script pour vérifier le nouveau système de notifications
avec event loop persistant
"""

import asyncio
import threading
import time
import logging
import sys
sys.path.insert(0, 'src')
from src.telegram_notifier import TelegramNotifier
import yaml

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NotificationTester:
    def __init__(self, config):
        self.telegram = TelegramNotifier(config)
        self._notification_loop = None
        self._start_notification_loop()
    
    def _start_notification_loop(self):
        """Start persistent event loop for notifications in daemon thread"""
        def run_loop():
            try:
                self._notification_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._notification_loop)
                logger.info("📡 Notification event loop started in daemon thread")
                self._notification_loop.run_forever()
            except Exception as e:
                logger.error(f"Notification loop error: {e}", exc_info=True)
        
        thread = threading.Thread(target=run_loop, daemon=True, name="notification-loop")
        thread.start()
        time.sleep(0.1)  # Wait for loop to be ready
    
    def _send_telegram_notification(self, coro):
        """Helper to send Telegram notification synchronously"""
        if not self.telegram or not self._notification_loop:
            return
        
        try:
            logger.info("📤 Sending Telegram notification...")
            
            # Submit coroutine to dedicated loop
            future = asyncio.run_coroutine_threadsafe(coro, self._notification_loop)
            
            # Wait max 5 seconds
            future.result(timeout=5)
            logger.info("✅ Telegram notification sent successfully")
            
        except TimeoutError:
            logger.warning("⚠️ Telegram notification timeout (>5s)")
        except Exception as e:
            logger.error(f"❌ Failed to send Telegram notification: {e}", exc_info=True)
    
    def test_rapid_notifications(self, count=10):
        """Test sending multiple notifications rapidly"""
        logger.info(f"🧪 Testing {count} rapid notifications...")
        
        start_time = time.time()
        
        for i in range(count):
            message = f"Test notification {i+1}/{count}"
            self._send_telegram_notification(
                self.telegram.send_info_notification(message)
            )
            logger.info(f"Submitted notification {i+1}/{count}")
        
        elapsed = time.time() - start_time
        logger.info(f"✅ All {count} notifications submitted in {elapsed:.2f}s")
        
        # Wait a bit for all to complete
        time.sleep(2)
    
    def test_concurrent_notifications(self, count=5):
        """Test sending notifications from multiple threads"""
        logger.info(f"🧪 Testing {count} concurrent notifications from threads...")
        
        def send_from_thread(thread_id):
            for i in range(3):
                message = f"Thread {thread_id}, Message {i+1}"
                self._send_telegram_notification(
                    self.telegram.send_info_notification(message)
                )
                logger.info(f"Thread {thread_id} sent message {i+1}")
                time.sleep(0.1)
        
        threads = []
        start_time = time.time()
        
        for i in range(count):
            thread = threading.Thread(target=send_from_thread, args=(i+1,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        elapsed = time.time() - start_time
        logger.info(f"✅ All threads completed in {elapsed:.2f}s")
        time.sleep(2)
    
    def stop(self):
        """Stop the notification loop"""
        if self._notification_loop:
            self._notification_loop.call_soon_threadsafe(self._notification_loop.stop)
            logger.info("Notification loop stopped")

def main():
    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    logger.info("🚀 Starting notification system test...")
    
    tester = NotificationTester(config)
    
    try:
        # Test 1: Rapid sequential notifications
        tester.test_rapid_notifications(count=10)
        
        time.sleep(2)
        
        # Test 2: Concurrent notifications from multiple threads
        tester.test_concurrent_notifications(count=5)
        
        logger.info("✅ All tests completed successfully!")
        
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    finally:
        tester.stop()
        time.sleep(1)
        logger.info("Test finished")

if __name__ == "__main__":
    main()

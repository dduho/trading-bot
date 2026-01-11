#!/usr/bin/env python3
"""
Quick start script for the trading bot
"""

import sys
import os
import shutil
import logging

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

logger = logging.getLogger(__name__)


def check_disk_space_and_cleanup():
    """
    Check disk space and clean up logs if disk is getting full (>85%)
    """
    try:
        bot_dir = os.path.dirname(os.path.abspath(__file__))
        stat = shutil.disk_usage(bot_dir)

        # Calculate disk usage percentage
        used_percent = (stat.used / stat.total) * 100

        if used_percent > 85:
            logger.warning(f"⚠️ DISK SPACE CRITICAL: {used_percent:.1f}% used ({stat.free / (1024**3):.1f}GB free)")

            # Clean up log files
            log_files = ['bot.log', 'trading_bot.log', 'market_alerts.log']
            total_freed = 0

            for log_file in log_files:
                log_path = os.path.join(bot_dir, log_file)
                if os.path.exists(log_path):
                    size_mb = os.path.getsize(log_path) / (1024 * 1024)
                    if size_mb > 50:  # If log > 50MB, truncate it
                        # Keep last 10000 lines
                        try:
                            with open(log_path, 'r') as f:
                                lines = f.readlines()

                            with open(log_path, 'w') as f:
                                f.writelines(lines[-10000:])  # Keep last 10k lines

                            total_freed += size_mb - (os.path.getsize(log_path) / (1024 * 1024))
                            logger.warning(f"  🗑️ Truncated {log_file} ({size_mb:.1f}MB → {os.path.getsize(log_path) / (1024 * 1024):.1f}MB)")
                        except Exception as e:
                            logger.error(f"Failed to truncate {log_file}: {e}")

            if total_freed > 0:
                logger.warning(f"✅ Freed {total_freed:.1f}MB of disk space")

            # Recheck disk space
            stat = shutil.disk_usage(bot_dir)
            used_percent = (stat.used / stat.total) * 100
            logger.info(f"📊 Disk usage after cleanup: {used_percent:.1f}% ({stat.free / (1024**3):.1f}GB free)")

    except Exception as e:
        logger.error(f"Error checking disk space: {e}")


from trading_bot import main

if __name__ == "__main__":
    # Check disk space before starting
    check_disk_space_and_cleanup()
    main()

#!/usr/bin/env python3
"""
Monitoring script to verify bot stays operational
Checks every 5 minutes and reports status
"""
import subprocess
import time
from datetime import datetime

def check_bot_status():
    """Check if bot is trading"""
    try:
        # Get last 20 opened positions
        result = subprocess.run([
            'gcloud', 'compute', 'ssh', 'trading-bot-instance',
            '--zone=europe-west1-d',
            '--command=grep "Opened.*position" /home/black/trading-bot/trading_bot.log | tail -n 20'
        ], capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if lines and lines[0]:
                # Get timestamp of last trade
                last_line = lines[-1]
                timestamp_str = last_line.split(' - ')[0]

                # Parse timestamp
                timestamp = datetime.fromisoformat(timestamp_str)
                now = datetime.now()

                # Calculate time since last trade
                time_since = (now - timestamp).total_seconds() / 60

                status = "✅ TRADING" if time_since < 60 else "⚠️ STOPPED"

                print(f"\n{'='*60}")
                print(f"[{now.strftime('%H:%M:%S')}] Bot Status: {status}")
                print(f"Last trade: {timestamp.strftime('%H:%M:%S')} ({time_since:.1f} min ago)")
                print(f"Recent trades: {len(lines)}")
                print(f"{'='*60}")

                return time_since < 60
            else:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ❌ NO TRADES FOUND")
                return False
        else:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ❌ ERROR: {result.stderr}")
            return False

    except Exception as e:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ❌ EXCEPTION: {e}")
        return False

def main():
    print("Starting bot monitor...")
    print("Checking every 5 minutes")
    print("Press Ctrl+C to stop\n")

    consecutive_failures = 0

    while True:
        try:
            is_trading = check_bot_status()

            if is_trading:
                consecutive_failures = 0
            else:
                consecutive_failures += 1
                print(f"⚠️ WARNING: Bot not trading for {consecutive_failures * 5} minutes!")

                if consecutive_failures >= 3:  # 15 minutes
                    print("🚨 ALERT: Bot stopped for 15+ minutes!")

            # Wait 5 minutes
            time.sleep(300)

        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user")
            break
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()

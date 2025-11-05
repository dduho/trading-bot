"""
Safety Checks Module
Provides safety confirmations and checks for live trading
"""

import os
import sys
from colorama import Fore, Style, init
import time

init(autoreset=True)


def confirm_live_trading() -> bool:
    """
    Ask user to confirm they understand the risks of live trading

    Returns:
        True if user confirms, False otherwise
    """
    print(f"\n{Fore.RED}{'='*80}")
    print(f"⚠️  LIVE TRADING CONFIRMATION REQUIRED ⚠️")
    print(f"{'='*80}{Style.RESET_ALL}\n")

    print(f"{Fore.YELLOW}You are about to start the bot in LIVE MODE with REAL MONEY.{Style.RESET_ALL}")
    print(f"\n{Fore.RED}RISKS:{Style.RESET_ALL}")
    print(f"  • You can lose ALL of your capital")
    print(f"  • The bot may have bugs or unexpected behavior")
    print(f"  • Market conditions can change rapidly")
    print(f"  • Technical issues (internet, API) can cause problems")
    print(f"  • Past performance does NOT guarantee future results")

    print(f"\n{Fore.CYAN}BEFORE CONTINUING, ENSURE THAT:{Style.RESET_ALL}")
    print(f"  ✓ You have tested in PAPER mode for at least 1 week")
    print(f"  ✓ You have tested in TESTNET mode successfully")
    print(f"  ✓ You have backtested your strategy with good results")
    print(f"  ✓ You understand how the bot works")
    print(f"  ✓ Your API keys do NOT have withdrawal permissions")
    print(f"  ✓ You have enabled 2FA on your exchange account")
    print(f"  ✓ You have configured risk limits in config.yaml")
    print(f"  ✓ You are using money you can afford to lose")
    print(f"  ✓ You will monitor the bot regularly")

    print(f"\n{Fore.RED}{'='*80}{Style.RESET_ALL}\n")

    # First confirmation
    response1 = input(f"{Fore.YELLOW}Type 'I UNDERSTAND THE RISKS' to continue: {Style.RESET_ALL}")
    if response1.strip() != "I UNDERSTAND THE RISKS":
        print(f"\n{Fore.GREEN}✅ Smart choice! Start with paper or testnet mode first.{Style.RESET_ALL}")
        return False

    # Second confirmation
    print(f"\n{Fore.RED}This is your final warning.{Style.RESET_ALL}")
    response2 = input(f"{Fore.YELLOW}Type 'START LIVE TRADING' to confirm: {Style.RESET_ALL}")
    if response2.strip() != "START LIVE TRADING":
        print(f"\n{Fore.GREEN}✅ Cancelled. Please test more before going live.{Style.RESET_ALL}")
        return False

    print(f"\n{Fore.GREEN}✅ Confirmed. Starting live trading...{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}⚠️  Remember: You can stop the bot anytime with Ctrl+C{Style.RESET_ALL}\n")
    time.sleep(2)  # Give user time to read

    return True


def confirm_testnet_trading() -> bool:
    """
    Inform user about testnet mode

    Returns:
        Always True (testnet is safe)
    """
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"📝 TESTNET MODE - Safe Testing Environment")
    print(f"{'='*80}{Style.RESET_ALL}\n")

    print(f"{Fore.GREEN}You are starting in TESTNET mode:{Style.RESET_ALL}")
    print(f"  • Uses exchange testnet/sandbox")
    print(f"  • Fake money (no real risk)")
    print(f"  • Real API calls")
    print(f"  • Perfect for testing before going live")

    print(f"\n{Fore.CYAN}This mode is safe to use.{Style.RESET_ALL}\n")

    response = input(f"Press Enter to continue with testnet mode... ")
    return True


def check_api_permissions(exchange) -> tuple:
    """
    Check if API keys have withdrawal permissions (security risk)

    Args:
        exchange: CCXT exchange instance

    Returns:
        Tuple of (is_safe, message)
    """
    try:
        # Try to fetch account info to check permissions
        # Note: Not all exchanges provide permission info via API
        if hasattr(exchange, 'fetch_balance'):
            # If we can fetch balance, API keys work
            balance = exchange.fetch_balance()

            # Some exchanges provide permission info
            if 'info' in balance and 'permissions' in balance['info']:
                permissions = balance['info']['permissions']
                if 'withdraw' in permissions or 'WITHDRAW' in permissions:
                    return False, "⚠️  WARNING: API keys have WITHDRAWAL permission! This is dangerous!"

        return True, "API keys configured (ensure withdrawal is disabled on exchange)"

    except Exception as e:
        return False, f"Failed to verify API permissions: {e}"


def validate_risk_config(config: dict) -> tuple:
    """
    Validate risk management configuration

    Args:
        config: Bot configuration dict

    Returns:
        Tuple of (is_valid, warnings)
    """
    warnings = []

    # Check if risk config exists
    if 'risk' not in config:
        return False, ["No risk management configuration found!"]

    risk = config['risk']

    # Check max position size
    max_pos = risk.get('max_position_size_percent', 0)
    if max_pos > 20:
        warnings.append(f"⚠️  Max position size is HIGH: {max_pos}% (recommended: 5-10%)")
    elif max_pos == 0:
        warnings.append("❌ Max position size not configured!")

    # Check stop loss
    stop_loss = risk.get('stop_loss_percent', 0)
    if stop_loss == 0:
        warnings.append("❌ Stop loss not configured! You NEED stop losses!")
    elif stop_loss > 5:
        warnings.append(f"⚠️  Stop loss is HIGH: {stop_loss}% (recommended: 1-3%)")

    # Check daily loss limit
    max_daily_loss = risk.get('max_daily_loss_percent', 0)
    if max_daily_loss == 0:
        warnings.append("❌ Daily loss limit not configured!")
    elif max_daily_loss > 10:
        warnings.append(f"⚠️  Daily loss limit is HIGH: {max_daily_loss}% (recommended: 3-5%)")

    # Check max positions
    max_positions = risk.get('max_open_positions', 0)
    if max_positions == 0:
        warnings.append("❌ Max open positions not configured!")
    elif max_positions > 5:
        warnings.append(f"⚠️  Max open positions is HIGH: {max_positions} (recommended: 1-3)")

    return len(warnings) == 0, warnings


def check_environment_variables() -> tuple:
    """
    Check if required environment variables are set

    Returns:
        Tuple of (is_valid, warnings)
    """
    warnings = []

    # Check API keys
    api_key = os.getenv('API_KEY')
    api_secret = os.getenv('API_SECRET')

    if not api_key or api_key == 'your_api_key_here':
        warnings.append("❌ API_KEY not configured in .env file")
    if not api_secret or api_secret == 'your_api_secret_here':
        warnings.append("❌ API_SECRET not configured in .env file")

    # Check exchange
    exchange = os.getenv('EXCHANGE')
    if not exchange:
        warnings.append("❌ EXCHANGE not configured in .env file")

    return len(warnings) == 0, warnings


def pre_flight_check(trading_mode: str, config: dict, exchange=None) -> bool:
    """
    Perform all safety checks before starting the bot

    Args:
        trading_mode: 'paper', 'testnet', or 'live'
        config: Bot configuration
        exchange: CCXT exchange instance (optional)

    Returns:
        True if all checks pass and user confirms
    """
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"🔍 PRE-FLIGHT SAFETY CHECK")
    print(f"{'='*80}{Style.RESET_ALL}\n")

    all_clear = True

    # 1. Check environment variables (for testnet and live)
    if trading_mode in ['testnet', 'live']:
        is_valid, warnings = check_environment_variables()
        if not is_valid:
            print(f"{Fore.RED}Environment Variables:{Style.RESET_ALL}")
            for warning in warnings:
                print(f"  {warning}")
            all_clear = False
        else:
            print(f"{Fore.GREEN}✓ Environment variables configured{Style.RESET_ALL}")

    # 2. Check API permissions (for live mode only)
    if trading_mode == 'live' and exchange:
        is_safe, message = check_api_permissions(exchange)
        if is_safe:
            print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}{message}{Style.RESET_ALL}")
            all_clear = False

    # 3. Validate risk configuration
    is_valid, warnings = validate_risk_config(config)
    if warnings:
        print(f"\n{Fore.YELLOW}Risk Configuration Warnings:{Style.RESET_ALL}")
        for warning in warnings:
            print(f"  {warning}")
        if not is_valid:
            all_clear = False
    else:
        print(f"{Fore.GREEN}✓ Risk management properly configured{Style.RESET_ALL}")

    print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

    # If checks failed, don't continue
    if not all_clear and trading_mode == 'live':
        print(f"{Fore.RED}❌ Safety checks failed! Please fix the issues above before starting.{Style.RESET_ALL}\n")
        return False

    # Ask for user confirmation based on mode
    if trading_mode == 'live':
        return confirm_live_trading()
    elif trading_mode == 'testnet':
        return confirm_testnet_trading()
    else:  # paper mode
        print(f"{Fore.GREEN}✓ Paper mode - Safe to proceed{Style.RESET_ALL}\n")
        return True


def emergency_stop_info():
    """Display emergency stop information"""
    print(f"\n{Fore.YELLOW}{'='*80}")
    print(f"🛑 EMERGENCY STOP INFORMATION")
    print(f"{'='*80}{Style.RESET_ALL}\n")
    print(f"If you need to stop the bot urgently:")
    print(f"  1. Press {Fore.RED}Ctrl + C{Style.RESET_ALL} to stop the bot")
    print(f"  2. If unresponsive, close the terminal")
    print(f"  3. Log into your exchange to manually close positions")
    print(f"\n{Fore.CYAN}The bot will automatically close positions on normal exit.{Style.RESET_ALL}\n")

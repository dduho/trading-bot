#!/bin/bash

################################################################################
# Trading Bot - Oracle Cloud Installation Script
# Automated setup for Ubuntu 22.04 on Oracle Cloud Free Tier
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

################################################################################
# Step 1: System Update
################################################################################
step1_update_system() {
    print_header "STEP 1/8: Updating System"

    sudo apt update
    sudo apt upgrade -y

    print_success "System updated"
}

################################################################################
# Step 2: Install Dependencies
################################################################################
step2_install_dependencies() {
    print_header "STEP 2/8: Installing Dependencies"

    print_info "Installing Python and tools..."
    sudo apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        git \
        curl \
        wget \
        nano \
        vim \
        htop \
        screen \
        tmux \
        build-essential

    print_success "Dependencies installed"
}

################################################################################
# Step 3: Install TA-Lib
################################################################################
step3_install_talib() {
    print_header "STEP 3/8: Installing TA-Lib"

    print_info "Installing TA-Lib dependencies..."
    sudo apt install -y libta-lib0-dev

    print_info "Installing TA-Lib Python wrapper..."
    pip3 install --upgrade ta-lib --break-system-packages

    print_success "TA-Lib installed"
}

################################################################################
# Step 4: Clone from GitHub
################################################################################
step4_clone_github() {
    print_header "STEP 4/8: Cloning from GitHub"

    cd ~

    # Ask for GitHub repo URL
    echo ""
    print_info "Enter your GitHub repository URL:"
    echo "Example: https://github.com/USERNAME/trading-bot.git"
    read -p "GitHub URL: " GITHUB_URL

    if [ -z "$GITHUB_URL" ]; then
        print_error "No URL provided"
        exit 1
    fi

    # Remove existing directory if present
    if [ -d "trading-bot" ]; then
        print_info "Removing existing trading-bot directory..."
        rm -rf trading-bot
    fi

    # Clone the repository
    print_info "Cloning repository..."
    if git clone "$GITHUB_URL" trading-bot; then
        print_success "Repository cloned successfully"
    else
        print_error "Failed to clone repository"
        exit 1
    fi

    cd trading-bot

    # Check if required files exist
    if [ ! -d "src" ] || [ ! -f "config.yaml" ]; then
        print_error "Required files not found in repository!"
        print_error "Make sure your repo contains 'src/' directory and 'config.yaml'"
        exit 1
    fi

    print_success "Repository ready: ~/trading-bot"
}

################################################################################
# Step 5: Configure Credentials (Optional)
################################################################################
step5_configure_credentials() {
    print_header "STEP 5/8: Configure API Credentials"

    cd ~/trading-bot

    echo ""
    print_info "Do you want to configure Binance API credentials now?"
    echo "You can also do this later by editing config.yaml"
    echo ""
    read -p "Configure now? (y/n): " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Opening config.yaml in nano..."
        print_info "Add your API keys in the 'exchange' section"
        echo ""
        read -p "Press ENTER to continue..."
        nano config.yaml
        print_success "Configuration updated"
    else
        print_info "Skipping credentials configuration"
        print_info "Remember to configure them later!"
    fi
}

################################################################################
# Step 6: Install Python Requirements
################################################################################
step6_install_python_requirements() {
    print_header "STEP 6/8: Installing Python Requirements"

    cd ~/trading-bot

    if [ -f "requirements.txt" ]; then
        print_info "Installing from requirements.txt..."
        pip3 install -r requirements.txt --break-system-packages
    else
        print_info "requirements.txt not found, installing common packages..."
        pip3 install \
            ccxt \
            pandas \
            numpy \
            ta-lib \
            python-binance \
            pyyaml \
            scikit-learn \
            --break-system-packages
    fi

    print_success "Python requirements installed"
}

################################################################################
# Step 7: Create Systemd Service
################################################################################
step7_create_service() {
    print_header "STEP 7/8: Creating Systemd Service"

    SERVICE_FILE="/etc/systemd/system/trading-bot.service"

    print_info "Creating service file..."

    sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=Trading Bot with Machine Learning
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/trading-bot
Environment="PYTHONUNBUFFERED=1"
Environment="LOG_ML_FEATURES=0"
ExecStart=/usr/bin/python3 /home/ubuntu/trading-bot/src/trading_bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Resource limits (optional)
MemoryMax=1G
CPUQuota=80%

[Install]
WantedBy=multi-user.target
EOF

    print_success "Service file created"

    print_info "Reloading systemd..."
    sudo systemctl daemon-reload

    print_info "Enabling service..."
    sudo systemctl enable trading-bot

    print_success "Service configured"
}

################################################################################
# Step 8: Configure Firewall
################################################################################
step8_configure_firewall() {
    print_header "STEP 8/8: Configuring Firewall"

    print_info "Allowing SSH..."
    sudo iptables -I INPUT -p tcp --dport 22 -j ACCEPT

    # Try to save iptables rules (may not work on all systems)
    sudo netfilter-persistent save 2>/dev/null || print_info "netfilter-persistent not available (OK)"

    print_success "Firewall configured"
}

################################################################################
# Final Steps
################################################################################
final_steps() {
    print_header "INSTALLATION COMPLETE!"

    echo ""
    print_success "Trading bot is ready to run"
    echo ""

    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Start the bot:"
    echo -e "   ${GREEN}sudo systemctl start trading-bot${NC}"
    echo ""
    echo "2. Check status:"
    echo -e "   ${GREEN}sudo systemctl status trading-bot${NC}"
    echo ""
    echo "3. View logs:"
    echo -e "   ${GREEN}sudo journalctl -u trading-bot -f${NC}"
    echo ""
    echo "4. Test ML system:"
    echo -e "   ${GREEN}cd ~/trading-bot && python3 test_ml_system.py${NC}"
    echo ""

    echo -e "${YELLOW}Useful commands:${NC}"
    echo -e "  Stop:     ${GREEN}sudo systemctl stop trading-bot${NC}"
    echo -e "  Restart:  ${GREEN}sudo systemctl restart trading-bot${NC}"
    echo -e "  Logs:     ${GREEN}sudo journalctl -u trading-bot -n 100${NC}"
    echo ""

    read -p "Start the bot now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo systemctl start trading-bot
        sleep 2
        sudo systemctl status trading-bot
    fi
}

################################################################################
# Main Execution
################################################################################
main() {
    clear

    print_header "TRADING BOT - ORACLE CLOUD SETUP"
    echo ""
    echo "This script will:"
    echo "  1. Update the system"
    echo "  2. Install all dependencies"
    echo "  3. Setup the trading bot"
    echo "  4. Configure systemd service"
    echo ""

    read -p "Continue? (y/n): " -n 1 -r
    echo

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Installation cancelled"
        exit 0
    fi

    echo ""

    # Run all steps
    step1_update_system
    step2_install_dependencies
    step3_install_talib
    step4_clone_github
    step5_configure_credentials
    step6_install_python_requirements
    step7_create_service
    step8_configure_firewall

    final_steps
}

# Run main function
main

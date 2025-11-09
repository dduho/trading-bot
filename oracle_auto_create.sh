#!/bin/bash

################################################################################
# Oracle Cloud A1.Flex Auto-Create Script
# Tries to create instance every 5 minutes until successful
################################################################################

# Configuration
REGION="eu-frankfurt-1"  # Change to your region
COMPARTMENT_ID="your-compartment-ocid"  # Get from OCI Console
SUBNET_ID="your-subnet-ocid"  # Get from VCN details
SSH_KEY_FILE="$HOME/.ssh/oracle_key.pub"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}============================================${NC}"
echo -e "${YELLOW}Oracle A1.Flex Auto-Create Monitor${NC}"
echo -e "${YELLOW}============================================${NC}"
echo ""
echo "This script will try to create an A1.Flex instance every 5 minutes"
echo "Press Ctrl+C to stop"
echo ""

# Counter
attempt=1

while true; do
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${YELLOW}[$timestamp] Attempt #$attempt${NC}"

    # Try each availability domain
    for AD in 1 2 3; do
        echo "  Trying AD-$AD..."

        # OCI CLI command to create instance
        result=$(oci compute instance launch \
            --region "$REGION" \
            --compartment-id "$COMPARTMENT_ID" \
            --availability-domain "AD-$AD" \
            --shape VM.Standard.A1.Flex \
            --shape-config '{"ocpus":2,"memoryInGBs":12}' \
            --image-id "ocid1.image.oc1.eu-frankfurt-1.aaaaaaaaxyz" \
            --subnet-id "$SUBNET_ID" \
            --assign-public-ip true \
            --display-name "trading-bot" \
            --ssh-authorized-keys-file "$SSH_KEY_FILE" \
            2>&1)

        if echo "$result" | grep -q "Out of capacity"; then
            echo -e "    ${RED}✗ Out of capacity${NC}"
        elif echo "$result" | grep -q "\"id\""; then
            echo -e "    ${GREEN}✓ SUCCESS! Instance created in AD-$AD${NC}"
            echo ""
            echo "$result"
            exit 0
        else
            echo -e "    ${RED}✗ Error: $result${NC}"
        fi
    done

    # Wait 5 minutes
    echo -e "  ${YELLOW}Waiting 5 minutes before next attempt...${NC}"
    echo ""
    sleep 300

    ((attempt++))
done

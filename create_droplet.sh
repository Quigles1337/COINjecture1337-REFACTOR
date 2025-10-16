#!/bin/bash

# COINjecture Faucet API - DigitalOcean Droplet Creation Script
# Based on: https://docs.digitalocean.com/reference/api/

# Set your DigitalOcean API token
TOKEN="${DO_TOKEN}"

if [ -z "$TOKEN" ]; then
    echo "❌ Error: DO_TOKEN environment variable not set"
    echo "Please set your DigitalOcean API token:"
    echo "export DO_TOKEN=your_token_here"
    exit 1
fi

echo "🚀 Creating COINjecture Faucet API droplet..."

# Create droplet with proper naming and configuration
curl -X POST \
    -H 'Content-Type: application/json' \
    -H "Authorization: Bearer $TOKEN" \
    -d '{
        "name": "coinjecture-faucet-api",
        "size": "s-2vcpu-4gb-120gb-intel",
        "region": "sfo2",
        "image": "ubuntu-22-04-x64",
        "vpc_uuid": "d6343e1b-4802-423e-9244-b0a244fbd920",
        "ssh_keys": ["YOUR_SSH_KEY_FINGERPRINT"],
        "tags": ["coinjecture", "faucet", "api", "blockchain"],
        "monitoring": true,
        "backups": false,
        "ipv6": true,
        "user_data": "#!/bin/bash\napt update && apt upgrade -y\napt install -y python3.9 python3.9-pip python3.9-venv nginx git\nadduser coinjecture\nusermod -aG sudo coinjecture\necho \"coinjecture ALL=(ALL) NOPASSWD:ALL\" >> /etc/sudoers"
    }' \
    "https://api.digitalocean.com/v2/droplets"

echo ""
echo "✅ Droplet creation request sent!"
echo "📋 Droplet Details:"
echo "   Name: coinjecture-faucet-api"
echo "   Size: s-2vcpu-4gb-120gb-intel (2 vCPU, 4GB RAM, 120GB SSD)"
echo "   Region: sfo2 (San Francisco)"
echo "   Image: Ubuntu 22.04 LTS"
echo "   Tags: coinjecture, faucet, api, blockchain"
echo "   Monitoring: Enabled"
echo "   IPv6: Enabled"
echo ""
echo "⏳ Droplet is being created... This may take 2-3 minutes."
echo "🔍 Check your DigitalOcean dashboard or run:"
echo "   curl -H \"Authorization: Bearer \$DO_TOKEN\" https://api.digitalocean.com/v2/droplets | jq '.droplets[] | select(.name==\"coinjecture-faucet-api\") | {name, status, networks}'"

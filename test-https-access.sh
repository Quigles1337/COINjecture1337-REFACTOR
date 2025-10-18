#!/usr/bin/env bash
set -euo pipefail

echo "🧪 Testing HTTPS Access for coinjecture.com"
echo "==========================================="
echo ""

# Test main domain
echo "1. Testing https://coinjecture.com"
if curl -s -I "https://coinjecture.com" | head -1 | grep -q "200 OK"; then
    echo "   ✅ HTTPS working for coinjecture.com"
else
    echo "   ❌ HTTPS not working for coinjecture.com"
    echo "   Status: $(curl -s -I "https://coinjecture.com" | head -1)"
fi

echo ""

# Test www subdomain
echo "2. Testing https://www.coinjecture.com"
if curl -s -I "https://www.coinjecture.com" | head -1 | grep -q "200 OK"; then
    echo "   ✅ HTTPS working for www.coinjecture.com"
else
    echo "   ❌ HTTPS not working for www.coinjecture.com"
    echo "   Status: $(curl -s -I "https://www.coinjecture.com" | head -1)"
fi

echo ""

# Test HTTP redirect
echo "3. Testing HTTP to HTTPS redirect"
HTTP_REDIRECT=$(curl -s -I "http://coinjecture.com" | grep -i "location" | head -1)
if [[ "$HTTP_REDIRECT" == *"https://"* ]]; then
    echo "   ✅ HTTP redirects to HTTPS"
    echo "   Redirect: $HTTP_REDIRECT"
else
    echo "   ❌ HTTP redirect not working"
    echo "   Response: $HTTP_REDIRECT"
fi

echo ""

# Test SSL certificate
echo "4. Testing SSL Certificate"
SSL_INFO=$(echo | openssl s_client -servername coinjecture.com -connect coinjecture.com:443 2>/dev/null | openssl x509 -noout -dates 2>/dev/null || echo "No SSL info")
if [[ "$SSL_INFO" != "No SSL info" ]]; then
    echo "   ✅ SSL Certificate found"
    echo "   $SSL_INFO"
else
    echo "   ❌ SSL Certificate not found"
fi

echo ""

# Test website content
echo "5. Testing website content"
CONTENT=$(curl -s "https://coinjecture.com" | grep -i "coinjecture" | head -1 || echo "No content found")
if [[ "$CONTENT" != "No content found" ]]; then
    echo "   ✅ Website content accessible"
    echo "   Found: $CONTENT"
else
    echo "   ❌ Website content not accessible"
fi

echo ""
echo "🎯 Summary:"
echo "   If all tests show ✅, your HTTPS setup is complete!"
echo "   If any tests show ❌, check the Cloudflare configuration."
echo ""
echo "🔗 Your secure website:"
echo "   https://coinjecture.com"
echo "   https://www.coinjecture.com"

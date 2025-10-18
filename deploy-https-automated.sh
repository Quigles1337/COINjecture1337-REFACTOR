#!/usr/bin/env bash
set -euo pipefail

echo "🚀 COINjecture HTTPS Deployment Script"
echo "======================================"
echo ""

# Check if AWS CLI is configured
if ! aws sts get-caller-identity >/dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Please run: aws configure"
    exit 1
fi

echo "✅ AWS CLI configured"
echo ""

# Get S3 bucket IP address
echo "🔍 Getting S3 bucket IP address..."
S3_IP=$(nslookup coinjecture.com.s3-website.us-east-1.amazonaws.com | grep "Address:" | tail -1 | awk '{print $2}')
echo "   S3 IP: $S3_IP"
echo ""

# Create CloudFront distribution config
echo "🌐 Creating CloudFront distribution..."

# First, request SSL certificate
echo "🔐 Step 1: Requesting SSL Certificate..."
CERT_ARN=$(aws acm request-certificate \
  --domain-name "coinjecture.com" \
  --subject-alternative-names "www.coinjecture.com" \
  --validation-method DNS \
  --region us-east-1 \
  --query 'CertificateArn' \
  --output text)

echo "   Certificate ARN: $CERT_ARN"
echo ""
echo "⚠️  IMPORTANT: You need to validate this certificate manually:"
echo "   1. Go to: https://console.aws.amazon.com/acm/home?region=us-east-1"
echo "   2. Click on your certificate"
echo "   3. Add the DNS validation records to your domain"
echo "   4. Wait for validation (5-30 minutes)"
echo ""
echo "Press Enter after you've added the DNS validation records..."
read

echo "⏳ Waiting for certificate validation..."
aws acm wait certificate-validated \
  --certificate-arn "$CERT_ARN" \
  --region us-east-1

echo "✅ Certificate validated!"
echo ""

# Create CloudFront distribution
echo "🌐 Step 2: Creating CloudFront Distribution..."

cat > /tmp/cloudfront-config.json <<EOF
{
  "Comment": "COINjecture HTTPS Distribution",
  "Enabled": true,
  "Origins": [{
    "Id": "S3-coinjecture-origin",
    "DomainName": "coinjecture.com.s3-website.us-east-1.amazonaws.com",
    "CustomOriginConfig": {
      "HTTPPort": 80,
      "HTTPSPort": 443,
      "OriginProtocolPolicy": "http-only"
    }
  }],
  "DefaultRootObject": "index.html",
  "DefaultCacheBehavior": {
    "TargetOriginId": "S3-coinjecture-origin",
    "ViewerProtocolPolicy": "redirect-to-https",
    "AllowedMethods": ["GET", "HEAD", "OPTIONS"],
    "CachedMethods": ["GET", "HEAD"],
    "ForwardedValues": {
      "QueryString": false,
      "Cookies": {"Forward": "none"}
    },
    "Compress": true,
    "MinTTL": 0,
    "DefaultTTL": 86400,
    "MaxTTL": 31536000
  },
  "CustomErrorResponses": [{
    "ErrorCode": 404,
    "ResponsePagePath": "/index.html",
    "ResponseCode": "200",
    "ErrorCachingMinTTL": 300
  }],
  "Aliases": ["coinjecture.com", "www.coinjecture.com"],
  "ViewerCertificate": {
    "ACMCertificateArn": "${CERT_ARN}",
    "SSLSupportMethod": "sni-only",
    "MinimumProtocolVersion": "TLSv1.2_2021"
  },
  "PriceClass": "PriceClass_100"
}
EOF

# Create the distribution
CF_OUTPUT=$(aws cloudfront create-distribution \
  --distribution-config file:///tmp/cloudfront-config.json \
  --query '{Id:Distribution.Id, Domain:Distribution.DomainName, Status:Distribution.Status}' \
  --output json)

CF_ID=$(echo "$CF_OUTPUT" | jq -r '.Id')
CF_DOMAIN=$(echo "$CF_OUTPUT" | jq -r '.Domain')
CF_STATUS=$(echo "$CF_OUTPUT" | jq -r '.Status')

echo "✅ CloudFront Distribution Created!"
echo "   ID: $CF_ID"
echo "   Domain: $CF_DOMAIN"
echo "   Status: $CF_STATUS"
echo ""

echo "📝 Step 3: DNS Configuration Required"
echo ""
echo "Add these DNS records for coinjecture.com:"
echo ""
echo "   Type: A (ALIAS if supported)"
echo "   Name: coinjecture.com"
echo "   Value: $CF_DOMAIN"
echo ""
echo "   Type: CNAME"
echo "   Name: www.coinjecture.com"
echo "   Value: $CF_DOMAIN"
echo ""

echo "⏳ Step 4: Waiting for CloudFront deployment..."
echo "   This takes 15-30 minutes..."

# Wait for deployment
while true; do
  STATUS=$(aws cloudfront get-distribution --id "$CF_ID" --query 'Distribution.Status' --output text)
  if [ "$STATUS" = "Deployed" ]; then
    echo "✅ CloudFront deployed!"
    break
  fi
  echo "   Status: $STATUS (waiting...)"
  sleep 30
done

echo ""
echo "🎉 HTTPS Setup Complete!"
echo ""
echo "Your website will be available at:"
echo "   https://coinjecture.com"
echo "   https://www.coinjecture.com"
echo ""
echo "Note: DNS propagation may take up to 24 hours"
echo ""

# Test the distribution
echo "🧪 Testing HTTPS access..."
if curl -s -I "https://$CF_DOMAIN" | head -1 | grep -q "200 OK"; then
    echo "✅ CloudFront distribution is working!"
else
    echo "⚠️  CloudFront may still be deploying. Check again in a few minutes."
fi

echo ""
echo "📋 Next Steps:"
echo "   1. Update your domain's DNS records as shown above"
echo "   2. Wait for DNS propagation (5-30 minutes)"
echo "   3. Test: curl -I https://coinjecture.com"
echo "   4. Your website will be secure with HTTPS!"

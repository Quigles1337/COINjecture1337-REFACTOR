#!/usr/bin/env bash
set -euo pipefail

DOMAIN="coinjecture.com"
BUCKET_NAME="coinjecture.com"
REGION="us-east-1"

echo "🔐 Step 1: Request SSL Certificate"
CERT_ARN=$(aws acm request-certificate \
  --domain-name "$DOMAIN" \
  --subject-alternative-names "www.$DOMAIN" \
  --validation-method DNS \
  --region us-east-1 \
  --query 'CertificateArn' \
  --output text)

echo "Certificate ARN: $CERT_ARN"
echo ""
echo "⚠️  IMPORTANT: Add the DNS validation records shown in ACM console"
echo "   Go to: https://console.aws.amazon.com/acm/home?region=us-east-1"
echo ""
echo "Press Enter after you've added the DNS records..."
read

echo "⏳ Waiting for certificate validation..."
aws acm wait certificate-validated \
  --certificate-arn "$CERT_ARN" \
  --region us-east-1

echo "✅ Certificate validated!"
echo ""

echo "🌐 Step 2: Create CloudFront Distribution"

# Create distribution config
cat > /tmp/cf-config.json <<EOF
{
  "Comment": "COINjecture HTTPS",
  "Enabled": true,
  "Origins": [{
    "Id": "S3-origin",
    "DomainName": "${BUCKET_NAME}.s3.amazonaws.com",
    "S3OriginConfig": {"OriginAccessIdentity": ""}
  }],
  "DefaultRootObject": "index.html",
  "DefaultCacheBehavior": {
    "TargetOriginId": "S3-origin",
    "ViewerProtocolPolicy": "redirect-to-https",
    "AllowedMethods": ["GET", "HEAD", "OPTIONS"],
    "CachedMethods": ["GET", "HEAD"],
    "ForwardedValues": {
      "QueryString": false,
      "Cookies": {"Forward": "none"}
    },
    "Compress": true,
    "MinTTL": 0
  },
  "CustomErrorResponses": [{
    "ErrorCode": 404,
    "ResponsePagePath": "/index.html",
    "ResponseCode": "200"
  }],
  "Aliases": ["${DOMAIN}", "www.${DOMAIN}"],
  "ViewerCertificate": {
    "ACMCertificateArn": "${CERT_ARN}",
    "SSLSupportMethod": "sni-only",
    "MinimumProtocolVersion": "TLSv1.2_2021"
  },
  "PriceClass": "PriceClass_100"
}
EOF

CF_OUTPUT=$(aws cloudfront create-distribution \
  --distribution-config file:///tmp/cf-config.json \
  --query '{Id:Distribution.Id, Domain:Distribution.DomainName}' \
  --output json)

CF_ID=$(echo "$CF_OUTPUT" | jq -r '.Id')
CF_DOMAIN=$(echo "$CF_OUTPUT" | jq -r '.Domain')

echo "CloudFront Distribution Created:"
echo "  ID: $CF_ID"
echo "  Domain: $CF_DOMAIN"
echo ""

echo "📝 Step 3: Update DNS Records"
echo ""
echo "Add these DNS records for $DOMAIN:"
echo ""
echo "  Type: A (ALIAS if supported) or CNAME"
echo "  Name: $DOMAIN"
echo "  Value: $CF_DOMAIN"
echo ""
echo "  Type: CNAME"
echo "  Name: www.$DOMAIN"
echo "  Value: $CF_DOMAIN"
echo ""
echo "⏳ Waiting for CloudFront deployment (this takes 15-30 minutes)..."

# Wait for deployment
while true; do
  STATUS=$(aws cloudfront get-distribution --id "$CF_ID" --query 'Distribution.Status' --output text)
  if [ "$STATUS" = "Deployed" ]; then
    echo "✅ CloudFront deployed!"
    break
  fi
  echo "  Status: $STATUS (waiting...)"
  sleep 30
done

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Your website is now available at:"
echo "  https://$DOMAIN"
echo "  https://www.$DOMAIN"
echo ""
echo "Note: DNS propagation may take up to 24 hours"

#!/usr/bin/env bash
set -euo pipefail

BUCKET_NAME="coinjecture.com"

echo "🔍 Checking S3 bucket setup for HTTPS deployment..."
echo ""

# Check if bucket exists
echo "1. Checking if S3 bucket exists:"
if aws s3 ls "s3://$BUCKET_NAME" 2>/dev/null; then
    echo "   ✅ Bucket $BUCKET_NAME exists"
else
    echo "   ❌ Bucket $BUCKET_NAME not found"
    echo "   Please create the bucket first or update BUCKET_NAME in this script"
    exit 1
fi

echo ""

# Check bucket website configuration
echo "2. Checking bucket website configuration:"
WEBSITE_CONFIG=$(aws s3api get-bucket-website --bucket "$BUCKET_NAME" 2>/dev/null || echo "No website config")
if [[ "$WEBSITE_CONFIG" == "No website config" ]]; then
    echo "   ❌ Bucket website not configured"
    echo "   Run: aws s3 website s3://$BUCKET_NAME --index-document index.html"
else
    echo "   ✅ Bucket website configured"
    echo "$WEBSITE_CONFIG"
fi

echo ""

# Check bucket policy
echo "3. Checking bucket policy:"
POLICY=$(aws s3api get-bucket-policy --bucket "$BUCKET_NAME" 2>/dev/null || echo "No policy")
if [[ "$POLICY" == "No policy" ]]; then
    echo "   ❌ No bucket policy found"
    echo "   You may need to add a policy for CloudFront access"
else
    echo "   ✅ Bucket policy exists"
fi

echo ""

# Check if files are uploaded
echo "4. Checking uploaded files:"
aws s3 ls "s3://$BUCKET_NAME/" --recursive | head -10

echo ""

# Get bucket region
echo "5. Bucket region:"
REGION=$(aws s3api get-bucket-location --bucket "$BUCKET_NAME" --query 'LocationConstraint' --output text)
if [[ "$REGION" == "None" ]]; then
    REGION="us-east-1"
fi
echo "   Region: $REGION"

echo ""

# Get website endpoint
echo "6. Website endpoint:"
if [[ "$REGION" == "us-east-1" ]]; then
    ENDPOINT="$BUCKET_NAME.s3-website.us-east-1.amazonaws.com"
else
    ENDPOINT="$BUCKET_NAME.s3-website.$REGION.amazonaws.com"
fi
echo "   Endpoint: $ENDPOINT"

echo ""

# Test website access
echo "7. Testing website access:"
if curl -s -I "http://$ENDPOINT" | head -1 | grep -q "200 OK"; then
    echo "   ✅ Website accessible at http://$ENDPOINT"
else
    echo "   ❌ Website not accessible"
fi

echo ""
echo "📋 Summary for HTTPS setup:"
echo "   Bucket: $BUCKET_NAME"
echo "   Region: $REGION"
echo "   Endpoint: $ENDPOINT"
echo ""
echo "Next steps:"
echo "   1. Choose HTTPS method:"
echo "      - Cloudflare (easier): Follow setup-cloudflare-https.md"
echo "      - AWS CloudFront: Run ./deploy-https.sh"
echo "   2. Update DNS records to point to your chosen solution"

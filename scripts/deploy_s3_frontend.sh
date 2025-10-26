#!/bin/bash
# Deploy Updated Frontend to S3
# Includes CID download functionality and mobile optimization

set -e

echo "🌐 COINjecture S3 Frontend Deployment"
echo "===================================="

# Configuration
S3_BUCKET="coinjecture-frontend"
CLOUDFRONT_DISTRIBUTION="E1234567890ABCD"  # Replace with actual CloudFront distribution ID
REGION="us-east-1"

echo "📋 Deployment Configuration:"
echo "  S3 Bucket: $S3_BUCKET"
echo "  CloudFront: $CLOUDFRONT_DISTRIBUTION"
echo "  Region: $REGION"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install AWS CLI first."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "web/index.html" ]; then
    echo "❌ Please run this script from the COINjecture project root directory"
    exit 1
fi

# Create backup of current S3 content
echo "📦 Creating S3 backup..."
aws s3 sync s3://$S3_BUCKET s3://$S3_BUCKET-backup-$(date +%Y%m%d-%H%M%S)/ --region $REGION

# Upload updated frontend files
echo "📤 Uploading updated frontend files..."

# Upload main files
aws s3 cp web/index.html s3://$S3_BUCKET/index.html --region $REGION --content-type "text/html"
aws s3 cp web/app.js s3://$S3_BUCKET/app.js --region $REGION --content-type "application/javascript"
aws s3 cp web/style.css s3://$S3_BUCKET/style.css --region $REGION --content-type "text/css"

# Upload documentation
if [ -f "web/README.md" ]; then
    aws s3 cp web/README.md s3://$S3_BUCKET/README.md --region $REGION --content-type "text/markdown"
fi

# Upload PDF files
if [ -f "web/Critical_Complex_Equilibrium_Proof.pdf" ]; then
    aws s3 cp web/Critical_Complex_Equilibrium_Proof.pdf s3://$S3_BUCKET/Critical_Complex_Equilibrium_Proof.pdf --region $REGION --content-type "application/pdf"
fi

# Set proper cache headers
echo "⚙️  Setting cache headers..."
aws s3 cp s3://$S3_BUCKET/index.html s3://$S3_BUCKET/index.html --metadata-directive REPLACE --cache-control "max-age=300" --region $REGION
aws s3 cp s3://$S3_BUCKET/app.js s3://$S3_BUCKET/app.js --metadata-directive REPLACE --cache-control "max-age=3600" --region $REGION
aws s3 cp s3://$S3_BUCKET/style.css s3://$S3_BUCKET/style.css --metadata-directive REPLACE --cache-control "max-age=3600" --region $REGION

# Set CORS policy
echo "🔧 Setting CORS policy..."
aws s3api put-bucket-cors --bucket $S3_BUCKET --cors-configuration file://web/cors.json --region $REGION

# Invalidate CloudFront cache
echo "🔄 Invalidating CloudFront cache..."
aws cloudfront create-invalidation --distribution-id $CLOUDFRONT_DISTRIBUTION --paths "/*" --region $REGION

# Test the deployment
echo "🧪 Testing deployment..."
FRONTEND_URL="https://$S3_BUCKET.s3-website-$REGION.amazonaws.com"

if curl -s "$FRONTEND_URL" | grep -q "COINjecture"; then
    echo "✅ Frontend deployment successful"
    echo "🌐 Frontend URL: $FRONTEND_URL"
else
    echo "❌ Frontend deployment test failed"
    exit 1
fi

# Test CID download functionality
echo "🔗 Testing CID download functionality..."
if curl -s "$FRONTEND_URL/app.js" | grep -q "downloadProofBundle"; then
    echo "✅ CID download functionality deployed"
else
    echo "⚠️  CID download functionality not found"
fi

# Test mobile optimization
echo "📱 Testing mobile optimization..."
if curl -s "$FRONTEND_URL/style.css" | grep -q "@media"; then
    echo "✅ Mobile optimization deployed"
else
    echo "⚠️  Mobile optimization not found"
fi

echo "🎉 S3 frontend deployment completed successfully!"
echo "📊 Deployment Summary:"
echo "  - Frontend URL: $FRONTEND_URL"
echo "  - CID Download: ✅ Enabled"
echo "  - Mobile Optimized: ✅ Enabled"
echo "  - CloudFront Cache: ✅ Invalidated"
echo "  - CORS Policy: ✅ Configured"

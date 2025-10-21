#!/usr/bin/env bash
set -euo pipefail

BUCKET_NAME="coinjecture.com"
REGION="us-east-1"
CLOUDFRONT_DISTRIBUTION_ID="E2INLKPSADEUYX"

echo "Creating bucket (if not exists)"
aws s3api create-bucket --bucket "$BUCKET_NAME" --region "$REGION" || true

echo "Enable website hosting"
aws s3 website s3://"$BUCKET_NAME"/ --index-document index.html --error-document index.html

echo "Sync web/ to bucket"
aws s3 sync . s3://"$BUCKET_NAME"/ --delete

echo "Invalidating CloudFront cache to serve latest version"
aws cloudfront create-invalidation --distribution-id "$CLOUDFRONT_DISTRIBUTION_ID" --paths "/*"

echo "✅ Deployment complete! CloudFront cache invalidated."
echo "🌐 Website: https://coinjecture.com"
echo "📊 S3 Website: http://coinjecture.com.s3-website-us-east-1.amazonaws.com/"

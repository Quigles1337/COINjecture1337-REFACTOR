#!/usr/bin/env bash
set -euo pipefail

BUCKET_NAME="your-bucket-name"
REGION="us-east-1"

echo "Creating bucket (if not exists)"
aws s3api create-bucket --bucket "$BUCKET_NAME" --region "$REGION" \
  --create-bucket-configuration LocationConstraint="$REGION" || true

echo "Enable website hosting"
aws s3 website s3://"$BUCKET_NAME"/ --index-document index.html --error-document index.html

echo "Apply bucket policy"
aws s3api put-bucket-policy --bucket "$BUCKET_NAME" --policy file://bucket-policy.json

echo "Apply CORS"
aws s3api put-bucket-cors --bucket "$BUCKET_NAME" --cors-configuration file://cors.json

echo "Sync web/ to bucket"
aws s3 sync . s3://"$BUCKET_NAME"/ --delete --acl public-read

echo "Done. Website endpoint is listed in the S3 console for bucket $BUCKET_NAME"



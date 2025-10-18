# COINjecture Web Frontend (Static)

Tabs:
- API Docs (renders `API.README.md`)
- Live Console (fetches latest block JSON)

Local preview:
```bash
python3 -m http.server 8080 -d web
```

Deploy to AWS S3:
```bash
# 1) Create bucket
aws s3api create-bucket --bucket <your-bucket-name> --region <region> --create-bucket-configuration LocationConstraint=<region>

# 2) Enable website
aws s3 website s3://<your-bucket-name>/ --index-document index.html --error-document index.html

# 3) Policy & CORS
aws s3api put-bucket-policy --bucket <your-bucket-name> --policy file://bucket-policy.json
aws s3api put-bucket-cors --bucket <your-bucket-name> --cors-configuration file://cors.json

# 4) Sync
aws s3 sync ./web s3://<your-bucket-name>/ --delete --acl public-read
```

CORS note: The console calls `http://167.172.213.70:5000/v1/data/block/latest`. Ensure that API includes `Access-Control-Allow-Origin: *` or place a proxy in front.


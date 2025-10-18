# Cloudflare HTTPS Setup (Easier Alternative)

## Quick Setup Steps

### 1. Sign up for Cloudflare
- Go to [cloudflare.com](https://cloudflare.com)
- Sign up for free account
- Add your domain `coinjecture.com`

### 2. Update Nameservers
Cloudflare will give you 2 nameservers like:
```
ns1.cloudflare.com
ns2.cloudflare.com
```

Update your domain's nameservers at your domain registrar to point to Cloudflare.

### 3. Configure DNS Records
In Cloudflare DNS settings, add:

| Type | Name | Content | Proxy Status |
|------|------|---------|--------------|
| A | @ | [Your S3 bucket IP] | 🟠 Proxied |
| CNAME | www | coinjecture.com | 🟠 Proxied |

**Note**: You need to find your S3 bucket's IP address. You can get this by:
```bash
nslookup coinjecture.com.s3-website.us-east-1.amazonaws.com
```

### 4. Enable SSL/TLS
In Cloudflare dashboard:
- Go to **SSL/TLS** → **Overview**
- Set encryption mode to **"Flexible"** (Cloudflare → HTTPS, Cloudflare → S3 HTTP)
- Go to **SSL/TLS** → **Edge Certificates**
- Enable **"Always Use HTTPS"**
- Enable **"Automatic HTTPS Rewrites"**

### 5. Test HTTPS
Once DNS propagates (5-30 minutes):
```bash
curl -I https://coinjecture.com
curl -I https://www.coinjecture.com
```

Both should return `200 OK` with HTTPS.

## Benefits of Cloudflare
- ✅ **Free SSL certificate** (automatic)
- ✅ **Fast setup** (5 minutes vs 30+ minutes)
- ✅ **Global CDN** (faster loading worldwide)
- ✅ **DDoS protection** (included)
- ✅ **Analytics** (basic traffic stats)
- ✅ **Automatic HTTPS** (redirects HTTP to HTTPS)

## Alternative: AWS CloudFront (More Complex)
If you prefer AWS native solution, use the `deploy-https.sh` script instead.

## Update Website for HTTPS
Once HTTPS is working, you may want to update API calls to use HTTPS if your backend supports it:

```javascript
// In web/app.js, update the API base URL
this.apiBase = 'https://167.172.213.70:5000'; // If backend supports HTTPS
// Or keep HTTP for now:
this.apiBase = 'http://167.172.213.70:5000'; // Current working setup
```

The browser will allow mixed content (HTTPS site calling HTTP API) but may show warnings.

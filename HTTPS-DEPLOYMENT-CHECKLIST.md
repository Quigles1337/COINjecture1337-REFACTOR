# 🔐 HTTPS Deployment Checklist for coinjecture.com

## ✅ Current Status
- ✅ S3 bucket configured and accessible
- ✅ Website files uploaded
- ✅ S3 IP address identified: `16.182.98.101`
- ✅ Cloudflare deployment script ready

## 🚀 Next Steps (Follow in Order)

### Step 1: Cloudflare Account Setup
- [ ] Go to [cloudflare.com](https://cloudflare.com)
- [ ] Sign up for free account
- [ ] Add domain: `coinjecture.com`
- [ ] Choose "Free" plan

### Step 2: Update Nameservers
- [ ] Copy the 2 nameservers from Cloudflare (e.g., `ns1.cloudflare.com`, `ns2.cloudflare.com`)
- [ ] Go to your domain registrar (where you bought coinjecture.com)
- [ ] Update nameservers to Cloudflare's
- [ ] Wait 5-30 minutes for propagation

### Step 3: Configure DNS Records
In Cloudflare DNS settings, add:

| Type | Name | Content | Proxy Status |
|------|------|---------|--------------|
| A | @ | 16.182.98.101 | 🟠 Proxied (ON) |
| CNAME | www | coinjecture.com | 🟠 Proxied (ON) |

**Important**: Both records must have **Proxy Status ON** (🟠)

### Step 4: Enable SSL/TLS
In Cloudflare dashboard:
- [ ] Go to **SSL/TLS** → **Overview**
- [ ] Set encryption mode to **"Flexible"**
- [ ] Go to **SSL/TLS** → **Edge Certificates**
- [ ] Enable **"Always Use HTTPS"**
- [ ] Enable **"Automatic HTTPS Rewrites"**

### Step 5: Test HTTPS Access
```bash
curl -I https://coinjecture.com
curl -I https://www.coinjecture.com
```

Both should return `200 OK` with HTTPS.

## 🎯 Expected Results
- ✅ `https://coinjecture.com` (secure)
- ✅ `https://www.coinjecture.com` (secure)
- ✅ Automatic HTTP → HTTPS redirects
- ✅ Free SSL certificate
- ✅ Global CDN for faster loading
- ✅ DDoS protection

## ⏱️ Timeline
- **Setup**: 5 minutes
- **DNS Propagation**: 5-30 minutes
- **Total**: ~10-35 minutes

## 🆘 Troubleshooting
If HTTPS doesn't work:
1. Check that Proxy Status is ON (🟠) for both DNS records
2. Verify nameservers are updated at domain registrar
3. Wait longer for DNS propagation (up to 24 hours)
4. Clear browser cache and try again

## 📞 Support
If you need help with any step, just ask!

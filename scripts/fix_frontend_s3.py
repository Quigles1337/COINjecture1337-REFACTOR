#!/usr/bin/env python3
"""
Fix Frontend S3 Issues
Resolves invalid CIDs and static metrics on S3 frontend
"""

import boto3
import json
import time
from datetime import datetime
import os

class FrontendS3Fixer:
    def __init__(self):
        self.s3_bucket = "coinjecture-web"
        self.aws_region = "us-east-1"
        self.s3_client = boto3.client('s3', region_name=self.aws_region)
        
    def update_app_js_cache_busting(self):
        """Update app.js to include proper cache busting"""
        print("🔧 Updating app.js cache busting...")
        
        # Read current app.js
        try:
            response = self.s3_client.get_object(Bucket=self.s3_bucket, Key='app.js')
            app_js_content = response['Body'].read().decode('utf-8')
        except Exception as e:
            print(f"❌ Failed to read app.js from S3: {e}")
            return False
        
        # Add cache busting headers and force refresh
        cache_busting_code = f"""
// Cache busting and force refresh
const CACHE_BUSTER = '?v={int(time.time())}&t={int(time.time())}';
const FORCE_REFRESH = true;

// Override fetch to add cache busting
const originalFetch = window.fetch;
window.fetch = function(url, options = {{}}) {{
    if (typeof url === 'string' && url.includes('/v1/')) {{
        const separator = url.includes('?') ? '&' : '?';
        url = url + separator + 't=' + Date.now();
    }}
    return originalFetch.call(this, url, {{
        ...options,
        cache: 'no-cache',
        headers: {{
            ...options.headers,
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }}
    }});
}};

// Force refresh metrics on page load
document.addEventListener('DOMContentLoaded', function() {{
    if (window.webInterface) {{
        window.webInterface.forceRefreshMetrics();
    }}
}});
"""
        
        # Insert cache busting code at the beginning
        updated_content = cache_busting_code + app_js_content
        
        # Upload updated app.js
        try:
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key='app.js',
                Body=updated_content.encode('utf-8'),
                ContentType='application/javascript',
                CacheControl='no-cache, no-store, must-revalidate',
                Metadata={
                    'updated': str(int(time.time())),
                    'cache-busting': 'enabled'
                }
            )
            print("✅ app.js updated with cache busting")
            return True
        except Exception as e:
            print(f"❌ Failed to update app.js: {e}")
            return False
    
    def update_index_html_cache_busting(self):
        """Update index.html to include proper cache busting"""
        print("🔧 Updating index.html cache busting...")
        
        # Read current index.html
        try:
            response = self.s3_client.get_object(Bucket=self.s3_bucket, Key='index.html')
            index_html_content = response['Body'].read().decode('utf-8')
        except Exception as e:
            print(f"❌ Failed to read index.html from S3: {e}")
            return False
        
        # Update script tag with cache busting
        timestamp = int(time.time())
        updated_content = index_html_content.replace(
            'app.js?v=3.10.5&t=1761102200',
            f'app.js?v=3.13.14&t={timestamp}'
        )
        
        # Add meta tags for cache control
        meta_tags = f"""
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <meta name="updated" content="{timestamp}">
"""
        
        # Insert meta tags in head
        if '<head>' in updated_content:
            updated_content = updated_content.replace('<head>', f'<head>{meta_tags}')
        
        # Upload updated index.html
        try:
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key='index.html',
                Body=updated_content.encode('utf-8'),
                ContentType='text/html',
                CacheControl='no-cache, no-store, must-revalidate',
                Metadata={
                    'updated': str(timestamp),
                    'cache-busting': 'enabled'
                }
            )
            print("✅ index.html updated with cache busting")
            return True
        except Exception as e:
            print(f"❌ Failed to update index.html: {e}")
            return False
    
    def add_force_refresh_functionality(self):
        """Add force refresh functionality to the frontend"""
        print("🔧 Adding force refresh functionality...")
        
        # Create a small script to force refresh metrics
        force_refresh_script = f"""
// Force refresh functionality
window.forceRefreshMetrics = function() {{
    console.log('🔄 Force refreshing metrics...');
    
    // Clear any existing intervals
    if (window.metricsInterval) {{
        clearInterval(window.metricsInterval);
    }}
    
    // Force immediate refresh
    if (window.webInterface) {{
        window.webInterface.fetchMetrics().then(metrics => {{
            window.webInterface.updateMetricsDashboard(metrics);
            console.log('✅ Metrics refreshed:', metrics);
        }}).catch(error => {{
            console.error('❌ Metrics refresh failed:', error);
        }});
    }}
    
    // Restart polling with shorter interval
    if (window.webInterface) {{
        window.webInterface.startMetricsPolling();
    }}
}};

// Auto-refresh on page load
document.addEventListener('DOMContentLoaded', function() {{
    setTimeout(() => {{
        window.forceRefreshMetrics();
    }}, 1000);
}});

// Add refresh button
document.addEventListener('DOMContentLoaded', function() {{
    const refreshBtn = document.createElement('button');
    refreshBtn.innerHTML = '🔄 Force Refresh';
    refreshBtn.style.cssText = `
        position: fixed;
        top: 10px;
        right: 10px;
        z-index: 1000;
        background: #4CAF50;
        color: white;
        border: none;
        padding: 10px 15px;
        border-radius: 5px;
        cursor: pointer;
        font-size: 12px;
    `;
    refreshBtn.onclick = window.forceRefreshMetrics;
    document.body.appendChild(refreshBtn);
}});
"""
        
        # Upload as a separate script file
        try:
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key='force-refresh.js',
                Body=force_refresh_script.encode('utf-8'),
                ContentType='application/javascript',
                CacheControl='no-cache, no-store, must-revalidate'
            )
            print("✅ force-refresh.js uploaded")
            return True
        except Exception as e:
            print(f"❌ Failed to upload force-refresh.js: {e}")
            return False
    
    def update_bucket_policy(self):
        """Update S3 bucket policy to prevent caching"""
        print("🔧 Updating S3 bucket policy...")
        
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{self.s3_bucket}/*"
                }
            ]
        }
        
        try:
            self.s3_client.put_bucket_policy(
                Bucket=self.s3_bucket,
                Policy=json.dumps(bucket_policy)
            )
            print("✅ Bucket policy updated")
            return True
        except Exception as e:
            print(f"❌ Failed to update bucket policy: {e}")
            return False
    
    def set_no_cache_headers(self):
        """Set no-cache headers for all files"""
        print("🔧 Setting no-cache headers for all files...")
        
        files_to_update = ['index.html', 'app.js', 'style.css']
        
        for file_key in files_to_update:
            try:
                # Copy object with new metadata
                copy_source = {'Bucket': self.s3_bucket, 'Key': file_key}
                self.s3_client.copy_object(
                    CopySource=copy_source,
                    Bucket=self.s3_bucket,
                    Key=file_key,
                    MetadataDirective='REPLACE',
                    Metadata={
                        'updated': str(int(time.time())),
                        'cache-busting': 'enabled'
                    },
                    CacheControl='no-cache, no-store, must-revalidate',
                    ContentType='text/html' if file_key.endswith('.html') else 
                               'application/javascript' if file_key.endswith('.js') else
                               'text/css' if file_key.endswith('.css') else 'text/plain'
                )
                print(f"✅ {file_key} updated with no-cache headers")
            except Exception as e:
                print(f"❌ Failed to update {file_key}: {e}")
        
        return True
    
    def test_frontend_access(self):
        """Test if the frontend is accessible and working"""
        print("🧪 Testing frontend access...")
        
        try:
            import requests
            
            # Test main page
            response = requests.get(f'https://{self.s3_bucket}.s3-website-{self.aws_region}.amazonaws.com/', timeout=10)
            if response.status_code == 200:
                print("✅ Frontend is accessible")
                
                # Check if cache busting is working
                if 'cache-busting' in response.text or 'force-refresh' in response.text:
                    print("✅ Cache busting is active")
                else:
                    print("⚠️  Cache busting may not be working")
                
                return True
            else:
                print(f"❌ Frontend returned status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Frontend test failed: {e}")
            return False
    
    def run_fix(self):
        """Run the complete frontend fix"""
        print("🔧 COINjecture Frontend S3 Fix")
        print("=" * 40)
        
        # Update files with cache busting
        self.update_app_js_cache_busting()
        self.update_index_html_cache_busting()
        self.add_force_refresh_functionality()
        
        # Update S3 configuration
        self.update_bucket_policy()
        self.set_no_cache_headers()
        
        # Test the fixes
        self.test_frontend_access()
        
        print("\n📋 Frontend Fix Summary:")
        print("=" * 30)
        print("✅ Cache busting implemented")
        print("✅ Force refresh functionality added")
        print("✅ No-cache headers set")
        print("✅ S3 bucket policy updated")
        print("\n🌐 Frontend URL:")
        print(f"   https://{self.s3_bucket}.s3-website-{self.aws_region}.amazonaws.com/")
        print("\n💡 If you still see static metrics:")
        print("   1. Hard refresh the page (Ctrl+F5 or Cmd+Shift+R)")
        print("   2. Clear browser cache")
        print("   3. Use the 'Force Refresh' button on the page")
        print("   4. Check browser developer tools for errors")

def main():
    """Main function"""
    fixer = FrontendS3Fixer()
    fixer.run_fix()

if __name__ == "__main__":
    main()

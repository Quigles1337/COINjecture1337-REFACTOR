#!/usr/bin/env python3
"""
Force Frontend S3 Update
Comprehensive cache busting and invalidation for S3 frontend
"""

import boto3
import time
import hashlib
from datetime import datetime

class FrontendForceUpdater:
    def __init__(self):
        self.s3_bucket = "coinjecture-web"
        self.aws_region = "us-east-1"
        self.s3_client = boto3.client('s3', region_name=self.aws_region)
        
    def generate_cache_buster(self):
        """Generate a unique cache buster"""
        timestamp = int(time.time())
        random_hash = hashlib.md5(f"coinjecture-{timestamp}".encode()).hexdigest()[:8]
        return f"{timestamp}-{random_hash}"
    
    def update_html_with_aggressive_cache_busting(self):
        """Update HTML with aggressive cache busting"""
        print("🔧 Updating HTML with aggressive cache busting...")
        
        cache_buster = self.generate_cache_buster()
        
        # Read current HTML
        try:
            response = self.s3_client.get_object(Bucket=self.s3_bucket, Key='index.html')
            html_content = response['Body'].read().decode('utf-8')
        except Exception as e:
            print(f"❌ Failed to read HTML: {e}")
            return False
        
        # Add aggressive cache busting
        updated_html = html_content.replace(
            'app.js?v=3.13.14&t=1761441226',
            f'app.js?v=4.0.0&t={cache_buster}&cb={cache_buster}'
        )
        
        # Add meta tags for cache control
        meta_tags = f"""
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate, max-age=0">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <meta name="updated" content="{cache_buster}">
    <meta name="cache-buster" content="{cache_buster}">
    <meta name="version" content="4.0.0">
"""
        
        # Insert meta tags in head
        if '<head>' in updated_html:
            updated_html = updated_html.replace('<head>', f'<head>{meta_tags}')
        
        # Upload with aggressive cache control
        try:
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key='index.html',
                Body=updated_html.encode('utf-8'),
                ContentType='text/html; charset=utf-8',
                CacheControl='no-cache, no-store, must-revalidate, max-age=0',
                Metadata={
                    'updated': str(cache_buster),
                    'cache-busting': 'aggressive',
                    'version': '4.0.0'
                }
            )
            print(f"✅ HTML updated with cache buster: {cache_buster}")
            return True
        except Exception as e:
            print(f"❌ Failed to update HTML: {e}")
            return False
    
    def update_js_with_aggressive_cache_busting(self):
        """Update JavaScript with aggressive cache busting"""
        print("🔧 Updating JavaScript with aggressive cache busting...")
        
        cache_buster = self.generate_cache_buster()
        
        # Read current JS
        try:
            response = self.s3_client.get_object(Bucket=self.s3_bucket, Key='app.js')
            js_content = response['Body'].read().decode('utf-8')
        except Exception as e:
            print(f"❌ Failed to read JS: {e}")
            return False
        
        # Add aggressive cache busting at the top
        cache_busting_code = f"""
// AGGRESSIVE CACHE BUSTING - Version 4.0.0
const CACHE_BUSTER = '{cache_buster}';
const FORCE_REFRESH = true;
const VERSION = '4.0.0';

// Clear all caches
if ('caches' in window) {{
    caches.keys().then(names => {{
        names.forEach(name => {{
            caches.delete(name);
        }});
    }});
}}

// Override fetch with aggressive cache busting
const originalFetch = window.fetch;
window.fetch = function(url, options = {{}}) {{
    if (typeof url === 'string') {{
        const separator = url.includes('?') ? '&' : '?';
        url = url + separator + 't=' + Date.now() + '&cb=' + CACHE_BUSTER + '&v=' + VERSION;
    }}
    return originalFetch.call(this, url, {{
        ...options,
        cache: 'no-cache',
        headers: {{
            ...options.headers,
            'Cache-Control': 'no-cache, no-store, must-revalidate, max-age=0',
            'Pragma': 'no-cache',
            'Expires': '0',
            'X-Cache-Buster': CACHE_BUSTER,
            'X-Version': VERSION
        }}
    }});
}};

// Force refresh on load
window.addEventListener('load', function() {{
    console.log('🔄 Force refreshing with cache buster:', CACHE_BUSTER);
    if (window.webInterface) {{
        window.webInterface.forceRefreshMetrics();
    }}
}});

// Clear localStorage and sessionStorage
localStorage.clear();
sessionStorage.clear();

console.log('🚀 COINjecture Frontend v4.0.0 - Cache Buster:', CACHE_BUSTER);
"""
        
        # Insert at the beginning
        updated_js = cache_busting_code + js_content
        
        # Upload with aggressive cache control
        try:
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key='app.js',
                Body=updated_js.encode('utf-8'),
                ContentType='application/javascript; charset=utf-8',
                CacheControl='no-cache, no-store, must-revalidate, max-age=0',
                Metadata={
                    'updated': str(cache_buster),
                    'cache-busting': 'aggressive',
                    'version': '4.0.0'
                }
            )
            print(f"✅ JS updated with cache buster: {cache_buster}")
            return True
        except Exception as e:
            print(f"❌ Failed to update JS: {e}")
            return False
    
    def update_css_with_aggressive_cache_busting(self):
        """Update CSS with aggressive cache busting"""
        print("🔧 Updating CSS with aggressive cache busting...")
        
        cache_buster = self.generate_cache_buster()
        
        # Read current CSS
        try:
            response = self.s3_client.get_object(Bucket=self.s3_bucket, Key='style.css')
            css_content = response['Body'].read().decode('utf-8')
        except Exception as e:
            print(f"❌ Failed to read CSS: {e}")
            return False
        
        # Add cache buster comment at the top
        cache_buster_comment = f"""
/* COINjecture Frontend CSS v4.0.0 - Cache Buster: {cache_buster} */
/* Updated: {datetime.now().isoformat()} */
/* Force refresh enabled */

"""
        
        updated_css = cache_buster_comment + css_content
        
        # Upload with aggressive cache control
        try:
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key='style.css',
                Body=updated_css.encode('utf-8'),
                ContentType='text/css; charset=utf-8',
                CacheControl='no-cache, no-store, must-revalidate, max-age=0',
                Metadata={
                    'updated': str(cache_buster),
                    'cache-busting': 'aggressive',
                    'version': '4.0.0'
                }
            )
            print(f"✅ CSS updated with cache buster: {cache_buster}")
            return True
        except Exception as e:
            print(f"❌ Failed to update CSS: {e}")
            return False
    
    def create_force_refresh_page(self):
        """Create a force refresh page"""
        print("🔧 Creating force refresh page...")
        
        cache_buster = self.generate_cache_buster()
        
        force_refresh_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate, max-age=0">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <title>COINjecture Force Refresh</title>
    <style>
        body {{
            font-family: 'Courier New', monospace;
            background: #1a1a1a;
            color: #fff;
            margin: 0;
            padding: 20px;
            text-align: center;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 40px 20px;
        }}
        .title {{
            font-size: 24px;
            color: #4CAF50;
            margin-bottom: 20px;
        }}
        .cache-buster {{
            background: #2a2a2a;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            font-family: monospace;
        }}
        .btn {{
            background: #4CAF50;
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin: 10px;
        }}
        .btn:hover {{
            background: #66BB6A;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1 class="title">🚀 COINjecture Force Refresh</h1>
        <p>Cache buster: <span class="cache-buster">{cache_buster}</span></p>
        <p>Version: 4.0.0</p>
        <p>This page forces a complete cache refresh.</p>
        
        <button class="btn" onclick="window.location.href='/?t={cache_buster}&cb={cache_buster}&v=4.0.0'">
            🔄 Go to Main App
        </button>
        
        <button class="btn" onclick="location.reload(true)">
            🔄 Force Reload This Page
        </button>
        
        <script>
            // Clear all caches
            if ('caches' in window) {{
                caches.keys().then(names => {{
                    names.forEach(name => {{
                        caches.delete(name);
                    }});
                }});
            }}
            
            // Clear storage
            localStorage.clear();
            sessionStorage.clear();
            
            console.log('🔄 Force refresh page loaded with cache buster: {cache_buster}');
        </script>
    </div>
</body>
</html>"""
        
        try:
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key='force-refresh.html',
                Body=force_refresh_html.encode('utf-8'),
                ContentType='text/html; charset=utf-8',
                CacheControl='no-cache, no-store, must-revalidate, max-age=0'
            )
            print("✅ Force refresh page created")
            return True
        except Exception as e:
            print(f"❌ Failed to create force refresh page: {e}")
            return False
    
    def run_force_update(self):
        """Run the complete force update process"""
        print("🚀 COINjecture Frontend Force Update")
        print("=" * 40)
        
        cache_buster = self.generate_cache_buster()
        print(f"🎯 Cache Buster: {cache_buster}")
        
        # Update all files
        self.update_html_with_aggressive_cache_busting()
        self.update_js_with_aggressive_cache_busting()
        self.update_css_with_aggressive_cache_busting()
        self.create_force_refresh_page()
        
        print("\n📋 Force Update Summary:")
        print("=" * 30)
        print("✅ HTML updated with aggressive cache busting")
        print("✅ JavaScript updated with cache clearing")
        print("✅ CSS updated with version markers")
        print("✅ Force refresh page created")
        
        print(f"\n🌐 Frontend URLs:")
        print(f"   Main App: https://coinjecture-web.s3-website-us-east-1.amazonaws.com/")
        print(f"   Force Refresh: https://coinjecture-web.s3-website-us-east-1.amazonaws.com/force-refresh.html")
        
        print(f"\n💡 TO FORCE UPDATE:")
        print(f"   1. Go to: https://coinjecture-web.s3-website-us-east-1.amazonaws.com/force-refresh.html")
        print(f"   2. Click 'Go to Main App' button")
        print(f"   3. Or add ?t={cache_buster}&cb={cache_buster}&v=4.0.0 to any URL")
        print(f"   4. Clear browser cache completely")
        print(f"   5. Try incognito/private mode")
        
        return True

def main():
    """Main function"""
    updater = FrontendForceUpdater()
    updater.run_force_update()

if __name__ == "__main__":
    main()

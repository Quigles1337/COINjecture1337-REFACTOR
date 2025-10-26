#!/bin/bash

# Manual Droplet Cache-Bust Fix
# Run this script directly on the droplet to fix the cache-bust issue

set -e

echo "🔧 Manual Droplet Cache-Bust Fix"
echo "================================="
echo "Run this script directly on your droplet:"
echo "ssh coinjecture@167.172.213.70"
echo "curl -s https://raw.githubusercontent.com/beanapologist/COINjecture/main/scripts/manual_droplet_fix.sh | bash"
echo ""

echo "🔍 Checking current status..."
echo "================================"

# Check if cache-bust files exist
echo "📁 Checking for cache-bust files:"
ls -la /home/coinjecture/COINjecture/web/ | grep -E "(cache-bust|index\.html)" || echo "No cache-bust files found"

echo ""
echo "🔍 Checking current index.html content:"
if [ -f "/home/coinjecture/COINjecture/web/index.html" ]; then
    echo "Current index.html has cache-bust references:"
    grep -c "cache-bust" /home/coinjecture/COINjecture/web/index.html || echo "0 cache-bust references found"
else
    echo "index.html not found"
fi

echo ""
echo "🧹 Removing cache-bust files and references..."

# Remove cache-bust.js file if it exists
if [ -f "/home/coinjecture/COINjecture/web/cache-bust.js" ]; then
    echo "🗑️  Removing cache-bust.js file..."
    rm -f /home/coinjecture/COINjecture/web/cache-bust.js
    echo "✅ cache-bust.js removed"
else
    echo "ℹ️  cache-bust.js not found"
fi

# Remove cache-bust references from index.html
if [ -f "/home/coinjecture/COINjecture/web/index.html" ]; then
    echo "🧹 Cleaning index.html from cache-bust references..."
    
    # Create a backup
    cp /home/coinjecture/COINjecture/web/index.html /home/coinjecture/COINjecture/web/index.html.backup
    
    # Remove cache-bust meta tags and script references
    sed -i '/<meta name="cache-bust"/d' /home/coinjecture/COINjecture/web/index.html
    sed -i '/<meta http-equiv="Cache-Control"/d' /home/coinjecture/COINjecture/web/index.html
    sed -i '/<meta http-equiv="Pragma"/d' /home/coinjecture/COINjecture/web/index.html
    sed -i '/<meta http-equiv="Expires"/d' /home/coinjecture/COINjecture/web/index.html
    sed -i '/<script src="cache-bust.js/d' /home/coinjecture/COINjecture/web/index.html
    
    echo "✅ Cache-bust references removed from index.html"
else
    echo "ℹ️  index.html not found"
fi

# Remove any other cache-bust related files
echo "🧹 Removing other cache-bust related files..."
rm -f /home/coinjecture/COINjecture/web/cache-bust.js*
rm -f /home/coinjecture/COINjecture/web/*cache-bust*

echo ""
echo "🔄 Restarting Nginx to clear any cached configurations..."
sudo systemctl restart nginx
echo "✅ Nginx restarted"

echo ""
echo "🧪 Testing the fix..."
echo "===================="

# Test if cache-bust references are gone
if [ -f "/home/coinjecture/COINjecture/web/index.html" ]; then
    CACHE_BUST_COUNT=$(grep -c "cache-bust" /home/coinjecture/COINjecture/web/index.html || echo "0")
    echo "📊 Cache-bust references in index.html: $CACHE_BUST_COUNT"
    
    if [ "$CACHE_BUST_COUNT" -eq 0 ]; then
        echo "✅ SUCCESS: No cache-bust references found!"
    else
        echo "⚠️  WARNING: Still found $CACHE_BUST_COUNT cache-bust references"
        echo "🔍 Remaining references:"
        grep "cache-bust" /home/coinjecture/COINjecture/web/index.html || echo "None found"
    fi
else
    echo "❌ index.html not found after cleanup"
fi

echo ""
echo "🌐 Testing HTTP response..."
curl -s http://localhost/ | grep -c "cache-bust" || echo "0"

echo ""
echo "🔍 Final status check:"
echo "====================="
echo "📁 Files in web directory:"
ls -la /home/coinjecture/COINjecture/web/ | grep -E "(index|cache)" || echo "No index or cache files found"

echo ""
echo "✅ Droplet cache-bust fix completed!"
echo "🌐 Test the frontend at: https://coinjecture.com"

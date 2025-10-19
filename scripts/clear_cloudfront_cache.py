#!/usr/bin/env python3
"""
Clear CloudFront cache to force fresh content delivery
"""

import boto3
import sys
import logging
from botocore.exceptions import ClientError

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clear_cloudfront_cache():
    """Clear CloudFront cache for coinjecture.com"""
    
    logger.info("=== Clear CloudFront Cache ===")
    
    try:
        # Initialize CloudFront client
        cloudfront = boto3.client('cloudfront')
        
        # List all distributions to find coinjecture.com
        logger.info("Finding CloudFront distribution for coinjecture.com...")
        
        distributions = cloudfront.list_distributions()
        coinjecture_distribution = None
        
        for distribution in distributions['DistributionList']['Items']:
            if 'coinjecture.com' in distribution['DomainName'] or 'coinjecture.com' in distribution['Origins']['Items'][0]['DomainName']:
                coinjecture_distribution = distribution
                break
        
        if not coinjecture_distribution:
            logger.error("❌ Could not find CloudFront distribution for coinjecture.com")
            logger.info("Available distributions:")
            for dist in distributions['DistributionList']['Items']:
                logger.info(f"  - {dist['DomainName']} (ID: {dist['Id']})")
            return False
        
        distribution_id = coinjecture_distribution['Id']
        domain_name = coinjecture_distribution['DomainName']
        
        logger.info(f"Found distribution: {domain_name} (ID: {distribution_id})")
        
        # Create invalidation for all paths
        paths_to_invalidate = [
            '/*',  # Invalidate all content
            '/index.html',
            '/app.js',
            '/style.css',
            '/cache-bust.js',
            '/clear-cache.html'
        ]
        
        logger.info("Creating CloudFront invalidation...")
        
        response = cloudfront.create_invalidation(
            DistributionId=distribution_id,
            InvalidationBatch={
                'Paths': {
                    'Quantity': len(paths_to_invalidate),
                    'Items': paths_to_invalidate
                },
                'CallerReference': f'cache-clear-{int(__import__("time").time())}'
            }
        )
        
        invalidation_id = response['Invalidation']['Id']
        logger.info(f"✅ CloudFront invalidation created: {invalidation_id}")
        logger.info("This may take 5-15 minutes to complete globally")
        
        # Check invalidation status
        logger.info("Checking invalidation status...")
        invalidation = cloudfront.get_invalidation(
            DistributionId=distribution_id,
            Id=invalidation_id
        )
        
        status = invalidation['Invalidation']['Status']
        logger.info(f"Invalidation status: {status}")
        
        if status == 'InProgress':
            logger.info("✅ Invalidation is in progress - cache will be cleared soon")
        elif status == 'Completed':
            logger.info("✅ Invalidation completed - cache has been cleared")
        
        return True
        
    except ClientError as e:
        logger.error(f"❌ AWS Client Error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error clearing CloudFront cache: {e}")
        return False

def clear_cloudfront_cache_manual():
    """Manual CloudFront cache clearing instructions"""
    
    logger.info("=== Manual CloudFront Cache Clear ===")
    logger.info("If automatic clearing fails, you can manually clear CloudFront cache:")
    logger.info("")
    logger.info("1. Go to AWS CloudFront Console:")
    logger.info("   https://console.aws.amazon.com/cloudfront/")
    logger.info("")
    logger.info("2. Find the distribution for coinjecture.com")
    logger.info("")
    logger.info("3. Click on the distribution ID")
    logger.info("")
    logger.info("4. Go to 'Invalidations' tab")
    logger.info("")
    logger.info("5. Click 'Create Invalidation'")
    logger.info("")
    logger.info("6. Enter these paths (one per line):")
    logger.info("   /*")
    logger.info("   /index.html")
    logger.info("   /app.js")
    logger.info("   /style.css")
    logger.info("   /cache-bust.js")
    logger.info("   /clear-cache.html")
    logger.info("")
    logger.info("7. Click 'Create Invalidation'")
    logger.info("")
    logger.info("8. Wait 5-15 minutes for global cache clearing")

if __name__ == "__main__":
    print("🌐 CloudFront Cache Clear for COINjecture")
    print("=" * 50)
    
    try:
        success = clear_cloudfront_cache()
        if success:
            print("✅ CloudFront cache clearing initiated successfully")
            print("⏳ Cache clearing may take 5-15 minutes to complete globally")
            print("🔄 Users should see fresh content after cache clearing completes")
        else:
            print("❌ Failed to clear CloudFront cache automatically")
            print("📋 Manual instructions:")
            clear_cloudfront_cache_manual()
    except ImportError:
        print("❌ boto3 not installed. Installing...")
        import subprocess
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'boto3'])
        print("✅ boto3 installed. Please run the script again.")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("📋 Manual instructions:")
        clear_cloudfront_cache_manual()
        sys.exit(1)

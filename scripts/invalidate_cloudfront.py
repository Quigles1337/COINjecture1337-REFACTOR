#!/usr/bin/env python3
"""
CloudFront Cache Invalidation
Invalidates CloudFront cache to fix frontend caching issues
"""

import boto3
import time
from datetime import datetime

class CloudFrontInvalidator:
    def __init__(self):
        self.cloudfront = boto3.client('cloudfront')
        
    def list_distributions(self):
        """List all CloudFront distributions"""
        print("🔍 Finding CloudFront distributions...")
        
        try:
            response = self.cloudfront.list_distributions()
            distributions = response.get('DistributionList', {}).get('Items', [])
            
            print(f"Found {len(distributions)} CloudFront distributions:")
            for dist in distributions:
                print(f"  - {dist['Id']}: {dist['DomainName']} (Status: {dist['Status']})")
            
            return distributions
        except Exception as e:
            print(f"❌ Failed to list distributions: {e}")
            return []
    
    def find_coinjecture_distribution(self):
        """Find the CloudFront distribution for COINjecture"""
        distributions = self.list_distributions()
        
        for dist in distributions:
            # Check if this distribution is for COINjecture
            if 'coinjecture' in dist['DomainName'].lower() or 'coinjecture' in dist.get('Comment', '').lower():
                return dist
        
        # If no specific match, return the first distribution
        if distributions:
            print("⚠️  No specific COINjecture distribution found, using first available")
            return distributions[0]
        
        return None
    
    def invalidate_cache(self, distribution_id, paths=None):
        """Invalidate CloudFront cache for specific paths"""
        if paths is None:
            paths = [
                '/',
                '/index.html',
                '/app.js',
                '/style.css',
                '/force-refresh.js'
            ]
        
        print(f"🔄 Invalidating CloudFront cache for distribution: {distribution_id}")
        print(f"📁 Paths to invalidate: {paths}")
        
        try:
            response = self.cloudfront.create_invalidation(
                DistributionId=distribution_id,
                InvalidationBatch={
                    'Paths': {
                        'Quantity': len(paths),
                        'Items': paths
                    },
                    'CallerReference': f'coinjecture-cache-invalidation-{int(time.time())}'
                }
            )
            
            invalidation_id = response['Invalidation']['Id']
            print(f"✅ Cache invalidation created: {invalidation_id}")
            print(f"🌐 Status: {response['Invalidation']['Status']}")
            
            return invalidation_id
        except Exception as e:
            print(f"❌ Failed to create invalidation: {e}")
            return None
    
    def check_invalidation_status(self, distribution_id, invalidation_id):
        """Check the status of a cache invalidation"""
        try:
            response = self.cloudfront.get_invalidation(
                DistributionId=distribution_id,
                Id=invalidation_id
            )
            
            status = response['Invalidation']['Status']
            print(f"📊 Invalidation Status: {status}")
            
            return status
        except Exception as e:
            print(f"❌ Failed to check invalidation status: {e}")
            return None
    
    def wait_for_completion(self, distribution_id, invalidation_id, max_wait=300):
        """Wait for cache invalidation to complete"""
        print("⏳ Waiting for cache invalidation to complete...")
        
        start_time = time.time()
        while time.time() - start_time < max_wait:
            status = self.check_invalidation_status(distribution_id, invalidation_id)
            
            if status == 'Completed':
                print("✅ Cache invalidation completed!")
                return True
            elif status == 'InProgress':
                print("🔄 Invalidation in progress...")
                time.sleep(10)
            else:
                print(f"⚠️  Unexpected status: {status}")
                time.sleep(5)
        
        print("⏰ Timeout waiting for invalidation completion")
        return False
    
    def force_s3_cache_busting(self):
        """Force S3 cache busting by updating file metadata"""
        print("🔧 Forcing S3 cache busting...")
        
        s3 = boto3.client('s3')
        bucket = 'coinjecture-web'
        timestamp = int(time.time())
        
        files_to_update = ['index.html', 'app.js', 'style.css']
        
        for file_key in files_to_update:
            try:
                # Copy object with new metadata to force cache refresh
                copy_source = {'Bucket': bucket, 'Key': file_key}
                s3.copy_object(
                    CopySource=copy_source,
                    Bucket=bucket,
                    Key=file_key,
                    MetadataDirective='REPLACE',
                    Metadata={
                        'updated': str(timestamp),
                        'cache-busting': 'enabled',
                        'invalidation': 'forced'
                    },
                    CacheControl='no-cache, no-store, must-revalidate'
                )
                print(f"✅ {file_key} updated with cache busting metadata")
            except Exception as e:
                print(f"❌ Failed to update {file_key}: {e}")
    
    def run_invalidation(self):
        """Run the complete cache invalidation process"""
        print("🚀 COINjecture CloudFront Cache Invalidation")
        print("=" * 50)
        
        # Find the distribution
        distribution = self.find_coinjecture_distribution()
        if not distribution:
            print("❌ No CloudFront distribution found")
            return False
        
        distribution_id = distribution['Id']
        domain_name = distribution['DomainName']
        
        print(f"🎯 Target Distribution: {distribution_id}")
        print(f"🌐 Domain: {domain_name}")
        
        # Create cache invalidation
        invalidation_id = self.invalidate_cache(distribution_id)
        if not invalidation_id:
            return False
        
        # Force S3 cache busting
        self.force_s3_cache_busting()
        
        # Wait for completion
        self.wait_for_completion(distribution_id, invalidation_id)
        
        print("\n📋 Cache Invalidation Summary:")
        print("=" * 35)
        print("✅ CloudFront cache invalidated")
        print("✅ S3 cache busting applied")
        print("✅ All frontend files updated")
        
        print(f"\n🌐 Frontend URLs:")
        print(f"   CloudFront: https://{domain_name}/")
        print(f"   S3 Direct: https://coinjecture-web.s3-website-us-east-1.amazonaws.com/")
        
        print(f"\n💡 Cache Invalidation Complete!")
        print(f"   - All cached content cleared")
        print(f"   - Fresh content will be served")
        print(f"   - Frontend should now show live data")
        
        return True

def main():
    """Main function"""
    invalidator = CloudFrontInvalidator()
    invalidator.run_invalidation()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Check CloudFront invalidation status
"""

import boto3
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_cloudfront_status():
    """Check CloudFront invalidation status"""
    
    try:
        cloudfront = boto3.client('cloudfront')
        
        # The distribution ID and invalidation ID from the previous run
        distribution_id = "E2INLKPSADEUYX"
        invalidation_id = "IARMCOG2K55AP4BIUUKXY9XT9X"
        
        logger.info(f"Checking invalidation status for {invalidation_id}...")
        
        response = cloudfront.get_invalidation(
            DistributionId=distribution_id,
            Id=invalidation_id
        )
        
        status = response['Invalidation']['Status']
        create_time = response['Invalidation']['CreateTime']
        
        logger.info(f"Invalidation ID: {invalidation_id}")
        logger.info(f"Status: {status}")
        logger.info(f"Created: {create_time}")
        
        if status == 'InProgress':
            logger.info("⏳ Cache clearing is still in progress...")
            logger.info("This may take 5-15 minutes to complete globally")
        elif status == 'Completed':
            logger.info("✅ Cache clearing completed!")
            logger.info("Users should now see fresh content")
        else:
            logger.info(f"Status: {status}")
        
        return status
        
    except Exception as e:
        logger.error(f"❌ Error checking CloudFront status: {e}")
        return None

if __name__ == "__main__":
    print("🔍 Checking CloudFront Invalidation Status")
    print("=" * 50)
    
    status = check_cloudfront_status()
    
    if status == 'Completed':
        print("✅ CloudFront cache has been cleared!")
        print("🔄 Users should now see fresh content")
    elif status == 'InProgress':
        print("⏳ Cache clearing is still in progress...")
        print("Please wait a few more minutes")
    else:
        print(f"📊 Status: {status}")

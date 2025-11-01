"""Test script for Price Optimizer with Data Collector integration"""
import asyncio
import logging
from pathlib import Path

from core.agents.price_optimizer.tools import Tools

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_integration")


async def test_integration():
    """Test the integrated workflow: check freshness, trigger collection, and optimize."""
    
    root = Path(__file__).resolve().parent
    app_db = root / "app" / "data.db"
    market_db = root / "data" / "market.db"
    
    tools = Tools(app_db, market_db)
    sku = "ASUS-ProArt-4910S"
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Testing Price Optimizer Integration for {sku}")
    logger.info(f"{'='*60}\n")
    
    # Step 1: Check market data freshness
    logger.info("Step 1: Checking market data freshness...")
    freshness = await tools.check_market_data_freshness(sku)
    logger.info(f"Freshness result: {freshness}")
    
    if freshness.get("ok"):
        is_stale = freshness.get("is_stale")
        has_data = freshness.get("has_data")
        
        if is_stale or not has_data:
            logger.info(f"\n⚠️  Market data is {'stale' if is_stale else 'missing'}!")
            logger.info(f"   Last update: {freshness.get('last_update', 'Never')}")
            logger.info(f"   Minutes stale: {freshness.get('minutes_stale', 'N/A')}")
            logger.info(f"   Market data count: {freshness.get('market_data_count', 0)}")
            
            # Step 2: Trigger data collection
            logger.info("\nStep 2: Triggering market data collection...")
            collection = await tools.start_market_data_collection(sku)
            logger.info(f"Collection result: {collection}")
            
            if collection.get("ok"):
                logger.info(f"\n✓ Market data collection started!")
                logger.info(f"   Request ID: {collection.get('request_id')}")
                logger.info(f"   Connector: {collection.get('connector')}")
                logger.info(f"   Has source URL: {collection.get('has_source_url')}")
                
                # Wait a bit for collection to complete (in real scenario, this would be async)
                logger.info("\n   Waiting 5 seconds for data collection...")
                await asyncio.sleep(5)
        else:
            logger.info(f"\n✓ Market data is fresh!")
            logger.info(f"   Last update: {freshness.get('last_update')}")
            logger.info(f"   Minutes stale: {freshness.get('minutes_stale')}")
    
    # Step 3: Get product info
    logger.info("\nStep 3: Getting product information...")
    product_info = await tools.get_product_info(sku)
    logger.info(f"Product info: {product_info}")
    
    if not product_info.get("ok"):
        logger.error(f"Failed to get product info: {product_info.get('error')}")
        return
    
    # Step 4: Get market intelligence
    logger.info("\nStep 4: Getting market intelligence...")
    title = product_info["title"]
    market_intel = await tools.get_market_intelligence(title)
    logger.info(f"Market intelligence: {market_intel}")
    
    # Step 5: Run pricing algorithm
    logger.info("\nStep 5: Running pricing algorithm...")
    algo_result = await tools.run_pricing_algorithm(
        algorithm="rule_based",
        sku=sku,
        our_price=product_info["current_price"],
        competitor_price=market_intel.get("competitor_price"),
        cost=product_info.get("cost"),
        market_records=market_intel.get("market_records", []),
        min_margin=0.12,
    )
    logger.info(f"Algorithm result: {algo_result}")
    
    if algo_result.get("ok"):
        recommended_price = algo_result["recommended_price"]
        logger.info(f"\n✓ Price optimization completed!")
        logger.info(f"   Current price: LKR {product_info['current_price']:.2f}")
        logger.info(f"   Recommended price: LKR {recommended_price:.2f}")
        logger.info(f"   Confidence: {algo_result.get('confidence', 0.0):.2%}")
        logger.info(f"   Rationale: {algo_result.get('rationale', 'N/A')}")
    
    logger.info(f"\n{'='*60}")
    logger.info("Integration test completed!")
    logger.info(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(test_integration())

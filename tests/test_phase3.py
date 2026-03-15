"""
Test script for Phase 3 implementation.

This script tests the basic functionality of the Phase 3 components.
"""

import os
import sys
import json
import time
import asyncio
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_phase3")

# Import Phase 3 integration
from phase3_integration import Phase3Integration

async def test_phase3():
    """Test Phase 3 implementation"""
    logger.info("Starting Phase 3 test...")
    
    # Create necessary directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("configs", exist_ok=True)
    os.makedirs("reports/regulatory", exist_ok=True)
    
    # Initialize Phase 3 integration
    integration = Phase3Integration("phase3_config.json")
    
    try:
        # Start integration
        logger.info("Initializing components...")
        await integration.initialize_components()
        
        logger.info("Starting integration...")
        await integration.start()
        
        # Get status
        logger.info("Getting status...")
        status = await integration.get_status()
        logger.info(f"Integration status: {json.dumps(status, indent=2)}")
        
        # Test bridge protocol
        if integration.bridge_protocol:
            logger.info("Testing bridge protocol...")
            bridge_status = integration.bridge_protocol.get_bridge_status()
            logger.info(f"Bridge status: {bridge_status}")
            
            # Test sending a cross-chain message
            try:
                message_id = await integration.bridge_protocol.send_cross_chain_message(
                    source_chain_id=1,  # Ethereum
                    destination_chain_id=56,  # BSC
                    message_type=integration.bridge_protocol.MessageType.DATA_MESSAGE,
                    payload={"data": "Test message from Ethereum to BSC"}
                )
                logger.info(f"Sent cross-chain message with ID: {message_id}")
            except Exception as e:
                logger.error(f"Error sending cross-chain message: {e}")
        
        # Test MEV protection
        if integration.mev_protection:
            logger.info("Testing MEV protection...")
            protection_status = integration.mev_protection.get_protection_status()
            logger.info(f"MEV protection status: {protection_status}")
        
        # Test atomic arbitrage
        if integration.atomic_arbitrage:
            logger.info("Testing atomic arbitrage...")
            arbitrage_status = integration.atomic_arbitrage.get_arbitrage_status()
            logger.info(f"Arbitrage status: {arbitrage_status}")
            
            # Get recent opportunities
            opportunities = integration.atomic_arbitrage.get_recent_opportunities(limit=3)
            logger.info(f"Recent opportunities: {opportunities}")
        
        # Test transaction monitoring
        if integration.transaction_monitoring:
            logger.info("Testing transaction monitoring...")
            stats = integration.transaction_monitoring.get_compliance_statistics()
            logger.info(f"Compliance statistics: {stats}")
            
            # Process a test transaction
            transaction = {
                "transaction_id": "test_tx_001",
                "blockchain": "ethereum",
                "tx_hash": "${CONTRACT_ADDRESS}90abcdef1234567890abcdef",
                "from_address": "${CONTRACT_ADDRESS}",
                "to_address": "${CONTRACT_ADDRESS}",
                "token": "ETH",
                "amount": 10.0,
                "amount_usd": 30000.0,  # High value to trigger alert
                "timestamp": int(time.time()),
                "block_number": 12345678,
                "gas_used": 21000,
                "gas_price": 50 * 10**9,  # 50 gwei
                "status": "confirmed",
                "metadata": {"test": True}
            }
            
            try:
                alerts = await integration.transaction_monitoring.process_transaction(transaction)
                logger.info(f"Processed test transaction, generated {len(alerts)} alerts")
            except Exception as e:
                logger.error(f"Error processing test transaction: {e}")
        
        # Test regulatory reporting
        if integration.regulatory_reporting:
            logger.info("Testing regulatory reporting...")
            reporting_stats = integration.regulatory_reporting.get_reporting_statistics()
            logger.info(f"Reporting statistics: {reporting_stats}")
            
            # Generate a test report
            template_ids = list(integration.regulatory_reporting.templates.keys())
            if template_ids:
                template_id = template_ids[0]
                try:
                    report_id = await integration.regulatory_reporting.generate_on_demand_report(
                        template_id=template_id,
                        parameters={
                            "generated_by": "test_script",
                            "test": True,
                            "date_range": {
                                "start_date": "2023-01-01",
                                "end_date": "2023-01-31"
                            }
                        }
                    )
                    logger.info(f"Generated test report with ID: {report_id}")
                except Exception as e:
                    logger.error(f"Error generating test report: {e}")
        
        # Test AML/KYC integration
        if integration.aml_kyc_integration:
            logger.info("Testing AML/KYC integration...")
            aml_kyc_stats = integration.aml_kyc_integration.get_aml_kyc_statistics()
            logger.info(f"AML/KYC statistics: {aml_kyc_stats}")
            
            # Create a test user
            try:
                user_id = await integration.aml_kyc_integration.create_user({
                    "email": "test@example.com",
                    "first_name": "Test",
                    "last_name": "User",
                    "date_of_birth": "1990-01-01",
                    "nationality": "US",
                    "country_of_residence": "US",
                    "address": {
                        "street": "123 Test St",
                        "city": "Test City",
                        "state": "TS",
                        "postal_code": "12345",
                        "country": "US"
                    },
                    "phone_number": "+11234567890"
                })
                logger.info(f"Created test user with ID: {user_id}")
                
                # Screen the user
                if user_id:
                    screening_id = await integration.aml_kyc_integration.screen_user(
                        user_id=user_id,
                        screening_type="sanctions"
                    )
                    logger.info(f"Screened test user, screening ID: {screening_id}")
            except Exception as e:
                logger.error(f"Error in AML/KYC test: {e}")
        
        # Run for a short time to allow background tasks to process
        logger.info("Running for 10 seconds to allow background tasks to process...")
        await asyncio.sleep(10)
        
        # Get final status
        final_status = await integration.get_status()
        logger.info(f"Final integration status: {json.dumps(final_status, indent=2)}")
        
        logger.info("Phase 3 test completed successfully")
    
    except Exception as e:
        logger.error(f"Error in Phase 3 test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Stop integration
        logger.info("Stopping integration...")
        await integration.stop()
        logger.info("Integration stopped")


if __name__ == "__main__":
    asyncio.run(test_phase3())
#!/usr/bin/env python3
"""
Comprehensive Test Suite for AI Nautilus Trader
==============================================

This script tests all components and error handling improvements.
"""

import asyncio
import sys
import traceback
from datetime import datetime
from typing import Dict, Any

# Import our modules
try:
    import ai_nautilus_trader
    from ai_nautilus_trader import AITradingSystem
    from ai_nautilus_trader.api import TradingAPI, TradingEndpoints
    from ai_nautilus_trader.config import Settings
    from ai_nautilus_trader.utils.logger import get_logger
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

logger = get_logger(__name__)


class ComprehensiveTestSuite:
    """Comprehensive test suite for all components."""
    
    def __init__(self):
        """Initialize test suite."""
        self.test_results = {}
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    def log_test_result(self, test_name: str, success: bool, error: str = None):
        """Log test result."""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            logger.info(f"✅ {test_name}: PASSED")
        else:
            self.failed_tests += 1
            logger.error(f"❌ {test_name}: FAILED - {error}")
        
        self.test_results[test_name] = {
            "success": success,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
    
    async def test_package_import(self):
        """Test package import and basic functionality."""
        try:
            version = ai_nautilus_trader.get_version()
            assert version == "1.0.0", f"Expected version 1.0.0, got {version}"
            
            # Test installation check
            ai_nautilus_trader.check_installation()
            
            self.log_test_result("Package Import", True)
            
        except Exception as e:
            self.log_test_result("Package Import", False, str(e))
    
    async def test_configuration(self):
        """Test configuration system."""
        try:
            # Test default configuration
            settings = Settings()
            assert settings is not None, "Settings initialization failed"
            
            # Test configuration validation
            config_dict = settings.to_dict()
            assert isinstance(config_dict, dict), "Configuration should be a dictionary"
            assert "system" in config_dict, "Missing system configuration"
            
            self.log_test_result("Configuration System", True)
            
        except Exception as e:
            self.log_test_result("Configuration System", False, str(e))
    
    async def test_trading_system_initialization(self):
        """Test trading system initialization."""
        try:
            system = AITradingSystem()
            assert system is not None, "Trading system initialization failed"
            assert not system.is_running, "System should not be running initially"
            
            self.log_test_result("Trading System Initialization", True)
            
        except Exception as e:
            self.log_test_result("Trading System Initialization", False, str(e))
    
    async def test_trading_system_start_stop(self):
        """Test trading system start/stop with error handling."""
        try:
            system = AITradingSystem()
            
            # Test start
            await system.start()
            assert system.is_running, "System should be running after start"
            
            # Test status
            status = system.get_status()
            assert isinstance(status, dict), "Status should be a dictionary"
            assert status["running"] is True, "Status should show running"
            
            # Test stop
            await system.stop()
            assert not system.is_running, "System should not be running after stop"
            
            self.log_test_result("Trading System Start/Stop", True)
            
        except Exception as e:
            self.log_test_result("Trading System Start/Stop", False, str(e))
    
    async def test_api_server(self):
        """Test API server functionality."""
        try:
            # Test API initialization
            api = TradingAPI()
            assert api is not None, "API initialization failed"
            
            # Test endpoints
            endpoints = TradingEndpoints(api)
            assert endpoints is not None, "Endpoints initialization failed"
            
            # Test status endpoint
            status = endpoints.get_status()
            assert isinstance(status, dict), "Status should be a dictionary"
            assert "status" in status, "Status should contain status field"
            
            # Test health endpoint
            health = endpoints.get_health()
            assert isinstance(health, dict), "Health should be a dictionary"
            assert "healthy" in health, "Health should contain healthy field"
            
            self.log_test_result("API Server", True)
            
        except Exception as e:
            self.log_test_result("API Server", False, str(e))
    
    async def test_error_handling(self):
        """Test error handling and recovery."""
        try:
            system = AITradingSystem()
            
            # Test multiple start calls (should handle gracefully)
            await system.start()
            await system.start()  # Should not fail
            
            # Test multiple stop calls (should handle gracefully)
            await system.stop()
            await system.stop()  # Should not fail
            
            self.log_test_result("Error Handling", True)
            
        except Exception as e:
            self.log_test_result("Error Handling", False, str(e))
    
    async def test_adapter_initialization(self):
        """Test adapter initialization with fallbacks."""
        try:
            from ai_nautilus_trader.adapters.real_crewai_adapter import RealCrewAIAdapter
            from ai_nautilus_trader.adapters.real_nautilus_adapter import RealNautilusAdapter
            
            # Test CrewAI adapter
            crewai_adapter = RealCrewAIAdapter()
            assert crewai_adapter is not None, "CrewAI adapter initialization failed"
            
            # Test Nautilus adapter
            nautilus_adapter = RealNautilusAdapter()
            assert nautilus_adapter is not None, "Nautilus adapter initialization failed"
            
            self.log_test_result("Adapter Initialization", True)
            
        except Exception as e:
            self.log_test_result("Adapter Initialization", False, str(e))
    
    async def test_agent_creation_with_fallbacks(self):
        """Test agent creation with fallback handling."""
        try:
            from ai_nautilus_trader.adapters.real_crewai_adapter import RealCrewAIAdapter
            
            adapter = RealCrewAIAdapter()
            
            # Test market analyst creation (should work or fallback gracefully)
            analyst = adapter.create_real_market_analyst()
            assert analyst is not None, "Market analyst creation failed"
            
            # Test risk manager creation (should work or fallback gracefully)
            risk_manager = adapter.create_real_risk_manager()
            assert risk_manager is not None, "Risk manager creation failed"
            
            self.log_test_result("Agent Creation with Fallbacks", True)
            
        except Exception as e:
            self.log_test_result("Agent Creation with Fallbacks", False, str(e))
    
    async def test_integration_flow(self):
        """Test complete integration flow."""
        try:
            # Create system
            system = AITradingSystem()
            
            # Start system
            await system.start()
            
            # Verify components are running
            status = system.get_status()
            assert status["running"] is True, "System should be running"
            
            # Test API integration
            api = TradingAPI()
            await api.initialize()
            
            # Stop system
            await system.stop()
            
            self.log_test_result("Integration Flow", True)
            
        except Exception as e:
            self.log_test_result("Integration Flow", False, str(e))
    
    async def run_all_tests(self):
        """Run all tests."""
        logger.info("🧪 Starting Comprehensive Test Suite")
        logger.info("=" * 60)
        
        # List of all tests
        tests = [
            self.test_package_import,
            self.test_configuration,
            self.test_trading_system_initialization,
            self.test_trading_system_start_stop,
            self.test_api_server,
            self.test_error_handling,
            self.test_adapter_initialization,
            self.test_agent_creation_with_fallbacks,
            self.test_integration_flow,
        ]
        
        # Run each test
        for test in tests:
            try:
                await test()
            except Exception as e:
                logger.error(f"❌ Test {test.__name__} failed with exception: {e}")
                logger.error(traceback.format_exc())
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary."""
        logger.info("=" * 60)
        logger.info("🧪 COMPREHENSIVE TEST RESULTS")
        logger.info("=" * 60)
        
        logger.info(f"📊 Total Tests: {self.total_tests}")
        logger.info(f"✅ Passed: {self.passed_tests}")
        logger.info(f"❌ Failed: {self.failed_tests}")
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        logger.info(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.failed_tests == 0:
            logger.info("🎉 ALL TESTS PASSED!")
            logger.info("✅ Repository is ready for production use!")
        else:
            logger.warning(f"⚠️ {self.failed_tests} tests failed")
            logger.info("📋 Failed Tests:")
            for test_name, result in self.test_results.items():
                if not result["success"]:
                    logger.info(f"  - {test_name}: {result['error']}")


async def main():
    """Main test function."""
    test_suite = ComprehensiveTestSuite()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())

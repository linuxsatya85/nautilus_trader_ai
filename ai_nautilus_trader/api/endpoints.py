"""
API Endpoints
=============

This module defines all REST API endpoints for the AI Nautilus Trader system.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from ..utils.logger import get_logger

logger = get_logger(__name__)


class TradingEndpoints:
    """
    Trading API endpoints.
    
    Defines all REST endpoints for the trading system.
    """
    
    def __init__(self, trading_api=None):
        """Initialize trading endpoints."""
        self.trading_api = trading_api
        logger.info("📡 Trading endpoints initialized")
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status."""
        status = {
            "status": "running" if self.trading_api and hasattr(self.trading_api, 'is_running') and self.trading_api.is_running else "stopped",
            "message": "AI Nautilus Trader API is operational",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }
        
        if self.trading_api and hasattr(self.trading_api, 'trading_system') and self.trading_api.trading_system:
            try:
                status.update(self.trading_api.trading_system.get_status())
            except Exception as e:
                logger.warning(f"⚠️ Could not get trading system status: {e}")
        
        return status
    
    def get_health(self) -> Dict[str, Any]:
        """Get health check."""
        return {
            "healthy": True,
            "timestamp": datetime.now().isoformat(),
            "components": {
                "api": "healthy",
                "trading_system": "healthy" if self.trading_api and hasattr(self.trading_api, 'is_running') and self.trading_api.is_running else "stopped"
            }
        }
    
    async def start_system(self) -> Dict[str, Any]:
        """Start the trading system."""
        try:
            if not self.trading_api:
                return {"error": "Trading API not initialized"}
            
            await self.trading_api.start()
            return {"message": "Trading system started successfully", "status": "running"}
            
        except Exception as e:
            logger.error(f"❌ Failed to start system via API: {e}")
            return {"error": str(e), "status": "error"}
    
    async def stop_system(self) -> Dict[str, Any]:
        """Stop the trading system."""
        try:
            if not self.trading_api:
                return {"error": "Trading API not initialized"}
            
            await self.trading_api.stop()
            return {"message": "Trading system stopped successfully", "status": "stopped"}
            
        except Exception as e:
            logger.error(f"❌ Failed to stop system via API: {e}")
            return {"error": str(e), "status": "error"}

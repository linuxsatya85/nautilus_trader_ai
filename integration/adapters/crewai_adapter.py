"""
CrewAI Adapter - Integrates existing CrewAI with Nautilus Trader

This adapter wraps existing CrewAI functionality to work with Nautilus Trader
without modifying the original CrewAI source code.
"""

import sys
import os
import asyncio
import logging
from typing import Dict, List, Any, Optional

# Add CrewAI to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'crewai', 'src'))

# Import existing CrewAI classes - NO MODIFICATIONS NEEDED!
from crewai import Agent, Crew, Task, LLM
from crewai.tools import tool

logger = logging.getLogger(__name__)


class CrewAIAdapter:
    """
    Adapter to integrate existing CrewAI with Nautilus Trader.
    
    This class wraps CrewAI functionality and provides methods to:
    - Create trading-focused AI agents using existing CrewAI
    - Execute crew analysis and convert results to trading signals
    - Bridge CrewAI events with Nautilus Trader message system
    """
    
    def __init__(self, nautilus_message_bus=None):
        self.nautilus_bus = nautilus_message_bus
        self.crews: Dict[str, Crew] = {}
        self.agents: Dict[str, Agent] = {}
        self.active_tasks: Dict[str, Any] = {}
        
        # Create default trading-focused tools
        self._setup_trading_tools()
        
    def _setup_trading_tools(self):
        """Setup trading-specific tools for AI agents."""
        
        @tool
        def technical_analysis(market_data: dict) -> str:
            """Perform technical analysis on market data."""
            try:
                # Simple technical analysis
                close_prices = market_data.get('close_prices', [])
                if len(close_prices) < 2:
                    return "Insufficient data for analysis"
                    
                # Calculate simple moving average
                sma = sum(close_prices[-5:]) / min(5, len(close_prices))
                current_price = close_prices[-1]
                
                trend = "bullish" if current_price > sma else "bearish"
                strength = abs(current_price - sma) / sma * 100
                
                return f"Technical Analysis: {trend} trend with {strength:.2f}% strength"
            except Exception as e:
                return f"Analysis error: {str(e)}"
                
        @tool
        def risk_assessment(position_data: dict) -> str:
            """Assess risk for a trading position."""
            try:
                position_size = position_data.get('size', 0)
                account_balance = position_data.get('balance', 100000)
                risk_pct = (position_size / account_balance) * 100
                
                if risk_pct > 5:
                    return f"HIGH RISK: Position size {risk_pct:.2f}% of account"
                elif risk_pct > 2:
                    return f"MEDIUM RISK: Position size {risk_pct:.2f}% of account"
                else:
                    return f"LOW RISK: Position size {risk_pct:.2f}% of account"
            except Exception as e:
                return f"Risk assessment error: {str(e)}"
        
        self.trading_tools = [technical_analysis, risk_assessment]
        
    def create_market_analyst_agent(self, name: str = "market_analyst") -> Agent:
        """Create a market analyst agent using existing CrewAI."""
        agent = Agent(
            role="Senior Market Analyst",
            goal="Analyze market conditions and provide accurate trading recommendations",
            backstory="""You are a seasoned market analyst with 20+ years of experience 
            in financial markets. You specialize in technical analysis, risk assessment, 
            and identifying profitable trading opportunities.""",
            tools=self.trading_tools,
            verbose=True,
            max_iter=3,
            memory=True
        )
        
        self.agents[name] = agent
        logger.info(f"Created market analyst agent: {name}")
        return agent
        
    def create_risk_manager_agent(self, name: str = "risk_manager") -> Agent:
        """Create a risk management agent using existing CrewAI."""
        agent = Agent(
            role="Risk Management Specialist", 
            goal="Minimize portfolio risk while maximizing returns",
            backstory="""You are a quantitative risk expert with institutional 
            trading experience. You focus on position sizing, risk-reward ratios, 
            and portfolio protection strategies.""",
            tools=self.trading_tools,
            verbose=True,
            max_iter=2,
            memory=True
        )
        
        self.agents[name] = agent
        logger.info(f"Created risk manager agent: {name}")
        return agent
        
    def create_trading_crew(self, name: str, agents: List[Agent] = None) -> Crew:
        """Create a trading crew using existing CrewAI."""
        if agents is None:
            # Create default trading crew
            agents = [
                self.create_market_analyst_agent(),
                self.create_risk_manager_agent()
            ]
            
        crew = Crew(
            agents=agents,
            verbose=True,
            memory=True
        )
        
        self.crews[name] = crew
        logger.info(f"Created trading crew: {name} with {len(agents)} agents")
        return crew
        
    async def analyze_market_data(self, crew_name: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute crew analysis on market data using existing CrewAI.
        
        Args:
            crew_name: Name of the crew to use
            market_data: Market data dictionary
            
        Returns:
            Dictionary containing trading signal and analysis
        """
        crew = self.crews.get(crew_name)
        if not crew:
            logger.error(f"Crew {crew_name} not found")
            return {"error": f"Crew {crew_name} not found"}
            
        try:
            # Create analysis task
            analysis_task = Task(
                description=f"""
                Analyze the following market data and provide a trading recommendation:
                
                Instrument: {market_data.get('instrument_id', 'Unknown')}
                Current Price: {market_data.get('close', 'N/A')}
                Volume: {market_data.get('volume', 'N/A')}
                Timestamp: {market_data.get('timestamp', 'N/A')}
                
                Provide:
                1. Technical analysis
                2. Risk assessment  
                3. Trading recommendation (BUY/SELL/HOLD)
                4. Confidence level (0-100%)
                5. Reasoning for the recommendation
                """,
                expected_output="Trading recommendation with analysis and confidence level"
            )
            
            # Add task to crew
            crew.tasks = [analysis_task]
            
            # Execute crew analysis using existing CrewAI kickoff
            result = crew.kickoff()
            
            # Convert CrewAI result to Nautilus-compatible format
            return self._parse_crew_result(result, market_data)
            
        except Exception as e:
            logger.error(f"Error in crew analysis: {str(e)}")
            return {
                "error": str(e),
                "signal": "HOLD",
                "confidence": 0.0
            }
            
    def _parse_crew_result(self, crew_result, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse CrewAI crew result into structured trading signal."""
        try:
            result_text = str(crew_result).upper()
            
            # Extract trading signal
            signal = "HOLD"  # default
            if "BUY" in result_text and "SELL" not in result_text:
                signal = "BUY"
            elif "SELL" in result_text and "BUY" not in result_text:
                signal = "SELL"
                
            # Extract confidence (look for percentage)
            confidence = 0.5  # default
            import re
            confidence_match = re.search(r'(\d+)%', result_text)
            if confidence_match:
                confidence = float(confidence_match.group(1)) / 100.0
                
            return {
                "instrument_id": market_data.get('instrument_id'),
                "signal": signal,
                "confidence": confidence,
                "reasoning": str(crew_result),
                "timestamp": market_data.get('timestamp'),
                "source": "crewai_analysis"
            }
            
        except Exception as e:
            logger.error(f"Error parsing crew result: {str(e)}")
            return {
                "instrument_id": market_data.get('instrument_id'),
                "signal": "HOLD",
                "confidence": 0.0,
                "reasoning": f"Parse error: {str(e)}",
                "timestamp": market_data.get('timestamp'),
                "source": "crewai_analysis"
            }
            
    def get_crew_status(self, crew_name: str) -> Dict[str, Any]:
        """Get status of a crew."""
        crew = self.crews.get(crew_name)
        if not crew:
            return {"status": "not_found"}
            
        return {
            "status": "active",
            "agents_count": len(crew.agents),
            "memory_enabled": crew.memory,
            "verbose": crew.verbose
        }
        
    def list_crews(self) -> List[str]:
        """List all available crews."""
        return list(self.crews.keys())
        
    def list_agents(self) -> List[str]:
        """List all available agents."""
        return list(self.agents.keys())
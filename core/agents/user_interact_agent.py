# core/agents/user_interact_agent.py
import asyncio
from datetime import datetime
from typing import Dict, Any

from ..bus import bus
from ..protocol import Topic
from ..models import UserRequest, PriceResponse
from .pricing_optimizer import LLMBrain


class UserInteractAgent:
    """Agent that handles user interactions and routes to pricing optimizer."""
    
    def __init__(self, product_name: str = "SKU-123", db_path: str = "market.db"):
        self.product_name = product_name
        self.db_path = db_path
        self.pricing_brain = LLMBrain()
        self.active_requests: Dict[str, UserRequest] = {}
    
    async def start(self):
        """Start the agent and subscribe to user requests."""
        bus.subscribe(Topic.USER_REQUEST.value, self.handle_user_request)
        print(f"UserInteractAgent started, listening for user requests...")
    
    async def handle_user_request(self, request: UserRequest):
        """Handle incoming user request and route to pricing optimizer."""
        try:
            print(f"Processing user request: {request.message} for product: {request.product_name}")
            
            # Store request for tracking
            self.active_requests[request.user_id] = request
            
            # Use the request's product name or fallback to default
            product_name = request.product_name or self.product_name
            
            # Call the pricing optimizer's process_full_workflow method
            def alert_notifier(msg):
                print(f"Alert from pricing optimizer: {msg}")
            
            # Process the request through the pricing optimizer
            result = self.pricing_brain.process_full_workflow(
                user_request=request.message,
                product_name=product_name,
                db_path=self.db_path,
                notify_alert_fn=alert_notifier,
                wait_seconds=1,  # Faster response for chat
                max_wait_attempts=2  # Fewer attempts for real-time feel
            )
            
            # Create response based on result
            if result.get("status") == "success":
                response_message = self.format_success_response(result)
            else:
                response_message = self.format_error_response(result)
            
            # Create and publish response
            response = PriceResponse(
                user_id=request.user_id,
                request_message=request.message,
                response_message=response_message,
                product_name=product_name,
                price=result.get("price"),
                algorithm=result.get("algorithm"),
                status=result.get("status", "error")
            )
            
            # Publish response back to the bus
            await bus.publish(Topic.PRICE_RESPONSE.value, response)
            
            # Clean up completed request
            self.active_requests.pop(request.user_id, None)
            
        except Exception as e:
            # Handle any errors and send error response
            error_response = PriceResponse(
                user_id=request.user_id,
                request_message=request.message,
                response_message=f"Sorry, I encountered an error processing your request: {str(e)}",
                product_name=request.product_name or self.product_name,
                status="error"
            )
            await bus.publish(Topic.PRICE_RESPONSE.value, error_response)
            self.active_requests.pop(request.user_id, None)
    
    def format_success_response(self, result: Dict[str, Any]) -> str:
        """Format a successful pricing result into a user-friendly message."""
        product = result.get("product", "the product")
        price = result.get("price", "N/A")
        algorithm = result.get("algorithm", "standard")
        
        # Create a user-friendly response based on the algorithm used
        if algorithm == "profit_maximization":
            return f"💰 **Profit Maximization Complete!**\n\nOptimal price for {product}: **${price:.2f}**\n\nThis price is calculated to maximize your profit margins based on current market conditions and demand patterns."
        elif algorithm == "ml_model":
            return f"🤖 **AI Model Prediction Ready!**\n\nRecommended price for {product}: **${price:.2f}**\n\nThis prediction uses machine learning analysis of market trends, competitor pricing, and historical data patterns."
        elif algorithm == "rule_based":
            return f"📊 **Market Analysis Complete!**\n\nSuggested price for {product}: **${price:.2f}**\n\nThis price is based on competitor analysis and rule-based optimization to stay competitive while maintaining margins."
        else:
            return f"✅ **Pricing Optimization Complete!**\n\nNew price for {product}: **${price:.2f}**\n\nPrice calculated using {algorithm} optimization strategy."
    
    def format_error_response(self, result: Dict[str, Any]) -> str:
        """Format an error result into a user-friendly message."""
        error_msg = result.get("message", "Unknown error occurred")
        
        if "market data" in error_msg.lower():
            return "📈 **Market Data Update Needed**\n\nI need fresh market data to provide accurate pricing recommendations. The market data collector is working to gather the latest information. Please try again in a moment."
        elif "connection" in error_msg.lower() or "database" in error_msg.lower():
            return "🔧 **System Maintenance**\n\nI'm experiencing a temporary connection issue. Our technical team is working to resolve this. Please try again shortly."
        else:
            return f"❓ **Processing Issue**\n\nI encountered an issue while processing your request: {error_msg}\n\nPlease try rephrasing your request or contact support if the issue persists."


# Global instance for easy import
user_interact_agent = UserInteractAgent()
print("UserInteractAgent: module imported and global instance created")

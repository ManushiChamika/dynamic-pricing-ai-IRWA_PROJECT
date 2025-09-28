from __future__ import annotations

import asyncio
from typing import Dict, Any, Optional
import uuid
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, ValidationError, Field

try:
    from mcp.server.fastmcp import FastMCP
except Exception as e:
    # Allow file to exist even if MCP isn't installed; runtime will report
    FastMCP = None  # type: ignore

from .optimizer import Features, optimize
from ..agent_sdk.health_tools import ping, version, health
from ..agent_sdk.auth import verify_capability, AuthError, get_auth_metrics

# Input validation schemas using Pydantic
class ProposePriceRequest(BaseModel):
    sku: str = Field(..., min_length=1)
    our_price: float = Field(..., gt=0)
    competitor_price: Optional[float] = Field(None, gt=0)
    demand_index: Optional[float] = Field(None, ge=0)
    cost: Optional[float] = Field(None, ge=0)
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, gt=0)
    min_margin: Optional[float] = Field(0.12, ge=0, le=1)

class ProposalActionRequest(BaseModel):
    proposal_id: str = Field(..., min_length=1)


async def main():
    if FastMCP is None:
        raise RuntimeError("MCP not available: install the MCP package to run this server.")

    mcp = FastMCP("price-optimizer-service")

    @mcp.tool()
    async def propose_price(
        sku: str,
        our_price: float,
        competitor_price: float = None,
        demand_index: float = None,
        cost: float = None,
        min_price: float = None,
        max_price: float = None,
        min_margin: float = 0.12,
        capability_token: str = ""
    ) -> Dict[str, Any]:
        """Generate price optimization proposal with validation."""
        try:
            # Validate auth
            verify_capability(capability_token, "propose")
            
            # Validate input using Pydantic
            request = ProposePriceRequest(
                sku=sku,
                our_price=our_price,
                competitor_price=competitor_price,
                demand_index=demand_index,
                cost=cost,
                min_price=min_price,
                max_price=max_price,
                min_margin=min_margin
            )
            
            # Validate price constraints
            if request.min_price and request.max_price and request.min_price >= request.max_price:
                return {"ok": False, "error": "min_price must be less than max_price", "error_code": "validation_error"}
            
            f = Features(
                sku=request.sku,
                our_price=request.our_price,
                competitor_price=request.competitor_price,
                demand_index=request.demand_index,
                cost=request.cost,
            )
            
            res = optimize(
                f=f,
                min_price=request.min_price or 0.0,
                max_price=request.max_price or 1e9,
                min_margin=request.min_margin,
            )
            
            # Wrap in proposal format
            proposal_id = str(uuid.uuid4())
            return {
                "ok": True,
                "proposal": {
                    "proposal_id": proposal_id,
                    "sku": request.sku,
                    "current_price": request.our_price,
                    "proposed_price": res.get("price", request.our_price),
                    "expected_margin": res.get("margin", request.min_margin),
                    "confidence": res.get("confidence", 0.8),
                    "reasoning": res.get("reasoning", "Price optimization based on market conditions"),
                    "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
                    "inputs": {
                        "competitor_price": request.competitor_price,
                        "demand_index": request.demand_index,
                        "cost": request.cost,
                        "min_price": request.min_price,
                        "max_price": request.max_price,
                        "min_margin": request.min_margin
                    }
                }
            }
        except AuthError as e:
            return {"ok": False, "error": "auth_error", "message": str(e)}
        except ValidationError as e:
            return {"ok": False, "error": "validation_error", "details": e.errors()}
        except Exception as e:
            return {"ok": False, "error": str(e), "error_code": "optimization_error"}

    @mcp.tool()
    async def explain_proposal(proposal_id: str, capability_token: str = "") -> Dict[str, Any]:
        """Explain optimization reasoning for a proposal with validation."""
        try:
            # Validate auth
            verify_capability(capability_token, "explain")
            
            # Validate input
            request = ProposalActionRequest(proposal_id=proposal_id)
            
            # In production, this would fetch actual proposal data
            return {
                "ok": True,
                "explanation": {
                    "proposal_id": request.proposal_id,
                    "reasoning": "Price optimization considers market conditions, competitor pricing, and demand patterns",
                    "factors": [
                        {"name": "competitor_price", "weight": 0.3, "description": "Impact of competitor pricing on our positioning"},
                        {"name": "demand_index", "weight": 0.25, "description": "Customer demand signal for price sensitivity"},
                        {"name": "cost_margin", "weight": 0.25, "description": "Minimum margin requirements based on cost structure"},
                        {"name": "market_position", "weight": 0.2, "description": "Our competitive position in the market segment"}
                    ],
                    "algorithm": "Multi-factor optimization with constraint satisfaction",
                    "generated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        except AuthError as e:
            return {"ok": False, "error": "auth_error", "message": str(e)}
        except ValidationError as e:
            return {"ok": False, "error": "validation_error", "details": e.errors()}
        except Exception as e:
            return {"ok": False, "error": "internal_error", "message": str(e)}

    @mcp.tool()
    async def apply_proposal(proposal_id: str, capability_token: str = "") -> Dict[str, Any]:
        """Apply approved price proposal with validation."""
        try:
            # Validate auth
            verify_capability(capability_token, "apply")
            
            # Validate input
            request = ProposalActionRequest(proposal_id=proposal_id)
            
            # In production, this would:
            # 1. Validate proposal exists and is not expired
            # 2. Update the pricing system
            # 3. Log the change for audit
            
            return {
                "ok": True,
                "result": {
                    "proposal_id": request.proposal_id,
                    "status": "applied",
                    "applied_at": datetime.now(timezone.utc).isoformat(),
                    "message": "Price proposal has been successfully applied"
                }
            }
        except AuthError as e:
            return {"ok": False, "error": "auth_error", "message": str(e)}
        except ValidationError as e:
            return {"ok": False, "error": "validation_error", "details": e.errors()}
        except Exception as e:
            return {"ok": False, "error": "internal_error", "message": str(e)}

    @mcp.tool()
    async def cancel_proposal(proposal_id: str, capability_token: str = "") -> Dict[str, Any]:
        """Cancel pending proposal with validation."""
        try:
            # Validate auth
            verify_capability(capability_token, "apply")  # Same permission as apply since it modifies proposals
            
            # Validate input
            request = ProposalActionRequest(proposal_id=proposal_id)
            
            # In production, this would:
            # 1. Validate proposal exists and is cancellable
            # 2. Mark proposal as cancelled
            # 3. Log the cancellation for audit
            
            return {
                "ok": True,
                "result": {
                    "proposal_id": request.proposal_id,
                    "status": "cancelled",
                    "cancelled_at": datetime.now(timezone.utc).isoformat(),
                    "message": "Price proposal has been cancelled"
                }
            }
        except AuthError as e:
            return {"ok": False, "error": "auth_error", "message": str(e)}
        except ValidationError as e:
            return {"ok": False, "error": "validation_error", "details": e.errors()}
        except Exception as e:
            return {"ok": False, "error": "internal_error", "message": str(e)}

    # Legacy tool for backward compatibility
    @mcp.tool()
    async def optimize_price(payload: Dict[str, Any], capability_token: str = "") -> Dict[str, Any]:
        """Legacy optimize_price tool - redirects to propose_price with payload unpacking."""
        try:
            return await propose_price(
                sku=payload.get("sku"),
                our_price=payload.get("our_price"),
                competitor_price=payload.get("competitor_price"),
                demand_index=payload.get("demand_index"),
                cost=payload.get("cost"),
                min_price=payload.get("min_price"),
                max_price=payload.get("max_price"),
                min_margin=payload.get("min_margin", 0.12),
                capability_token=capability_token
            )
        except Exception as e:
            return {"ok": False, "error": "legacy_call_error", "message": str(e)}

    # Health tools
    @mcp.tool()
    async def ping_health() -> Dict[str, Any]:
        """Basic connectivity test."""
        return await ping()

    @mcp.tool() 
    async def version_info() -> Dict[str, Any]:
        """Server version information."""
        return await version()

    @mcp.tool()
    async def health_check() -> Dict[str, Any]:
        """Detailed health status."""
        return await health("price-optimizer", check_dependencies=True)

    @mcp.tool()
    async def auth_metrics(capability_token: str = "") -> Dict[str, Any]:
        """Get authentication metrics for this service."""
        try:
            # Validate auth - requires admin scope to view metrics
            verify_capability(capability_token, "admin")
            
            metrics = get_auth_metrics()
            return {
                "ok": True,
                "result": {
                    "service": "price-optimizer",
                    "metrics": metrics,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
        except AuthError as e:
            return {"ok": False, "error": "auth_error", "message": str(e)}
        except Exception as e:
            return {"ok": False, "error": "internal_error", "message": str(e)}

    await mcp.run()


if __name__ == "__main__":
    asyncio.run(main())




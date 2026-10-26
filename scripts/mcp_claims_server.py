"""
Week 9 MCP Server: Claims System
Exposes claim status and adjuster notes via MCP protocol.
"""

import json
import sys


class ClaimsServer:
    """MCP server for claims-system. Implements Model Context Protocol."""
    
    # Mock claims database
    CLAIMS_DB = {
        "CLM-2026-0001": {
            "status": "approved",
            "loss_date": "2026-08-20",
            "claim_amount": 50000,
            "adjuster_notes": [
                "2026-09-01: Initial assessment - water damage from burst pipe",
                "2026-09-05: Inspection completed - sudden accidental discharge confirmed",
                "2026-09-10: Approved for payment - $49,000 after $1,000 deductible"
            ]
        },
        "CLM-2026-0002": {
            "status": "denied",
            "loss_date": "2026-08-21",
            "claim_amount": 75000,
            "adjuster_notes": [
                "2026-09-01: Claim received - basement flooding reported",
                "2026-09-05: Site visit - heavy rainfall, foundation damage evident",
                "2026-09-10: Denied - loss cause is flood (surface water exclusion applies)"
            ]
        }
    }
    
    def __init__(self):
        self.tools = [
            {
                "name": "get_claim_status",
                "description": "Get the current status of a claim (approved, denied, pending)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "claim_number": {
                            "type": "string",
                            "description": "Claim number, format CLM-YYYY-NNNNN"
                        }
                    },
                    "required": ["claim_number"]
                }
            },
            {
                "name": "get_adjuster_notes",
                "description": "Get the timeline of adjuster notes for a claim",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "claim_number": {
                            "type": "string",
                            "description": "Claim number, format CLM-YYYY-NNNNN"
                        }
                    },
                    "required": ["claim_number"]
                }
            }
        ]
    
    def handle_initialize(self):
        """Handle MCP initialize request."""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "claims-system",
                "version": "1.0.0"
            }
        }
    
    def handle_tools_list(self):
        """Handle tools/list request."""
        return {
            "tools": self.tools
        }
    
    def handle_tool_call(self, tool_name, arguments):
        """Handle tool call request."""
        claim_number = arguments.get("claim_number", "")
        
        if tool_name == "get_claim_status":
            if claim_number in self.CLAIMS_DB:
                claim = self.CLAIMS_DB[claim_number]
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Claim {claim_number}: Status is {claim['status']}"
                        }
                    ]
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Claim {claim_number} not found. Claim numbers look like CLM-YYYY-NNNNN. Check the claim number and try again."
                        }
                    ],
                    "isError": True
                }
        
        elif tool_name == "get_adjuster_notes":
            if claim_number in self.CLAIMS_DB:
                claim = self.CLAIMS_DB[claim_number]
                notes_text = "\n".join(claim["adjuster_notes"])
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Adjuster notes for {claim_number}:\n{notes_text}"
                        }
                    ]
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Claim {claim_number} not found. Claim numbers look like CLM-YYYY-NNNNN. Verify the claim number exists in the system."
                        }
                    ],
                    "isError": True
                }
        
        return {
            "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
            "isError": True
        }
    
    def run(self):
        """Run the MCP server in stdio mode."""
        while True:
            try:
                line = input()
                if not line:
                    continue
                
                request = json.loads(line)
                method = request.get("method")
                params = request.get("params", {})
                request_id = request.get("id")
                
                if method == "initialize":
                    response = self.handle_initialize()
                elif method == "tools/list":
                    response = self.handle_tools_list()
                elif method == "tools/call":
                    response = self.handle_tool_call(
                        params.get("name"),
                        params.get("arguments", {})
                    )
                else:
                    response = {"error": {"code": -32601, "message": "Method not found"}}
                
                output = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": response
                }
                
                print(json.dumps(output))
                sys.stdout.flush()
            
            except (EOFError, KeyboardInterrupt):
                break
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32700, "message": "Parse error"}
                }
                print(json.dumps(error_response))
                sys.stdout.flush()


if __name__ == "__main__":
    server = ClaimsServer()
    server.run()

#!/usr/bin/env python3
# mcp/calculator/server.py
"""
Ultra-simple MCP Calculator Server - MVP for testing
Compatible with Elf's MCP client implementation
"""
import json
import sys

def main():
    """Handle MCP requests via stdin/stdout"""
    tools = [
        {
            "name": "calculate",
            "description": "Perform basic arithmetic operations (add, subtract, multiply, divide)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "First number"},
                    "b": {"type": "number", "description": "Second number"},
                    "operation": {"type": "string", "enum": ["add", "subtract", "multiply", "divide"], "description": "Operation to perform"}
                },
                "required": ["a", "b", "operation"]
            }
        }
    ]
    
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            method = request.get("method")
            params = request.get("params", {})
            
            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "calculator", "version": "1.0.0"}
                    }
                }
            elif method == "tools/list":
                response = {
                    "jsonrpc": "2.0", 
                    "id": request.get("id"),
                    "result": {"tools": tools}
                }
            elif method == "tools/call":
                tool_name = params.get("name")
                args = params.get("arguments", {})
                
                if tool_name == "calculate":
                    a = args.get("a")
                    b = args.get("b")
                    operation = args.get("operation")
                    
                    try:
                        if operation == "add":
                            result = a + b
                        elif operation == "subtract":
                            result = a - b
                        elif operation == "multiply":
                            result = a * b
                        elif operation == "divide":
                            if b == 0:
                                raise ValueError("Cannot divide by zero")
                            result = a / b
                        else:
                            raise ValueError(f"Unknown operation: {operation}")
                        
                        response = {
                            "jsonrpc": "2.0",
                            "id": request.get("id"),
                            "result": {
                                "content": [{"type": "text", "text": str(result)}]
                            }
                        }
                    except Exception as e:
                        response = {
                            "jsonrpc": "2.0",
                            "id": request.get("id"),
                            "error": {"code": -1, "message": f"Calculation error: {str(e)}"}
                        }
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "error": {"code": -1, "message": f"Unknown tool: {tool_name}"}
                    }
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {"code": -32601, "message": f"Method not found: {method}"}
                }
            
            print(json.dumps(response), flush=True)
            
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": request.get("id") if 'request' in locals() else None,
                "error": {"code": -32603, "message": str(e)}
            }
            print(json.dumps(error_response), flush=True)

if __name__ == "__main__":
    main()
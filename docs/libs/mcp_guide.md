# 🧠 Integrating Model Context Protocol (MCP) into Python AI Agents

## Overview

The **Model Context Protocol (MCP)** is an open standard developed by Anthropic to facilitate seamless integration between AI models and external tools, services, and data sources. Think of MCP as the "USB-C of AI applications," providing a universal interface for AI agents to interact with various functionalities .

---

## 🔧 Core Components of MCP

- **MCP Server**: Exposes functionalities to AI agents through:
  - **Tools**: Executable functions or operations.
  - **Resources**: Data or content accessible to the agent.
  - **Prompts**: Predefined templates guiding agent interactions.

- **MCP Client**: Resides within the AI agent, facilitating communication with MCP servers to utilize available tools and resources.

This architecture allows agents to dynamically discover and interact with various capabilities provided by different MCP servers .

---

## 🛠️ Implementing an MCP Server in Python

### 1. **Setup and Installation**

Begin by installing the official MCP Python SDK:

```bash
pip install "mcp[cli]"
```

Alternatively, using `uv`:

```bash
uv init mcp-server-demo
cd mcp-server-demo
uv add "mcp[cli]"
```

### 2. **Creating the MCP Server**

Utilize the `FastMCP` class to define your server, tools, and resources:

```python
from mcp.server.fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("ExampleServer")

# Define a tool
@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

# Define a resource
@mcp.resource("message://{user}")
def get_message(user: str) -> str:
    """Retrieve a personalized message."""
    return f"Hello, {user}!"
```

This setup creates a server named "ExampleServer" with a multiplication tool and a message resource.

### 3. **Running the Server**

To run and test your MCP server:

- **Development Mode**: For testing and debugging.

  ```bash
  mcp dev server.py
  ```

- **Installation Mode**: For integrating with clients like Claude Desktop.

  ```bash
  mcp install server.py
  ```

These commands start the server and make it discoverable to MCP clients .

---

## 🤖 Integrating MCP Client into an AI Agent

### 1. **Installing the Client SDK**

If you're using the Hugging Face ecosystem, install the MCP-enabled version:

```bash
pip install "huggingface_hub[mcp]>=0.32.0"
```

### 2. **Connecting to MCP Servers**

Within your agent application, implement the MCP client to discover and interact with available servers:

```python
from mcp.client import MCPClient

# Initialize the MCP client
client = MCPClient()

# Discover available servers
servers = client.discover_servers()

# Connect to a specific server
server = client.connect(servers[0])

# Use a tool from the server
result = server.call_tool("multiply", {"a": 3, "b": 4})
print(result)  # Output: 12
```

This code discovers available MCP servers, connects to one, and invokes the "multiply" tool with specified parameters.

---

## 🔒 Security Considerations

When implementing MCP servers and clients, it's crucial to address security concerns:

- **Access Control**: Ensure that only authorized agents can access specific tools and resources.

- **Input Validation**: Validate inputs to tools to prevent injection attacks.

- **Audit Logging**: Maintain logs of interactions for monitoring and auditing purposes.

- **User Consent**: Implement mechanisms to obtain user consent before accessing sensitive data or performing critical operations .

---

## 📚 Additional Resources

- **Official MCP Documentation**: [Anthropic MCP Docs](https://docs.anthropic.com/en/docs/agents-and-tools/mcp)

- **GitHub Repository**: [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

- **Tutorials and Articles**:
  - [Model Context Protocol (MCP) Explained](https://medium.com/data-science-collective/model-context-protocol-mcp-explained-ef5c33c5fe05)
  - [Building a Model Context Protocol Server using Jina.ai and Python](https://traversable.twelvehart.org/building-a-model-context-protocol-server-using-jina-ai-and-python-1b606e155506)

---

By following this guide, developers can effectively integrate MCP functionality into their Python-based AI agents, enabling standardized and secure interactions with external tools and data sources.

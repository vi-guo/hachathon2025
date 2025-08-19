from fastmcp import FastMCP

config = {
    "mcpServers": {
        "A": {"url": "https://a.example.com/mcp", "transport": "http"},
        "B": {"url": "https://b.example.com/mcp", "transport": "http"},
    }
}

proxy = FastMCP.as_proxy(config, name="CompositeProxy")

if __name__ == "__main__":
    proxy.run(transport="http", host="0.0.0.0", port=8002)

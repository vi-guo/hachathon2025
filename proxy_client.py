import asyncio
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession

PROXY_URL = "http://proxy.example.com:8002/mcp"  # <- your proxy

async def main():
    rs, ws, _ = await streamablehttp_client(PROXY_URL).__aenter__()
    sess = ClientSession(rs, ws)
    await sess.initialize()

    reply = await sess.list_tools()
    tools = getattr(reply, "tools", reply["tools"])  # works for dict or model
    print("Tools via proxy:", [t["name"] for t in tools])

    # Call a proxied tool (e.g., "echo")
    result = await sess.call_tool("echo", {"message": "hello via proxy"})
    print("Result:", result)

asyncio.run(main())

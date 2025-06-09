# main.py
from mcp.server.fastmcp import FastMCP
from fastapi import FastAPI
from kerb_middleware import kerberos_guard

mcp = FastMCP("tools")
app = FastAPI()
app.add_middleware(kerberos_guard)       # plug it in
app.mount("/", mcp)                      # MCP endpoints work untouched

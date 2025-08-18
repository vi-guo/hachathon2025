# proxy.py
import asyncio
import os
import time
import ssl
from typing import Any, Dict, Optional

# === MCP protocol libs (pip install modelcontextprotocol) ===
from mcp import Server, Context, mcp, run as mcp_run
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession

# ===================== 配置 =====================
BACKEND_URL = os.getenv("BACKEND_MCP_URL", "http://127.0.0.1:9001/mcp")
PROXY_HOST = os.getenv("PROXY_HOST", "0.0.0.0")
PROXY_PORT = int(os.getenv("PROXY_PORT", "8002"))

# mTLS 相关（可选）
# BACKEND_TLS_CA   = 后端服务器证书的 CA 文件路径（PEM）
# BACKEND_TLS_CERT = 代理本身的客户端证书（PEM）
# BACKEND_TLS_KEY  = 代理本身的私钥（PEM）
# BACKEND_TLS_SKIP_VERIFY = "1"/"true" 时不校验后端证书（仅 PoC！别用于生产）
TLS_CA   = os.getenv("BACKEND_TLS_CA")
TLS_CERT = os.getenv("BACKEND_TLS_CERT")
TLS_KEY  = os.getenv("BACKEND_TLS_KEY")
TLS_SKIP_VERIFY = os.getenv("BACKEND_TLS_SKIP_VERIFY", "").lower() in ("1", "true", "yes")

# ===================== 认证桩 =====================
class KerberosVerifier:
    async def verify_ap_req(self, ctx: Context) -> Dict[str, Any]:
        ap_req = ctx.headers.get("x-kerberos-ap-req")
        if not ap_req:
            return {"principal": "anonymous@EXAMPLE"}
        # TODO: 在此校验 AP_REQ 并解析 principal / attrs
        return {"principal": "jane.doe@EXAMPLE.COM"}

class TokenBrokerClient:
    async def get_function_token(self, user_info: Dict[str, Any]) -> str:
        # TODO: 调用真实 Token Broker
        return f"fn_token_db_reader_{int(time.time())}"

# ===================== 后端路由 =====================
class BackendRouter:
    def __init__(self, backend_url: str):
        self.backend_url = backend_url
        self._sess: Optional[ClientSession] = None
        self._tools: Dict[str, Dict[str, Any]] = {}

    def _build_ssl_ctx(self) -> Optional[ssl.SSLContext]:
        """若 URL 为 https:// 则构建 mTLS 所需 SSLContext。"""
        if not self.backend_url.startswith("https://"):
            return None
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        if TLS_CA:
            ctx.load_verify_locations(cafile=TLS_CA)
        if TLS_SKIP_VERIFY:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        if TLS_CERT and TLS_KEY:
            ctx.load_cert_chain(certfile=TLS_CERT, keyfile=TLS_KEY)
        # ctx.minimum_version = ssl.TLSVersion.TLSv1_2  # 如需强制 TLS1.2+
        return ctx

    async def _dial_backend(self):
        """
        与后端建立连接。
        先尝试用 ssl=SSLContext；若不支持（不同版本实现差异），回退用 httpx_kwargs。
        """
        ssl_ctx = self._build_ssl_ctx()

        # Try A: ssl=...
        try:
            read_stream, write_stream, _ = await streamablehttp_client(
                self.backend_url,
                ssl=ssl_ctx
            ).__aenter__()
            return read_stream, write_stream
        except TypeError:
            pass  # 继续尝试 httpx_kwargs

        # Try B: httpx_kwargs=...
        httpx_kwargs = {}
        if self.backend_url.startswith("https://"):
            # 对 httpx：verify 可为 CA 路径或 False；cert 为 (cert, key)
            if TLS_SKIP_VERIFY:
                httpx_kwargs["verify"] = False
            elif TLS_CA:
                httpx_kwargs["verify"] = TLS_CA
            if TLS_CERT and TLS_KEY:
                httpx_kwargs["cert"] = (TLS_CERT, TLS_KEY)

        read_stream, write_stream, _ = await streamablehttp_client(
            self.backend_url,
            httpx_kwargs=httpx_kwargs
        ).__aenter__()
        return read_stream, write_stream

    async def start(self):
        read_stream, write_stream = await self._dial_backend()
        self._sess = ClientSession(read_stream, write_stream)
        await self._sess.initialize()
        tools_reply = await self._sess.list_tools()
        # 标准结构：{"tools": [{name, description, input_schema...}, ...]}
        self._tools = {t["name"]: t for t in tools_reply["tools"]}

    def list_tools(self) -> Dict[str, Dict[str, Any]]:
        return self._tools

    async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        assert self._sess is not None, "Backend session not initialized"
        return await self._sess.call_tool(tool_name, args)

# ===================== 代理服务器 =====================
class ProxyMCP:
    def __init__(self, backend_url: str):
        self.server = Server("mcp-proxy")
        self.router = BackendRouter(backend_url)
        self.kerberos = KerberosVerifier()
        self.broker = TokenBrokerClient()

    async def initialize(self):
        await self.router.start()
        for tool_name, tool_def in self.router.list_tools().items():
            self._register_proxy_tool(tool_name, tool_def)

    def _register_proxy_tool(self, tool_name: str, tool_def: Dict[str, Any]) -> None:
        @mcp.tool(self.server, name=tool_name, description=f"[PROXY] {tool_def.get('description','')}")
        async def proxy_tool(ctx: Context, **kwargs):
            # 1) Kerberos 校验（桩）
            user_info = await self.kerberos.verify_ap_req(ctx)
            # 2) Token Broker（桩）
            fn_token = await self.broker.get_function_token(user_info)
            # 3) 注入认证信息并转发
            forward_args = dict(kwargs)
            forward_args["_auth"] = {
                "user_principal": user_info.get("principal"),
                "function_token": fn_token,
            }
            return await self.router.call_tool(tool_name, forward_args)

    async def run(self):
        await self.initialize()
        await mcp_run(
            self.server,
            transport="streamable-http",
            host=PROXY_HOST,
            port=PROXY_PORT
        )

# ===================== 启动入口 =====================
if __name__ == "__main__":
    asyncio.run(ProxyMCP(BACKEND_URL).run())

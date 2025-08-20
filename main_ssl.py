import ssl, uvicorn
from fastmcp import FastMCP

mcp = FastMCP("MyServer")
app = mcp.http_app()

# If your key is encrypted, supply the password:
uvicorn.run(
    app,
    host="0.0.0.0", port=8000,
    ssl_certfile="./server-cert.pem",          # may include full chain
    ssl_keyfile="./server-key.pem",            # private key PEM
    ssl_keyfile_password="your-pass-here",     # only needed if key is encrypted
    # For mTLS (verify client certs):
    # ssl_ca_certs="./ca-bundle.pem",
    # ssl_cert_reqs=ssl.CERT_REQUIRED,
)

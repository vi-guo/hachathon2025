# only the new bits shown
import ssl, signal

def make_ctx():
    ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ctx.load_verify_locations("root.crt")
    ctx.load_cert_chain(certfile="server.crt", keyfile="server.key")
    ctx.verify_mode = ssl.CERT_REQUIRED
    return ctx

ctx = make_ctx()

def reload_ctx(sig, _):
    global ctx
    ctx = make_ctx()
    print("[TLS] context reloaded")

signal.signal(signal.SIGHUP, reload_ctx)

uvicorn.run(mcp, host="0.0.0.0", port=8443, ssl_context=lambda: ctx)

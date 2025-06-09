# kerb_middleware.py
import base64
import gssapi
from fastapi import Request, HTTPException

async def kerberos_guard(request: Request, call_next):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Negotiate "):
        raise HTTPException(status_code=401,
                            headers={"WWW-Authenticate": "Negotiate"})
    token = base64.b64decode(auth.split(" ", 1)[1])
    server_creds = gssapi.Credentials(usage="accept")      # reads /etc/krb5.keytab
    ctx = gssapi.SecurityContext(creds=server_creds)
    out_token = ctx.step(token)
    if out_token:          # mutual auth
        headers = {"WWW-Authenticate": "Negotiate " + base64.b64encode(out_token).decode()}
    if not ctx.complete:
        raise HTTPException(status_code=401, headers=headers)
    request.state.remote_user = str(ctx.initiator_name)
    return await call_next(request)

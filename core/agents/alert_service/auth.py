import hmac, hashlib, time, os

SECRET = os.getenv("ALERTS_CAP_SECRET", "dev-secret")

SCOPES = {"read","write","create_rule"}

def verify_capability(token: str, scope: str):
    if scope not in SCOPES: raise PermissionError("unknown scope")
    try:
        payload, sig = token.rsplit(".", 1)
        if not hmac.compare_digest(
            hmac.new(SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest(), sig
        ):
            raise ValueError("bad signature")
        ts_str, granted = payload.split(":")
        if scope not in granted.split(","): raise PermissionError("scope denied")
        if time.time() - int(ts_str) > 3600: raise PermissionError("token expired")
    except Exception as e:
        raise PermissionError("invalid capability") from e

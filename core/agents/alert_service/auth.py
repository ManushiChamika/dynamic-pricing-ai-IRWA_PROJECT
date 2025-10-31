#This code implements a capability-based authentication system —
#basically a security check to verify if a given token (like an API key) is valid, unexpired, and authorized for a specific permission (scope).

import hmac, hashlib, time, os   # Import security and utility modules

# Get the shared secret key from environment variable, or use default "dev-secret" for local/dev use
SECRET = os.getenv("ALERTS_CAP_SECRET", "dev-secret")

# Define allowed capability scopes (permissions)
SCOPES = {"read", "write", "create_rule"}

# Function to verify a capability token for a given scope
def verify_capability(token: str, scope: str):
    # Check if the requested scope is valid
    if scope not in SCOPES:
        raise PermissionError("unknown scope")

    try:
        # Split the token into payload and signature parts (token format: "<payload>.<signature>")
        payload, sig = token.rsplit(".", 1)

        # Verify the signature using HMAC-SHA256 and the shared SECRET
        if not hmac.compare_digest(
            hmac.new(SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest(), sig
        ):
            # If signatures don’t match, reject the token
            raise ValueError("bad signature")

        # Split the payload into timestamp and granted scopes (format: "<timestamp>:<scope1,scope2,...>")
        ts_str, granted = payload.split(":")

        # Check if the requested scope is included in the granted scopes
        if scope not in granted.split(","):
            raise PermissionError("scope denied")

        # Check if the token has expired (valid for 1 hour = 3600 seconds)
        if time.time() - int(ts_str) > 3600:
            raise PermissionError("token expired")

    except Exception as e:
        # On any error (bad format, wrong signature, expired, etc.), raise a generic invalid capability error
        raise PermissionError("invalid capability") from e

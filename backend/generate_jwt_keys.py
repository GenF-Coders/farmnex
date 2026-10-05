"""Make the login-signing key pair (RS256) for FarmNex.

    python generate_jwt_keys.py              # writes secrets/jwt_private.pem + jwt_public.pem
    python generate_jwt_keys.py --print-env  # ALSO prints the two lines to paste into
                                             # FastAPI Cloud (JWT_PRIVATE_KEY_B64 / JWT_PUBLIC_KEY_B64)

If secrets/ already has a key pair, it is reused (not replaced), so logins made
with it keep working. Delete the two .pem files first if you really want new keys.

Never commit the secrets/ folder or paste the printed lines into a chat, a file in
git, or a PR. They go only into FastAPI Cloud's Environment Variables (as secrets).
"""

import argparse
import base64
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
parser.add_argument(
    "--print-env",
    action="store_true",
    help="print JWT_PRIVATE_KEY_B64=... and JWT_PUBLIC_KEY_B64=... for FastAPI Cloud",
)
args = parser.parse_args()

SECRETS_DIR = Path("secrets")
SECRETS_DIR.mkdir(exist_ok=True)

private_path = SECRETS_DIR / "jwt_private.pem"
public_path = SECRETS_DIR / "jwt_public.pem"


if private_path.is_file() and public_path.is_file():
    private_pem = private_path.read_bytes()
    public_pem = public_path.read_bytes()
    print(f"Using existing keys in {SECRETS_DIR.resolve()}")
else:
    # Generate RSA 2048-bit private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    private_path.write_bytes(private_pem)
    public_path.write_bytes(public_pem)

    print(f"Created: {private_path.resolve()}")
    print(f"Created: {public_path.resolve()}")


if args.print_env:
    print()
    print("Paste these two into FastAPI Cloud -> Environment Variables, each marked SECRET:")
    print()
    print("JWT_PRIVATE_KEY_B64=" + base64.b64encode(private_pem).decode("ascii"))
    print()
    print("JWT_PUBLIC_KEY_B64=" + base64.b64encode(public_pem).decode("ascii"))

from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


SECRETS_DIR = Path("secrets")
SECRETS_DIR.mkdir(exist_ok=True)


# Generate RSA 2048-bit private key
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)


# Export private key
private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
)


# Derive public key
public_key = private_key.public_key()

public_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
)


private_path = SECRETS_DIR / "jwt_private.pem"
public_path = SECRETS_DIR / "jwt_public.pem"


private_path.write_bytes(private_pem)
public_path.write_bytes(public_pem)


print(f"Created: {private_path.resolve()}")
print(f"Created: {public_path.resolve()}")
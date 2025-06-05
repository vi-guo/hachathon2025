# cert_forge.py  – run every 4-5 minutes
from pathlib import Path
from cryptography import x509, hazmat
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from datetime import datetime, timedelta
import os, sys

ROLE   = sys.argv[1]            # "server" or "client"
CN     = f"demo-{ROLE}"
KEY    = Path(f"{ROLE}.key")
CERT   = Path(f"{ROLE}.crt")
ROOT_K = Path("root.key").read_bytes()
ROOT_C = x509.load_pem_x509_certificate(Path("root.crt").read_bytes())

root_key = serialization.load_pem_private_key(ROOT_K, None)

# create new keypair every time
priv_key = hazmat.primitives.asymmetric.rsa.generate_private_key(65537, 2048)
pub_key  = priv_key.public_key()

builder = (
    x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, CN)]))
        .issuer_name(ROOT_C.subject)
        .public_key(pub_key)
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow() - timedelta(seconds=5))
        .not_valid_after(datetime.utcnow() + timedelta(minutes=5))  # 5-min leaf
)
cert = builder.sign(root_key, hashes.SHA256())

KEY.write_bytes(
    priv_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption()
    )
)
CERT.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
print(f"[cert-forge] wrote {CERT} (valid 5 min)")

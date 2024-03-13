import subprocess


def get_ed25519_private_public_pair():
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.primitives import serialization
    privkey = ed25519.Ed25519PrivateKey.generate()
    pubkey = privkey.public_key()
    priv_bytes = privkey.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_bytes = pubkey.public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH,
    )
    return priv_bytes.decode(), pub_bytes.decode()


def get_wg_private_public_psk_pair():
    try:
        private_key = subprocess.run(["wg", "genkey"], capture_output=True, text=True, check=True).stdout.strip()
        public_key = subprocess.run(["wg", "pubkey"], input=private_key, capture_output=True, text=True, check=True).stdout.strip()
        psk = subprocess.run(["wg", "genpsk"], capture_output=True, text=True, check=True).stdout.strip()
        return private_key, public_key, psk
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return None, None, None

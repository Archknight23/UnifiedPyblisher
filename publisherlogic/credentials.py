"""Secure credential storage using Fernet encryption"""

import json
import os
from pathlib import Path
from cryptography.fernet import Fernet


class CredentialManager:
    """Manages encrypted storage of platform credentials"""

    def __init__(self):
        # Store credentials in ~/.unifiedpublisher/
        self.storage_dir = Path.home() / ".unifiedpublisher"
        self.storage_dir.mkdir(exist_ok=True)

        self.key_file = self.storage_dir / ".key"
        self.credentials_file = self.storage_dir / "credentials.enc"

        self.cipher = None
        self._initialize_cipher()

    def _initialize_cipher(self):
        """Initialize or load the encryption key"""
        try:
            if self.key_file.exists():
                # Load existing key
                with open(self.key_file, "rb") as f:
                    key = f.read()
            else:
                # Generate new key
                key = Fernet.generate_key()
                with open(self.key_file, "wb") as f:
                    f.write(key)
                # Secure the key file (user-only read/write)
                os.chmod(self.key_file, 0o600)

            self.cipher = Fernet(key)
        except Exception as e:
            print(f"[CredentialManager] ✗ Failed to initialize cipher: {e}")
            self.cipher = None

    def _ensure_cipher(self):
        if self.cipher is None:
            self._initialize_cipher()
        return self.cipher is not None

    def _load_all(self):
        """Internal: load all stored credentials map."""
        if not self._ensure_cipher():
            return {}
        if not self.credentials_file.exists():
            return {}
        try:
            with open(self.credentials_file, "rb") as f:
                encrypted_data = f.read()
            decrypted_data = self.cipher.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode("utf-8"))
        except Exception as e:
            print(f"[CredentialManager] ✗ Failed to decrypt credentials: {e}")
            return {}

    def _save_all(self, data):
        """Internal: save the full credentials map."""
        if not self._ensure_cipher():
            return False
        try:
            json_data = json.dumps(data).encode("utf-8")
            encrypted_data = self.cipher.encrypt(json_data)
            with open(self.credentials_file, "wb") as f:
                f.write(encrypted_data)
            os.chmod(self.credentials_file, 0o600)
            return True
        except Exception as e:
            print(f"[CredentialManager] ✗ Failed to save credentials: {e}")
            return False

    def save_platform_credentials(self, platform, payload):
        """Save arbitrary credential payload for a platform."""
        try:
            all_creds = self._load_all()
            all_creds[platform] = payload
            if self._save_all(all_creds):
                print(f"[CredentialManager] ✓ Credentials saved for {platform}")
                return True
        except Exception as e:
            print(
                f"[CredentialManager] ✗ Failed to save credentials for {platform}: {e}"
            )
        return False

    def load_platform_credentials(self, platform):
        """Load credentials for a single platform."""
        try:
            creds = self._load_all().get(platform)
            if creds:
                print(f"[CredentialManager] ✓ Loaded credentials for {platform}")
            else:
                print(f"[CredentialManager] No credentials found for {platform}")
            return creds
        except Exception as e:
            print(
                f"[CredentialManager] ✗ Failed to load credentials for {platform}: {e}"
            )
            return None

    def delete_platform_credentials(self, platform):
        """Delete credentials for a single platform."""
        try:
            all_creds = self._load_all()
            if platform in all_creds:
                all_creds.pop(platform, None)
                if all_creds:
                    self._save_all(all_creds)
                else:
                    if self.credentials_file.exists():
                        self.credentials_file.unlink()
                print(f"[CredentialManager] ✓ Credentials deleted for {platform}")
            else:
                print(f"[CredentialManager] No credentials found for {platform}")
            return True
        except Exception as e:
            print(
                f"[CredentialManager] ✗ Failed to delete credentials for {platform}: {e}"
            )
            return False

    # Backward-compatible Bluesky helpers
    def save_credentials(self, handle, password):
        try:
            return self.save_platform_credentials(
                "bluesky", {"handle": handle, "password": password}
            )
        except Exception as e:
            print(f"[CredentialManager] ✗ Failed to save credentials: {e}")
            return False

    def load_credentials(self):
        try:
            return self.load_platform_credentials("bluesky")
        except Exception as e:
            print(f"[CredentialManager] ✗ Failed to load credentials: {e}")
            return None

    def delete_credentials(self):
        try:
            return self.delete_platform_credentials("bluesky")
        except Exception as e:
            print(f"[CredentialManager] ✗ Failed to delete credentials: {e}")
            return False

    def has_saved_credentials(self):
        return self.credentials_file.exists()

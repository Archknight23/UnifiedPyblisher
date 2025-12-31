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
        if self.key_file.exists():
            # Load existing key
            with open(self.key_file, 'rb') as f:
                key = f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            # Secure the key file (user-only read/write)
            os.chmod(self.key_file, 0o600)

        self.cipher = Fernet(key)

    def save_credentials(self, handle, password):
        """
        Encrypt and save Bluesky credentials

        Args:
            handle: Bluesky handle (e.g., "user.bsky.social")
            password: Bluesky app password

        Returns:
            bool: True if successful
        """
        try:
            credentials = {
                "handle": handle,
                "password": password
            }

            # Convert to JSON and encrypt
            json_data = json.dumps(credentials).encode('utf-8')
            encrypted_data = self.cipher.encrypt(json_data)

            # Write to file
            with open(self.credentials_file, 'wb') as f:
                f.write(encrypted_data)

            # Secure the credentials file (user-only read/write)
            os.chmod(self.credentials_file, 0o600)

            print(f"[CredentialManager] ✓ Credentials saved for {handle}")
            return True
        except Exception as e:
            print(f"[CredentialManager] ✗ Failed to save credentials: {e}")
            return False

    def load_credentials(self):
        """
        Load and decrypt Bluesky credentials

        Returns:
            dict: {"handle": str, "password": str} or None if no credentials saved
        """
        try:
            if not self.credentials_file.exists():
                print("[CredentialManager] No saved credentials found")
                return None

            # Read and decrypt
            with open(self.credentials_file, 'rb') as f:
                encrypted_data = f.read()

            decrypted_data = self.cipher.decrypt(encrypted_data)
            credentials = json.loads(decrypted_data.decode('utf-8'))

            print(f"[CredentialManager] ✓ Loaded credentials for {credentials.get('handle', 'unknown')}")
            return credentials
        except Exception as e:
            print(f"[CredentialManager] ✗ Failed to load credentials: {e}")
            return None

    def delete_credentials(self):
        """
        Delete saved credentials

        Returns:
            bool: True if successful
        """
        try:
            if self.credentials_file.exists():
                self.credentials_file.unlink()
                print("[CredentialManager] ✓ Credentials deleted")
            return True
        except Exception as e:
            print(f"[CredentialManager] ✗ Failed to delete credentials: {e}")
            return False

    def has_saved_credentials(self):
        """Check if credentials are saved"""
        return self.credentials_file.exists()

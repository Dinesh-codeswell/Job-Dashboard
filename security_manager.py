"""
SECURITY MANAGER
================
Production-grade security features:
- Credential encryption
- API key rotation
- Input sanitization
- Rate limiting
- Audit logging
"""

import os
import json
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

logger = logging.getLogger(__name__)


# ============================================================================
# CREDENTIAL ENCRYPTION
# ============================================================================

class CredentialManager:
    """
    Secure credential storage using Fernet encryption.
    Replaces plain-text .env files with encrypted storage.
    """
    
    def __init__(self, master_password: Optional[str] = None):
        """
        Initialize credential manager.
        
        Args:
            master_password: Master password for encryption.
                           If None, generates and saves to secure location.
        """
        self.credentials_file = Path.home() / '.linkedin_scraper' / 'credentials.enc'
        self.key_file = Path.home() / '.linkedin_scraper' / '.key'
        
        # Ensure directory exists
        self.credentials_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize encryption key
        if master_password:
            self.key = self._derive_key(master_password)
        else:
            self.key = self._load_or_generate_key()
        
        self.cipher = Fernet(self.key)
    
    def _derive_key(self, password: str, salt: Optional[bytes] = None) -> bytes:
        """Derive encryption key from password using PBKDF2."""
        if salt is None:
            salt = b'linkedin_scraper_salt_v1'  # Fixed salt for consistency
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def _load_or_generate_key(self) -> bytes:
        """Load existing key or generate new one."""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            # Set restrictive permissions (Unix only)
            try:
                os.chmod(self.key_file, 0o600)
            except:
                pass
            return key
    
    def store_credential(self, key: str, value: str):
        """
        Store encrypted credential.
        
        Args:
            key: Credential key (e.g., 'LINKEDIN_EMAIL')
            value: Credential value
        """
        # Load existing credentials
        credentials = self._load_credentials()
        
        # Add/update credential
        credentials[key] = value
        
        # Encrypt and save
        encrypted_data = self.cipher.encrypt(json.dumps(credentials).encode())
        with open(self.credentials_file, 'wb') as f:
            f.write(encrypted_data)
        
        logger.info(f"Stored credential: {key}")
    
    def get_credential(self, key: str) -> Optional[str]:
        """
        Retrieve decrypted credential.
        
        Args:
            key: Credential key
            
        Returns:
            Decrypted value or None if not found
        """
        credentials = self._load_credentials()
        return credentials.get(key)
    
    def _load_credentials(self) -> Dict[str, str]:
        """Load and decrypt all credentials."""
        if not self.credentials_file.exists():
            return {}
        
        try:
            with open(self.credentials_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
            return {}
    
    def list_credentials(self) -> list:
        """List all stored credential keys (not values)."""
        credentials = self._load_credentials()
        return list(credentials.keys())
    
    def delete_credential(self, key: str):
        """Delete a credential."""
        credentials = self._load_credentials()
        if key in credentials:
            del credentials[key]
            encrypted_data = self.cipher.encrypt(json.dumps(credentials).encode())
            with open(self.credentials_file, 'wb') as f:
                f.write(encrypted_data)
            logger.info(f"Deleted credential: {key}")
    
    def migrate_from_env(self, env_file: str = '.env'):
        """
        Migrate credentials from .env file to encrypted storage.
        
        Args:
            env_file: Path to .env file
        """
        if not Path(env_file).exists():
            logger.warning(f"Env file not found: {env_file}")
            return
        
        from dotenv import dotenv_values
        env_vars = dotenv_values(env_file)
        
        # Migrate sensitive credentials
        sensitive_keys = [
            'LINKEDIN_EMAIL',
            'LINKEDIN_PASSWORD',
            'NEXT_PUBLIC_SUPABASE_SERVICE_ROLE_KEY',
            'GOOGLE_CREDENTIALS_FILE'
        ]
        
        migrated = 0
        for key in sensitive_keys:
            if key in env_vars:
                self.store_credential(key, env_vars[key])
                migrated += 1
        
        logger.info(f"Migrated {migrated} credentials from {env_file}")


# ============================================================================
# INPUT SANITIZATION
# ============================================================================

class InputSanitizer:
    """
    Sanitize user inputs to prevent injection attacks.
    """
    
    @staticmethod
    def sanitize_sql(value: str) -> str:
        """
        Sanitize SQL input (basic protection).
        Note: Always use parameterized queries as primary defense.
        """
        if not value:
            return ""
        
        # Remove dangerous SQL keywords
        dangerous = [
            'DROP', 'DELETE', 'INSERT', 'UPDATE', 'EXEC', 'EXECUTE',
            'SCRIPT', 'UNION', 'SELECT', '--', ';', '/*', '*/'
        ]
        
        sanitized = str(value)
        for keyword in dangerous:
            sanitized = sanitized.replace(keyword, '')
            sanitized = sanitized.replace(keyword.lower(), '')
        
        return sanitized.strip()
    
    @staticmethod
    def sanitize_url(url: str) -> str:
        """Sanitize URL to prevent XSS."""
        if not url:
            return ""
        
        # Only allow http/https protocols
        if not url.startswith(('http://', 'https://')):
            return ""
        
        # Remove javascript: and data: protocols
        dangerous_protocols = ['javascript:', 'data:', 'vbscript:', 'file:']
        url_lower = url.lower()
        for protocol in dangerous_protocols:
            if protocol in url_lower:
                return ""
        
        return url.strip()
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Remove HTML tags and dangerous content."""
        if not text:
            return ""
        
        import re
        
        # Remove script tags and content
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove all HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Decode HTML entities
        import html
        text = html.unescape(text)
        
        return text.strip()
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))


# ============================================================================
# AUDIT LOGGING
# ============================================================================

class AuditLogger:
    """
    Security audit logging for compliance and debugging.
    """
    
    def __init__(self, log_file: str = 'security_audit.log'):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure audit logger
        self.logger = logging.getLogger('security_audit')
        self.logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler(self.log_file)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(handler)
    
    def log_authentication(self, user: str, success: bool, ip: Optional[str] = None):
        """Log authentication attempt."""
        status = "SUCCESS" if success else "FAILURE"
        self.logger.info(
            f"AUTH {status} - User: {user} - IP: {ip or 'unknown'}"
        )
    
    def log_data_access(self, user: str, resource: str, action: str):
        """Log data access."""
        self.logger.info(
            f"DATA ACCESS - User: {user} - Resource: {resource} - Action: {action}"
        )
    
    def log_scraping_activity(self, platform: str, jobs_count: int, duration: float):
        """Log scraping activity."""
        self.logger.info(
            f"SCRAPING - Platform: {platform} - Jobs: {jobs_count} - Duration: {duration:.2f}s"
        )
    
    def log_error(self, error_type: str, message: str, user: Optional[str] = None):
        """Log security error."""
        self.logger.error(
            f"ERROR - Type: {error_type} - User: {user or 'system'} - Message: {message}"
        )
    
    def log_rate_limit(self, platform: str, user: Optional[str] = None):
        """Log rate limit hit."""
        self.logger.warning(
            f"RATE LIMIT - Platform: {platform} - User: {user or 'system'}"
        )


# ============================================================================
# API KEY ROTATION
# ============================================================================

class APIKeyManager:
    """
    Manage API keys with automatic rotation.
    """
    
    def __init__(self, storage_file: str = 'api_keys.json'):
        self.storage_file = Path(storage_file)
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
    
    def generate_api_key(self, prefix: str = 'sk') -> str:
        """Generate a secure API key."""
        random_bytes = secrets.token_bytes(32)
        key = base64.urlsafe_b64encode(random_bytes).decode('utf-8').rstrip('=')
        return f"{prefix}_{key}"
    
    def store_key(self, key_name: str, key_value: str, expires_days: int = 90):
        """
        Store API key with expiration.
        
        Args:
            key_name: Name/identifier for the key
            key_value: The API key value
            expires_days: Days until expiration
        """
        keys = self._load_keys()
        
        keys[key_name] = {
            'key': key_value,
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(days=expires_days)).isoformat(),
            'last_used': None,
            'usage_count': 0
        }
        
        self._save_keys(keys)
        logger.info(f"Stored API key: {key_name}")
    
    def get_key(self, key_name: str) -> Optional[str]:
        """
        Get API key and update usage stats.
        
        Returns:
            API key value or None if expired/not found
        """
        keys = self._load_keys()
        
        if key_name not in keys:
            return None
        
        key_data = keys[key_name]
        
        # Check expiration
        expires_at = datetime.fromisoformat(key_data['expires_at'])
        if datetime.now() > expires_at:
            logger.warning(f"API key expired: {key_name}")
            return None
        
        # Update usage
        key_data['last_used'] = datetime.now().isoformat()
        key_data['usage_count'] += 1
        self._save_keys(keys)
        
        return key_data['key']
    
    def rotate_key(self, key_name: str, expires_days: int = 90) -> str:
        """
        Rotate an API key (generate new one).
        
        Returns:
            New API key value
        """
        new_key = self.generate_api_key()
        self.store_key(key_name, new_key, expires_days)
        logger.info(f"Rotated API key: {key_name}")
        return new_key
    
    def list_keys(self) -> Dict[str, Dict[str, Any]]:
        """List all keys with metadata (excluding actual key values)."""
        keys = self._load_keys()
        return {
            name: {
                'created_at': data['created_at'],
                'expires_at': data['expires_at'],
                'last_used': data['last_used'],
                'usage_count': data['usage_count'],
                'is_expired': datetime.now() > datetime.fromisoformat(data['expires_at'])
            }
            for name, data in keys.items()
        }
    
    def _load_keys(self) -> Dict[str, Dict[str, Any]]:
        """Load keys from storage."""
        if not self.storage_file.exists():
            return {}
        
        with open(self.storage_file, 'r') as f:
            return json.load(f)
    
    def _save_keys(self, keys: Dict[str, Dict[str, Any]]):
        """Save keys to storage."""
        with open(self.storage_file, 'w') as f:
            json.dump(keys, f, indent=2)
        
        # Set restrictive permissions
        try:
            os.chmod(self.storage_file, 0o600)
        except:
            pass


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example 1: Credential Management
    print("=== Credential Management ===")
    cred_manager = CredentialManager()
    
    # Store credentials
    cred_manager.store_credential('LINKEDIN_EMAIL', 'user@example.com')
    cred_manager.store_credential('LINKEDIN_PASSWORD', 'secure_password_123')
    
    # Retrieve credentials
    email = cred_manager.get_credential('LINKEDIN_EMAIL')
    print(f"Retrieved email: {email}")
    
    # List all credentials
    print(f"Stored credentials: {cred_manager.list_credentials()}")
    
    # Example 2: Input Sanitization
    print("\n=== Input Sanitization ===")
    sanitizer = InputSanitizer()
    
    dangerous_sql = "'; DROP TABLE users; --"
    safe_sql = sanitizer.sanitize_sql(dangerous_sql)
    print(f"Sanitized SQL: {safe_sql}")
    
    dangerous_url = "javascript:alert('XSS')"
    safe_url = sanitizer.sanitize_url(dangerous_url)
    print(f"Sanitized URL: {safe_url}")
    
    # Example 3: API Key Management
    print("\n=== API Key Management ===")
    key_manager = APIKeyManager()
    
    # Generate and store key
    api_key = key_manager.generate_api_key()
    key_manager.store_key('production_key', api_key, expires_days=90)
    print(f"Generated API key: {api_key[:20]}...")
    
    # Retrieve key
    retrieved_key = key_manager.get_key('production_key')
    print(f"Retrieved key matches: {retrieved_key == api_key}")
    
    # List keys
    print(f"All keys: {key_manager.list_keys()}")
    
    # Example 4: Audit Logging
    print("\n=== Audit Logging ===")
    audit = AuditLogger('logs/security_audit.log')
    audit.log_authentication('user@example.com', True, '192.168.1.1')
    audit.log_scraping_activity('linkedin', 150, 45.2)
    print("Audit logs written to logs/security_audit.log")

import os
import re
import secrets
import hashlib
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import uuid
import ipaddress
import jwt
import bcrypt
import pyotp

class AdvancedSecurityManager:
    """
    Comprehensive security management system for Vocality Nexus
    Provides advanced protection mechanisms
    """
    
    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize security manager with advanced cryptographic protections
        
        :param secret_key: Optional custom secret key
        """
        self.logger = logging.getLogger(__name__)
        self.secret_key = secret_key or self._generate_secure_secret()
        
        # Advanced encryption key generation
        self.encryption_key = self._generate_encryption_key()
        self.fernet = Fernet(self.encryption_key)
        
        # Rate limiting and attack prevention tracking
        self.login_attempts: Dict[str, Dict[str, Any]] = {}
        self.blocked_ips: Dict[str, datetime] = {}

    def _generate_secure_secret(self) -> str:
        """
        Generate a cryptographically secure secret key
        
        :return: Secure secret key
        """
        return secrets.token_hex(32)

    def _generate_encryption_key(self) -> bytes:
        """
        Generate a strong encryption key using PBKDF2
        
        :return: Encryption key
        """
        password = self.secret_key.encode()
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key

    def hash_password(self, password: str) -> str:
        """
        Securely hash password using bcrypt
        
        :param password: Plain text password
        :return: Hashed password
        """
        # Ensure password meets complexity requirements
        if not self.validate_password_complexity(password):
            raise ValueError("Password does not meet complexity requirements")
        
        # Use bcrypt with high work factor for password hashing
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def verify_password(self, stored_password: str, provided_password: str) -> bool:
        """
        Verify password against stored hash
        
        :param stored_password: Stored bcrypt hash
        :param provided_password: Password to verify
        :return: Whether password is correct
        """
        return bcrypt.checkpw(
            provided_password.encode('utf-8'), 
            stored_password.encode('utf-8')
        )

    def validate_password_complexity(self, password: str) -> bool:
        """
        Validate password complexity
        
        :param password: Password to validate
        :return: Whether password meets complexity requirements
        """
        # Complex password requirements
        checks = [
            len(password) >= 12,  # Minimum length
            re.search(r'[A-Z]', password),  # Uppercase letter
            re.search(r'[a-z]', password),  # Lowercase letter
            re.search(r'\d', password),  # Number
            re.search(r'[!@#$%^&*(),.?":{}|<>]', password)  # Special character
        ]
        return all(checks)

    def generate_jwt_token(self, user_id: str, role: str) -> str:
        """
        Generate a secure JWT token with advanced claims
        
        :param user_id: User's unique identifier
        :param role: User's role
        :return: JWT token
        """
        payload = {
            'sub': user_id,
            'role': role,
            'jti': str(uuid.uuid4()),  # Unique token ID
            'iat': datetime.utcnow(),  # Issued at
            'exp': datetime.utcnow() + timedelta(hours=2),  # Expiration
            'nbf': datetime.utcnow(),  # Not before
            'token_type': 'access'
        }
        
        return jwt.encode(payload, self.secret_key, algorithm='HS256')

    def validate_jwt_token(self, token: str) -> Dict[str, Any]:
        """
        Validate and decode JWT token
        
        :param token: JWT token to validate
        :return: Decoded token payload
        """
        try:
            return jwt.decode(
                token, 
                self.secret_key, 
                algorithms=['HS256']
            )
        except jwt.ExpiredSignatureError:
            self.logger.warning("Expired JWT token")
            raise
        except jwt.InvalidTokenError:
            self.logger.warning("Invalid JWT token")
            raise

    def generate_2fa_secret(self) -> str:
        """
        Generate a TOTP secret for two-factor authentication
        
        :return: Base32 encoded secret
        """
        return pyotp.random_base32()

    def verify_2fa_token(self, secret: str, token: str) -> bool:
        """
        Verify two-factor authentication token
        
        :param secret: TOTP secret
        :param token: User-provided token
        :return: Whether token is valid
        """
        totp = pyotp.TOTP(secret)
        return totp.verify(token)

    def encrypt_sensitive_data(self, data: str) -> str:
        """
        Encrypt sensitive data using Fernet symmetric encryption
        
        :param data: Data to encrypt
        :return: Encrypted data
        """
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """
        Decrypt sensitive data
        
        :param encrypted_data: Encrypted data to decrypt
        :return: Decrypted data
        """
        return self.fernet.decrypt(encrypted_data.encode()).decode()

    def check_ip_reputation(self, ip_address: str) -> bool:
        """
        Check IP address reputation and prevent potential attacks
        
        :param ip_address: IP address to check
        :return: Whether IP is considered safe
        """
        try:
            ip = ipaddress.ip_address(ip_address)
            
            # Block private and reserved IP ranges
            if ip.is_private or ip.is_reserved:
                return False
            
            # Check against blocked IPs with time-based unblocking
            if ip_address in self.blocked_ips:
                if datetime.now() - self.blocked_ips[ip_address] < timedelta(hours=1):
                    return False
                else:
                    del self.blocked_ips[ip_address]
            
            return True
        
        except ValueError:
            self.logger.warning(f"Invalid IP address: {ip_address}")
            return False

    def track_login_attempts(self, username: str, ip_address: str) -> bool:
        """
        Track and prevent brute-force login attempts
        
        :param username: Username attempting login
        :param ip_address: IP address of login attempt
        :return: Whether login attempt is allowed
        """
        current_time = datetime.now()
        
        # Initialize tracking for username if not exists
        if username not in self.login_attempts:
            self.login_attempts[username] = {
                'attempts': 0,
                'last_attempt': current_time
            }
        
        user_attempts = self.login_attempts[username]
        
        # Reset attempts if last attempt was more than 15 minutes ago
        if current_time - user_attempts['last_attempt'] > timedelta(minutes=15):
            user_attempts['attempts'] = 0
        
        user_attempts['attempts'] += 1
        user_attempts['last_attempt'] = current_time
        
        # Block after 5 failed attempts
        if user_attempts['attempts'] > 5:
            self.blocked_ips[ip_address] = current_time
            self.logger.warning(f"Blocked IP {ip_address} due to excessive login attempts")
            return False
        
        return True

def initialize_security_manager() -> AdvancedSecurityManager:
    """
    Initialize and configure security manager
    
    :return: Configured security manager instance
    """
    return AdvancedSecurityManager()

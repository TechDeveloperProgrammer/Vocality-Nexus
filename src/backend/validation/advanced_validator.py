import os
import re
import json
import logging
from typing import Dict, Any, Optional, Union, List, Callable
import jsonschema
import phonenumbers
import email_validator
import bleach
import unicodedata
import secrets
import string
import hashlib
import base64

class AdvancedDataValidator:
    """
    Comprehensive data validation and sanitization utility
    Supports multiple validation and sanitization strategies
    """
    
    def __init__(self, 
                 schema_dir: str = 'validation_schemas',
                 log_dir: str = 'validation_logs'):
        """
        Initialize advanced data validator
        
        :param schema_dir: Directory for JSON schemas
        :param log_dir: Directory for validation logs
        """
        # Logging configuration
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Directories
        self.schema_dir = schema_dir
        self.log_dir = log_dir
        
        os.makedirs(schema_dir, exist_ok=True)
        os.makedirs(log_dir, exist_ok=True)
        
        # Validation schemas cache
        self._schemas: Dict[str, Dict[str, Any]] = {}

    def load_schema(self, schema_name: str) -> Dict[str, Any]:
        """
        Load JSON schema from file
        
        :param schema_name: Name of the schema
        :return: Parsed JSON schema
        """
        if schema_name in self._schemas:
            return self._schemas[schema_name]
        
        # Try different file extensions
        for ext in ['.json', '.jsonschema']:
            schema_path = os.path.join(self.schema_dir, f'{schema_name}{ext}')
            
            if os.path.exists(schema_path):
                with open(schema_path, 'r') as f:
                    schema = json.load(f)
                
                self._schemas[schema_name] = schema
                return schema
        
        raise FileNotFoundError(f"Schema {schema_name} not found")

    def validate_data(self, 
                      data: Any, 
                      schema_name: Optional[str] = None, 
                      custom_schema: Optional[Dict[str, Any]] = None) -> bool:
        """
        Validate data against JSON schema
        
        :param data: Data to validate
        :param schema_name: Name of predefined schema
        :param custom_schema: Optional custom schema
        :return: Whether data is valid
        """
        try:
            # Determine schema
            if schema_name:
                schema = self.load_schema(schema_name)
            elif custom_schema:
                schema = custom_schema
            else:
                raise ValueError("No schema provided")
            
            # Validate against schema
            jsonschema.validate(instance=data, schema=schema)
            return True
        
        except jsonschema.ValidationError as e:
            self.logger.error(f"Schema validation error: {e}")
            self._log_validation_error(data, e)
            return False

    def _log_validation_error(self, data: Any, error: jsonschema.ValidationError):
        """
        Log validation error details
        
        :param data: Data that failed validation
        :param error: Validation error
        """
        log_file = os.path.join(
            self.log_dir, 
            f'validation_error_{secrets.token_hex(8)}.json'
        )
        
        with open(log_file, 'w') as f:
            json.dump({
                'timestamp': time.time(),
                'data': data,
                'error': {
                    'message': error.message,
                    'path': list(error.path),
                    'validator': error.validator,
                    'validator_value': error.validator_value
                }
            }, f, indent=2)

    def sanitize_input(self, 
                       data: Union[str, Dict[str, Any]], 
                       sanitization_rules: Optional[Dict[str, str]] = None) -> Union[str, Dict[str, Any]]:
        """
        Sanitize input data
        
        :param data: Data to sanitize
        :param sanitization_rules: Optional custom sanitization rules
        :return: Sanitized data
        """
        # Default sanitization rules
        default_rules = {
            'html': self._sanitize_html,
            'text': self._sanitize_text,
            'email': self._sanitize_email,
            'phone': self._sanitize_phone_number
        }
        
        # Merge default and custom rules
        rules = {**default_rules, **(sanitization_rules or {})}
        
        # Recursive sanitization for dictionaries
        if isinstance(data, dict):
            return {
                k: self.sanitize_input(v, rules) 
                for k, v in data.items()
            }
        
        # String sanitization
        if isinstance(data, str):
            # Apply all sanitization rules
            for rule_type, sanitizer in rules.items():
                data = sanitizer(data)
        
        return data

    def _sanitize_html(self, html: str) -> str:
        """
        Sanitize HTML input
        
        :param html: HTML string to sanitize
        :return: Sanitized HTML
        """
        return bleach.clean(
            html, 
            tags=['p', 'b', 'i', 'u', 'em', 'strong', 'a'],
            attributes={'a': ['href', 'title']}
        )

    def _sanitize_text(self, text: str) -> str:
        """
        Sanitize plain text
        
        :param text: Text to sanitize
        :return: Sanitized text
        """
        # Remove control characters
        text = ''.join(
            char for char in text 
            if not unicodedata.category(char).startswith('C')
        )
        
        # Normalize unicode
        text = unicodedata.normalize('NFKD', text)
        
        # Remove non-printable characters
        text = re.sub(r'[^\x20-\x7E]', '', text)
        
        return text.strip()

    def _sanitize_email(self, email: str) -> Optional[str]:
        """
        Sanitize and validate email
        
        :param email: Email to sanitize
        :return: Sanitized email or None
        """
        try:
            # Normalize and validate email
            normalized_email = email_validator.normalize_email(email)
            email_validator.validate_email(normalized_email)
            return normalized_email
        except email_validator.EmailNotValidError:
            return None

    def _sanitize_phone_number(self, phone: str) -> Optional[str]:
        """
        Sanitize and validate phone number
        
        :param phone: Phone number to sanitize
        :return: Sanitized phone number or None
        """
        try:
            # Parse phone number
            parsed_number = phonenumbers.parse(phone, None)
            
            if phonenumbers.is_valid_number(parsed_number):
                return phonenumbers.format_number(
                    parsed_number, 
                    phonenumbers.PhoneNumberFormat.E164
                )
            return None
        except Exception:
            return None

    def generate_secure_token(self, 
                               length: int = 32, 
                               include_punctuation: bool = False) -> str:
        """
        Generate cryptographically secure random token
        
        :param length: Token length
        :param include_punctuation: Whether to include punctuation
        :return: Secure random token
        """
        # Character sets
        chars = string.ascii_letters + string.digits
        if include_punctuation:
            chars += string.punctuation
        
        # Generate secure token
        return ''.join(
            secrets.choice(chars) for _ in range(length)
        )

    def hash_data(self, 
                  data: Any, 
                  algorithm: str = 'sha256', 
                  salt: Optional[str] = None) -> str:
        """
        Hash data with optional salt
        
        :param data: Data to hash
        :param algorithm: Hashing algorithm
        :param salt: Optional salt value
        :return: Hashed data
        """
        # Convert data to string
        data_str = json.dumps(data, sort_keys=True)
        
        # Add optional salt
        if salt:
            data_str += salt
        
        # Hash using specified algorithm
        if algorithm == 'sha256':
            return hashlib.sha256(data_str.encode()).hexdigest()
        elif algorithm == 'sha512':
            return hashlib.sha512(data_str.encode()).hexdigest()
        elif algorithm == 'blake2b':
            return hashlib.blake2b(data_str.encode()).hexdigest()
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")

    def encrypt_data(self, 
                     data: Any, 
                     encryption_key: Optional[bytes] = None) -> str:
        """
        Encrypt data using Fernet symmetric encryption
        
        :param data: Data to encrypt
        :param encryption_key: Optional encryption key
        :return: Base64 encoded encrypted data
        """
        from cryptography.fernet import Fernet
        
        # Generate key if not provided
        key = encryption_key or Fernet.generate_key()
        fernet = Fernet(key)
        
        # Encrypt data
        encrypted_data = fernet.encrypt(
            json.dumps(data).encode()
        )
        
        return base64.b64encode(encrypted_data).decode()

def create_data_validator(
    schema_dir: str = 'validation_schemas',
    log_dir: str = 'validation_logs'
) -> AdvancedDataValidator:
    """
    Factory method to create data validator
    
    :param schema_dir: Directory for JSON schemas
    :param log_dir: Directory for validation logs
    :return: Configured data validator
    """
    return AdvancedDataValidator(
        schema_dir, 
        log_dir
    )

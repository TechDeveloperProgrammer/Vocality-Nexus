import re
import hashlib
import secrets
import logging
from typing import Dict, Any, Union, Optional
import numpy as np
import pandas as pd
from faker import Faker
from cryptography.fernet import Fernet

class AdvancedDataAnonymizer:
    """
    Comprehensive data anonymization utility
    Supports multiple anonymization strategies
    """
    
    def __init__(self, 
                 encryption_key: Optional[bytes] = None,
                 fake_locale: str = 'en_US'):
        """
        Initialize data anonymizer
        
        :param encryption_key: Optional encryption key
        :param fake_locale: Locale for fake data generation
        """
        self.logger = logging.getLogger(__name__)
        
        # Encryption setup
        self.encryption_key = encryption_key or Fernet.generate_key()
        self.fernet = Fernet(self.encryption_key)
        
        # Faker for generating realistic fake data
        self.faker = Faker(fake_locale)
        
        # Anonymization strategies
        self.anonymization_strategies = {
            'hash': self._hash_anonymize,
            'encrypt': self._encrypt_anonymize,
            'pseudonymize': self._pseudonymize,
            'generalize': self._generalize
        }

    def anonymize(self, 
                  data: Union[Dict[str, Any], pd.DataFrame], 
                  strategy: str = 'hash', 
                  fields: Optional[Dict[str, Any]] = None) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        Anonymize data using specified strategy
        
        :param data: Data to anonymize
        :param strategy: Anonymization strategy
        :param fields: Specific fields and their anonymization rules
        :return: Anonymized data
        """
        # Validate strategy
        if strategy not in self.anonymization_strategies:
            raise ValueError(f"Unsupported anonymization strategy: {strategy}")
        
        # Handle different data types
        if isinstance(data, dict):
            return self._anonymize_dict(data, strategy, fields)
        elif isinstance(data, pd.DataFrame):
            return self._anonymize_dataframe(data, strategy, fields)
        else:
            raise TypeError("Unsupported data type for anonymization")

    def _anonymize_dict(self, 
                         data: Dict[str, Any], 
                         strategy: str, 
                         fields: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Anonymize dictionary data
        
        :param data: Dictionary to anonymize
        :param strategy: Anonymization strategy
        :param fields: Specific field anonymization rules
        :return: Anonymized dictionary
        """
        anonymized_data = data.copy()
        fields = fields or {}
        
        for key, value in data.items():
            # Check if specific field has custom anonymization
            field_strategy = fields.get(key, strategy)
            
            # Apply anonymization
            anonymized_data[key] = self.anonymization_strategies[field_strategy](value)
        
        return anonymized_data

    def _anonymize_dataframe(self, 
                              data: pd.DataFrame, 
                              strategy: str, 
                              fields: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """
        Anonymize DataFrame
        
        :param data: DataFrame to anonymize
        :param strategy: Anonymization strategy
        :param fields: Specific field anonymization rules
        :return: Anonymized DataFrame
        """
        anonymized_df = data.copy()
        fields = fields or {}
        
        for column in data.columns:
            # Check if specific column has custom anonymization
            column_strategy = fields.get(column, strategy)
            
            # Apply anonymization
            anonymized_df[column] = data[column].apply(
                lambda x: self.anonymization_strategies[column_strategy](x)
            )
        
        return anonymized_df

    def _hash_anonymize(self, value: Any) -> str:
        """
        Hash-based anonymization
        
        :param value: Value to anonymize
        :return: Hashed value
        """
        if value is None:
            return None
        
        return hashlib.sha256(str(value).encode()).hexdigest()

    def _encrypt_anonymize(self, value: Any) -> Optional[str]:
        """
        Encryption-based anonymization
        
        :param value: Value to anonymize
        :return: Encrypted value
        """
        if value is None:
            return None
        
        try:
            return self.fernet.encrypt(str(value).encode()).decode()
        except Exception as e:
            self.logger.error(f"Encryption error: {e}")
            return None

    def _pseudonymize(self, value: Any) -> str:
        """
        Pseudonymization with consistent mapping
        
        :param value: Value to pseudonymize
        :return: Pseudonymized value
        """
        if value is None:
            return None
        
        # Use a consistent hash-based mapping
        seed = hashlib.md5(str(value).encode()).digest()
        np.random.seed(int.from_bytes(seed, byteorder='big'))
        
        # Generate realistic fake data
        fake_generators = [
            self.faker.name,
            self.faker.email,
            self.faker.user_name,
            self.faker.uuid4
        ]
        
        return np.random.choice(fake_generators)()

    def _generalize(self, value: Any) -> Any:
        """
        Generalize sensitive data
        
        :param value: Value to generalize
        :return: Generalized value
        """
        if value is None:
            return None
        
        # Age generalization
        if isinstance(value, (int, float)) and 0 < value < 120:
            return round(value / 10) * 10
        
        # Phone number generalization
        if isinstance(value, str):
            # Remove specific digits from phone numbers
            phone_pattern = r'^\+?1?\d{3,4}[-.]?\d{3}[-.]?(\d{4})$'
            match = re.match(phone_pattern, str(value))
            if match:
                return f"***-***-{match.group(1)}"
            
            # Email generalization
            email_pattern = r'^[^@]+@([^@]+)$'
            email_match = re.match(email_pattern, str(value))
            if email_match:
                return f"user@{email_match.group(1)}"
        
        return value

    def decrypt(self, encrypted_value: str) -> Optional[str]:
        """
        Decrypt previously encrypted value
        
        :param encrypted_value: Encrypted value
        :return: Decrypted value
        """
        try:
            return self.fernet.decrypt(encrypted_value.encode()).decode()
        except Exception as e:
            self.logger.error(f"Decryption error: {e}")
            return None

def create_data_anonymizer(
    encryption_key: Optional[bytes] = None,
    fake_locale: str = 'en_US'
) -> AdvancedDataAnonymizer:
    """
    Factory method to create data anonymizer
    
    :param encryption_key: Optional encryption key
    :param fake_locale: Locale for fake data generation
    :return: Configured data anonymizer
    """
    return AdvancedDataAnonymizer(
        encryption_key, 
        fake_locale
    )

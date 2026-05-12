# Copyright (c) 2024 AnyCompany. All rights reserved.
# Customer Data Models
# Defines data structures for customer records

from dataclasses import dataclass
from typing import Optional


@dataclass
class Customer:
    """
    Customer data model.
    
    Represents a customer record with all required and optional fields.
    Provides serialization methods for DynamoDB integration.
    
    Attributes:
        customer_id: Unique customer identifier (UUID)
        name: Customer name (required)
        email: Customer email address (required)
        created_at: ISO 8601 timestamp when customer was created
        updated_at: ISO 8601 timestamp when customer was last updated
        phone: Customer phone number (optional)
        address: Customer address (optional)
        company: Customer company name (optional)
        notes: Additional notes about the customer (optional)
    """
    customer_id: str
    name: str
    email: str
    created_at: str
    updated_at: str
    phone: Optional[str] = None
    address: Optional[str] = None
    company: Optional[str] = None
    notes: Optional[str] = None
    
    def to_dict(self) -> dict:
        """
        Convert Customer instance to dictionary for DynamoDB serialization.
        
        Returns:
            Dictionary containing all customer fields with their values.
            Optional fields are included even if None to maintain consistent schema.
        
        Example:
            >>> customer = Customer(
            ...     customer_id="123",
            ...     name="John Doe",
            ...     email="john@example.com",
            ...     created_at="2024-01-15T10:00:00Z",
            ...     updated_at="2024-01-15T10:00:00Z"
            ... )
            >>> customer.to_dict()
            {
                'customer_id': '123',
                'name': 'John Doe',
                'email': 'john@example.com',
                'phone': None,
                'address': None,
                'company': None,
                'notes': None,
                'created_at': '2024-01-15T10:00:00Z',
                'updated_at': '2024-01-15T10:00:00Z'
            }
        """
        return {
            'customer_id': self.customer_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'company': self.company,
            'notes': self.notes,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Customer':
        """
        Create Customer instance from dictionary (DynamoDB deserialization).
        
        Args:
            data: Dictionary containing customer fields from DynamoDB.
                  Must contain required fields: customer_id, name, email,
                  created_at, updated_at. Optional fields default to None.
        
        Returns:
            Customer instance populated with data from dictionary.
        
        Raises:
            KeyError: If required fields are missing from data dictionary.
        
        Example:
            >>> data = {
            ...     'customer_id': '123',
            ...     'name': 'John Doe',
            ...     'email': 'john@example.com',
            ...     'created_at': '2024-01-15T10:00:00Z',
            ...     'updated_at': '2024-01-15T10:00:00Z',
            ...     'phone': '+1234567890'
            ... }
            >>> customer = Customer.from_dict(data)
            >>> customer.name
            'John Doe'
        """
        return cls(
            customer_id=data['customer_id'],
            name=data['name'],
            email=data['email'],
            phone=data.get('phone'),
            address=data.get('address'),
            company=data.get('company'),
            notes=data.get('notes'),
            created_at=data['created_at'],
            updated_at=data['updated_at']
        )

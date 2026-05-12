# Copyright (c) 2024 AnyCompany. All rights reserved.
# Unit Tests for Customer Data Model
# Tests serialization and deserialization methods

import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'customers'))

from models import Customer


def test_customer_to_dict_with_all_fields():
    """Test Customer.to_dict() with all fields populated."""
    customer = Customer(
        customer_id="test-123",
        name="John Doe",
        email="john@example.com",
        phone="+1234567890",
        address="123 Main St",
        company="Acme Corp",
        notes="VIP customer",
        created_at="2024-01-15T10:00:00Z",
        updated_at="2024-01-15T12:00:00Z"
    )
    
    result = customer.to_dict()
    
    assert result['customer_id'] == "test-123"
    assert result['name'] == "John Doe"
    assert result['email'] == "john@example.com"
    assert result['phone'] == "+1234567890"
    assert result['address'] == "123 Main St"
    assert result['company'] == "Acme Corp"
    assert result['notes'] == "VIP customer"
    assert result['created_at'] == "2024-01-15T10:00:00Z"
    assert result['updated_at'] == "2024-01-15T12:00:00Z"


def test_customer_to_dict_with_required_fields_only():
    """Test Customer.to_dict() with only required fields."""
    customer = Customer(
        customer_id="test-456",
        name="Jane Smith",
        email="jane@example.com",
        created_at="2024-01-15T10:00:00Z",
        updated_at="2024-01-15T10:00:00Z"
    )
    
    result = customer.to_dict()
    
    assert result['customer_id'] == "test-456"
    assert result['name'] == "Jane Smith"
    assert result['email'] == "jane@example.com"
    assert result['phone'] is None
    assert result['address'] is None
    assert result['company'] is None
    assert result['notes'] is None
    assert result['created_at'] == "2024-01-15T10:00:00Z"
    assert result['updated_at'] == "2024-01-15T10:00:00Z"


def test_customer_from_dict_with_all_fields():
    """Test Customer.from_dict() with all fields populated."""
    data = {
        'customer_id': "test-789",
        'name': "Bob Johnson",
        'email': "bob@example.com",
        'phone': "+9876543210",
        'address': "456 Oak Ave",
        'company': "Tech Inc",
        'notes': "Prefers email contact",
        'created_at': "2024-01-15T10:00:00Z",
        'updated_at': "2024-01-15T14:00:00Z"
    }
    
    customer = Customer.from_dict(data)
    
    assert customer.customer_id == "test-789"
    assert customer.name == "Bob Johnson"
    assert customer.email == "bob@example.com"
    assert customer.phone == "+9876543210"
    assert customer.address == "456 Oak Ave"
    assert customer.company == "Tech Inc"
    assert customer.notes == "Prefers email contact"
    assert customer.created_at == "2024-01-15T10:00:00Z"
    assert customer.updated_at == "2024-01-15T14:00:00Z"


def test_customer_from_dict_with_required_fields_only():
    """Test Customer.from_dict() with only required fields."""
    data = {
        'customer_id': "test-101",
        'name': "Alice Brown",
        'email': "alice@example.com",
        'created_at': "2024-01-15T10:00:00Z",
        'updated_at': "2024-01-15T10:00:00Z"
    }
    
    customer = Customer.from_dict(data)
    
    assert customer.customer_id == "test-101"
    assert customer.name == "Alice Brown"
    assert customer.email == "alice@example.com"
    assert customer.phone is None
    assert customer.address is None
    assert customer.company is None
    assert customer.notes is None
    assert customer.created_at == "2024-01-15T10:00:00Z"
    assert customer.updated_at == "2024-01-15T10:00:00Z"


def test_customer_round_trip_serialization():
    """Test that to_dict() and from_dict() are inverse operations."""
    original = Customer(
        customer_id="test-202",
        name="Charlie Davis",
        email="charlie@example.com",
        phone="+1122334455",
        address="789 Pine Rd",
        company="Global Ltd",
        notes="Important client",
        created_at="2024-01-15T10:00:00Z",
        updated_at="2024-01-15T16:00:00Z"
    )
    
    # Serialize to dict and back
    data = original.to_dict()
    restored = Customer.from_dict(data)
    
    # Verify all fields match
    assert restored.customer_id == original.customer_id
    assert restored.name == original.name
    assert restored.email == original.email
    assert restored.phone == original.phone
    assert restored.address == original.address
    assert restored.company == original.company
    assert restored.notes == original.notes
    assert restored.created_at == original.created_at
    assert restored.updated_at == original.updated_at


def test_customer_from_dict_missing_required_field():
    """Test Customer.from_dict() raises KeyError when required field is missing."""
    data = {
        'customer_id': "test-303",
        'name': "Missing Email",
        # email is missing
        'created_at': "2024-01-15T10:00:00Z",
        'updated_at': "2024-01-15T10:00:00Z"
    }
    
    try:
        Customer.from_dict(data)
        assert False, "Expected KeyError for missing required field"
    except KeyError as e:
        assert 'email' in str(e)


def test_customer_to_dict_includes_all_keys():
    """Test that to_dict() includes all expected keys even when optional fields are None."""
    customer = Customer(
        customer_id="test-404",
        name="Test User",
        email="test@example.com",
        created_at="2024-01-15T10:00:00Z",
        updated_at="2024-01-15T10:00:00Z"
    )
    
    result = customer.to_dict()
    
    # Verify all expected keys are present
    expected_keys = {
        'customer_id', 'name', 'email', 'phone', 'address', 
        'company', 'notes', 'created_at', 'updated_at'
    }
    assert set(result.keys()) == expected_keys

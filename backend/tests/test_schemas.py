"""
Pydantic schemas validation tests.
"""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from backend.app.schemas.transaction import (
    TransactionCreate,
    TransactionType,
    TransactionStatus,
)
from backend.app.schemas.account import AccountCreate, AccountType, AccountStatus
from backend.app.schemas.alert import AlertCreate, AlertSeverity, AlertStatus


def test_valid_transaction_schema():
    payload = {
        "transaction_id": "TXN_1001",
        "sender_account_id": "ACC_SENDER_01",
        "receiver_account_id": "ACC_RECEIVER_02",
        "amount": 45000.50,
        "currency": "INR",
        "transaction_type": "UPI",
        "timestamp": datetime.now(timezone.utc),
        "channel": "mobile_app",
        "location": "Lucknow, UP",
        "transaction_status": "COMPLETED",
    }
    tx = TransactionCreate(**payload)
    assert tx.transaction_id == "TXN_1001"
    assert tx.amount == 45000.50
    assert tx.transaction_type == TransactionType.UPI


def test_invalid_transaction_negative_amount():
    payload = {
        "transaction_id": "TXN_BAD",
        "sender_account_id": "ACC_01",
        "receiver_account_id": "ACC_02",
        "amount": -50.0,  # Invalid: must be gt=0
        "currency": "INR",
        "transaction_type": "UPI",
        "timestamp": datetime.now(timezone.utc),
        "channel": "mobile_app",
        "location": "Mumbai",
    }
    with pytest.raises(ValidationError):
        TransactionCreate(**payload)


def test_valid_account_schema():
    acc = AccountCreate(
        account_id="ACC_USER_99",
        account_type=AccountType.SAVINGS,
        account_status=AccountStatus.ACTIVE,
    )
    assert acc.account_id == "ACC_USER_99"
    assert acc.account_type == AccountType.SAVINGS


def test_valid_security_alert_schema():
    alert = AlertCreate(
        alert_id="ALT_9001",
        transaction_id="TXN_1001",
        account_id="ACC_SENDER_01",
        alert_type="AML_STRUCTURING",
        severity=AlertSeverity.HIGH,
        risk_score=78.5,
        explanation="Rapid successive transfers just below threshold of 50,000 INR.",
    )
    assert alert.risk_score == 78.5
    assert alert.severity == AlertSeverity.HIGH
    assert alert.status == AlertStatus.OPEN


def test_invalid_alert_score_out_of_bounds():
    with pytest.raises(ValidationError):
        AlertCreate(
            alert_id="ALT_BAD",
            account_id="ACC_01",
            alert_type="FRAUD",
            severity=AlertSeverity.CRITICAL,
            risk_score=150.0,  # Invalid: max is 100
            explanation="Invalid score test",
        )


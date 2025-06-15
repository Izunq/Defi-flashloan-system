#!/usr/bin/env python3
"""
Compliance Framework for Institutional-Grade Arbitrage System
============================================================

This module provides KYC/AML compliance features for the arbitrage system:
- KYC verification integration
- AML monitoring and reporting
- Geographic restrictions
- Regulatory reporting
- Audit trail system
- Halal compliance verification
"""

import os
import json
import hashlib
import logging
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
import pandas as pd
import numpy as np
from web3 import Web3
from web3.types import ChecksumAddress
import sqlite3
import uuid
import hmac
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("compliance.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("COMPLIANCE")

# Constants
KYC_PROVIDERS = {
    "onfido": "https://api.onfido.com/v3/",
    "sumsub": "https://api.sumsub.com/",
    "sardine": "https://api.sardine.ai/v1/",
    "persona": "https://withpersona.com/api/v1/",
    "jumio": "https://netverify.com/api/v4/"
}

AML_PROVIDERS = {
    "chainalysis": "https://api.chainalysis.com/",
    "elliptic": "https://api.elliptic.co/",
    "coinfirm": "https://api.coinfirm.com/v3/",
    "merkle_science": "https://api.merklescience.com/"
}

RESTRICTED_COUNTRIES = {
    "US": ["NY", "WA"],  # Restricted states in the US
    "CN": [],  # All of China restricted
    "IR": [],  # All of Iran restricted
    "CU": [],  # All of Cuba restricted
    "KP": [],  # All of North Korea restricted
    "SY": []   # All of Syria restricted
}

REGULATORY_REPORTING_THRESHOLDS = {
    "USD": 10000,  # Report transactions over $10,000
    "EUR": 10000,  # Report transactions over €10,000
    "GBP": 8500,   # Report transactions over £8,500
    "ETH": 5,      # Report transactions over 5 ETH
    "BTC": 0.5     # Report transactions over 0.5 BTC
}

# Database paths
KYC_DB_PATH = "compliance/kyc_database.db"
AML_DB_PATH = "compliance/aml_database.db"
AUDIT_DB_PATH = "compliance/audit_trail.db"
HALAL_DB_PATH = "compliance/halal_compliance.db"

# Encryption key environment variable
ENCRYPTION_KEY_ENV = "COMPLIANCE_ENCRYPTION_KEY"

@dataclass
class UserProfile:
    """User profile with KYC/AML information"""
    user_id: str
    wallet_address: str
    kyc_status: str  # "pending", "approved", "rejected"
    kyc_level: int  # 1, 2, 3 (increasing verification levels)
    kyc_expiry: Optional[datetime] = None
    kyc_provider: Optional[str] = None
    kyc_reference_id: Optional[str] = None
    aml_status: str = "pending"  # "pending", "approved", "flagged", "blocked"
    aml_risk_score: float = 0.0  # 0.0 to 1.0
    aml_last_check: Optional[datetime] = None
    country_code: Optional[str] = None
    region_code: Optional[str] = None
    is_restricted: bool = False
    trading_limits: Dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    halal_compliance: bool = False
    additional_data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ComplianceEvent:
    """Compliance event for audit trail"""
    event_id: str
    event_type: str  # "kyc_update", "aml_check", "transaction_review", etc.
    user_id: Optional[str]
    wallet_address: Optional[str]
    timestamp: datetime
    details: Dict[str, Any]
    related_tx_hash: Optional[str] = None
    risk_score: Optional[float] = None
    action_taken: Optional[str] = None
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None

@dataclass
class RegulatoryReport:
    """Regulatory report for compliance reporting"""
    report_id: str
    report_type: str  # "SAR", "CTR", "STR", etc.
    user_id: Optional[str]
    wallet_address: Optional[str]
    transaction_hash: Optional[str]
    amount: float
    currency: str
    timestamp: datetime
    reason: str
    status: str  # "pending", "submitted", "acknowledged"
    submission_date: Optional[datetime] = None
    reference_number: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)

class EncryptionManager:
    """Manager for encrypting sensitive compliance data"""
    
    def __init__(self):
        # Get encryption key from environment
        encryption_key = os.environ.get(ENCRYPTION_KEY_ENV)
        
        if not encryption_key:
            # Generate a key if not provided
            logger.warning("No encryption key found in environment, generating a temporary one")
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000
            )
            encryption_key = base64.urlsafe_b64encode(kdf.derive(b"temporary_key"))
        
        if isinstance(encryption_key, str):
            encryption_key = encryption_key.encode()
        
        self.fernet = Fernet(encryption_key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data"""
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        return self.fernet.decrypt(encrypted_data.encode()).decode()

class DatabaseManager:
    """Manager for compliance databases"""
    
    def __init__(self):
        self.encryption = EncryptionManager()
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(KYC_DB_PATH), exist_ok=True)
        os.makedirs(os.path.dirname(AML_DB_PATH), exist_ok=True)
        os.makedirs(os.path.dirname(AUDIT_DB_PATH), exist_ok=True)
        os.makedirs(os.path.dirname(HALAL_DB_PATH), exist_ok=True)
        
        # Initialize databases
        self._init_kyc_db()
        self._init_aml_db()
        self._init_audit_db()
        self._init_halal_db()
    
    def _init_kyc_db(self):
        """Initialize KYC database"""
        conn = sqlite3.connect(KYC_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            wallet_address TEXT UNIQUE,
            kyc_status TEXT,
            kyc_level INTEGER,
            kyc_expiry TEXT,
            kyc_provider TEXT,
            kyc_reference_id TEXT,
            country_code TEXT,
            region_code TEXT,
            is_restricted INTEGER,
            created_at TEXT,
            updated_at TEXT,
            additional_data TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS kyc_documents (
            document_id TEXT PRIMARY KEY,
            user_id TEXT,
            document_type TEXT,
            document_number TEXT,
            issuing_country TEXT,
            expiry_date TEXT,
            verification_status TEXT,
            verification_date TEXT,
            document_data TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def _init_aml_db(self):
        """Initialize AML database"""
        conn = sqlite3.connect(AML_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS aml_checks (
            check_id TEXT PRIMARY KEY,
            user_id TEXT,
            wallet_address TEXT,
            aml_status TEXT,
            aml_risk_score REAL,
            check_date TEXT,
            provider TEXT,
            details TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS wallet_risk_scores (
            wallet_address TEXT PRIMARY KEY,
            risk_score REAL,
            last_updated TEXT,
            provider TEXT,
            details TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS transaction_reviews (
            review_id TEXT PRIMARY KEY,
            transaction_hash TEXT,
            user_id TEXT,
            wallet_address TEXT,
            amount REAL,
            currency TEXT,
            timestamp TEXT,
            risk_score REAL,
            status TEXT,
            review_notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def _init_audit_db(self):
        """Initialize audit trail database"""
        conn = sqlite3.connect(AUDIT_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS compliance_events (
            event_id TEXT PRIMARY KEY,
            event_type TEXT,
            user_id TEXT,
            wallet_address TEXT,
            timestamp TEXT,
            details TEXT,
            related_tx_hash TEXT,
            risk_score REAL,
            action_taken TEXT,
            reviewed_by TEXT,
            review_notes TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS regulatory_reports (
            report_id TEXT PRIMARY KEY,
            report_type TEXT,
            user_id TEXT,
            wallet_address TEXT,
            transaction_hash TEXT,
            amount REAL,
            currency TEXT,
            timestamp TEXT,
            reason TEXT,
            status TEXT,
            submission_date TEXT,
            reference_number TEXT,
            additional_data TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def _init_halal_db(self):
        """Initialize Halal compliance database"""
        conn = sqlite3.connect(HALAL_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS halal_assets (
            asset_address TEXT PRIMARY KEY,
            asset_name TEXT,
            asset_symbol TEXT,
            is_halal INTEGER,
            certification_authority TEXT,
            certification_date TEXT,
            expiry_date TEXT,
            notes TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS halal_strategies (
            strategy_id TEXT PRIMARY KEY,
            is_halal INTEGER,
            verification_date TEXT,
            verification_authority TEXT,
            details TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_user_profile(self, profile: UserProfile):
        """Save user profile to KYC database"""
        conn = sqlite3.connect(KYC_DB_PATH)
        cursor = conn.cursor()
        
        # Encrypt sensitive data
        additional_data = json.dumps(profile.additional_data)
        if additional_data:
            additional_data = self.encryption.encrypt(additional_data)
        
        cursor.execute('''
        INSERT OR REPLACE INTO users (
            user_id, wallet_address, kyc_status, kyc_level, kyc_expiry,
            kyc_provider, kyc_reference_id, country_code, region_code,
            is_restricted, created_at, updated_at, additional_data
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            profile.user_id,
            profile.wallet_address,
            profile.kyc_status,
            profile.kyc_level,
            profile.kyc_expiry.isoformat() if profile.kyc_expiry else None,
            profile.kyc_provider,
            profile.kyc_reference_id,
            profile.country_code,
            profile.region_code,
            1 if profile.is_restricted else 0,
            profile.created_at.isoformat(),
            profile.updated_at.isoformat(),
            additional_data
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Saved user profile for {profile.user_id}")
    
    def get_user_profile(self, user_id: str = None, wallet_address: str = None) -> Optional[UserProfile]:
        """Get user profile from KYC database"""
        if not user_id and not wallet_address:
            raise ValueError("Either user_id or wallet_address must be provided")
        
        conn = sqlite3.connect(KYC_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        else:
            cursor.execute("SELECT * FROM users WHERE wallet_address = ?", (wallet_address,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        # Decrypt sensitive data
        additional_data = {}
        if row['additional_data']:
            try:
                decrypted = self.encryption.decrypt(row['additional_data'])
                additional_data = json.loads(decrypted)
            except Exception as e:
                logger.error(f"Failed to decrypt additional data: {e}")
        
        return UserProfile(
            user_id=row['user_id'],
            wallet_address=row['wallet_address'],
            kyc_status=row['kyc_status'],
            kyc_level=row['kyc_level'],
            kyc_expiry=datetime.fromisoformat(row['kyc_expiry']) if row['kyc_expiry'] else None,
            kyc_provider=row['kyc_provider'],
            kyc_reference_id=row['kyc_reference_id'],
            country_code=row['country_code'],
            region_code=row['region_code'],
            is_restricted=bool(row['is_restricted']),
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at']),
            additional_data=additional_data
        )
    
    def save_aml_check(self, user_id: str, wallet_address: str, 
                      aml_status: str, risk_score: float, provider: str, details: Dict[str, Any]):
        """Save AML check result to database"""
        conn = sqlite3.connect(AML_DB_PATH)
        cursor = conn.cursor()
        
        check_id = str(uuid.uuid4())
        check_date = datetime.now().isoformat()
        
        # Encrypt details
        encrypted_details = self.encryption.encrypt(json.dumps(details))
        
        cursor.execute('''
        INSERT INTO aml_checks (
            check_id, user_id, wallet_address, aml_status, aml_risk_score,
            check_date, provider, details
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            check_id,
            user_id,
            wallet_address,
            aml_status,
            risk_score,
            check_date,
            provider,
            encrypted_details
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Saved AML check for {user_id} with status {aml_status}")
        
        # Update user profile with AML status
        profile = self.get_user_profile(user_id=user_id)
        if profile:
            profile.aml_status = aml_status
            profile.aml_risk_score = risk_score
            profile.aml_last_check = datetime.now()
            profile.updated_at = datetime.now()
            self.save_user_profile(profile)
    
    def save_wallet_risk_score(self, wallet_address: str, risk_score: float, provider: str, details: Dict[str, Any]):
        """Save wallet risk score to database"""
        conn = sqlite3.connect(AML_DB_PATH)
        cursor = conn.cursor()
        
        last_updated = datetime.now().isoformat()
        
        # Encrypt details
        encrypted_details = self.encryption.encrypt(json.dumps(details))
        
        cursor.execute('''
        INSERT OR REPLACE INTO wallet_risk_scores (
            wallet_address, risk_score, last_updated, provider, details
        ) VALUES (?, ?, ?, ?, ?)
        ''', (
            wallet_address,
            risk_score,
            last_updated,
            provider,
            encrypted_details
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Saved risk score for wallet {wallet_address}: {risk_score}")
    
    def get_wallet_risk_score(self, wallet_address: str) -> Tuple[float, Dict[str, Any]]:
        """Get wallet risk score from database"""
        conn = sqlite3.connect(AML_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM wallet_risk_scores WHERE wallet_address = ?", (wallet_address,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return 0.0, {}
        
        # Decrypt details
        details = {}
        if row['details']:
            try:
                decrypted = self.encryption.decrypt(row['details'])
                details = json.loads(decrypted)
            except Exception as e:
                logger.error(f"Failed to decrypt wallet risk details: {e}")
        
        return row['risk_score'], details
    
    def log_compliance_event(self, event: ComplianceEvent):
        """Log compliance event to audit trail"""
        conn = sqlite3.connect(AUDIT_DB_PATH)
        cursor = conn.cursor()
        
        # Encrypt details
        encrypted_details = self.encryption.encrypt(json.dumps(event.details))
        
        cursor.execute('''
        INSERT INTO compliance_events (
            event_id, event_type, user_id, wallet_address, timestamp,
            details, related_tx_hash, risk_score, action_taken,
            reviewed_by, review_notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event.event_id,
            event.event_type,
            event.user_id,
            event.wallet_address,
            event.timestamp.isoformat(),
            encrypted_details,
            event.related_tx_hash,
            event.risk_score,
            event.action_taken,
            event.reviewed_by,
            event.review_notes
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Logged compliance event: {event.event_type} for {event.user_id or event.wallet_address}")
    
    def save_regulatory_report(self, report: RegulatoryReport):
        """Save regulatory report to database"""
        conn = sqlite3.connect(AUDIT_DB_PATH)
        cursor = conn.cursor()
        
        # Encrypt additional data
        encrypted_data = self.encryption.encrypt(json.dumps(report.additional_data))
        
        cursor.execute('''
        INSERT INTO regulatory_reports (
            report_id, report_type, user_id, wallet_address, transaction_hash,
            amount, currency, timestamp, reason, status, submission_date,
            reference_number, additional_data
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            report.report_id,
            report.report_type,
            report.user_id,
            report.wallet_address,
            report.transaction_hash,
            report.amount,
            report.currency,
            report.timestamp.isoformat(),
            report.reason,
            report.status,
            report.submission_date.isoformat() if report.submission_date else None,
            report.reference_number,
            encrypted_data
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Saved regulatory report: {report.report_type} for {report.user_id or report.wallet_address}")
    
    def save_halal_asset(self, asset_address: str, asset_name: str, asset_symbol: str,
                        is_halal: bool, certification_authority: str, certification_date: datetime,
                        expiry_date: Optional[datetime] = None, notes: str = None):
        """Save Halal asset information to database"""
        conn = sqlite3.connect(HALAL_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT OR REPLACE INTO halal_assets (
            asset_address, asset_name, asset_symbol, is_halal,
            certification_authority, certification_date, expiry_date, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            asset_address,
            asset_name,
            asset_symbol,
            1 if is_halal else 0,
            certification_authority,
            certification_date.isoformat(),
            expiry_date.isoformat() if expiry_date else None,
            notes
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Saved Halal asset information for {asset_symbol} ({asset_address})")
    
    def is_asset_halal(self, asset_address: str) -> bool:
        """Check if an asset is Halal compliant"""
        conn = sqlite3.connect(HALAL_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT is_halal, expiry_date FROM halal_assets 
        WHERE asset_address = ?
        ''', (asset_address,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return False
        
        is_halal, expiry_date = row
        
        # Check if certification has expired
        if expiry_date:
            expiry = datetime.fromisoformat(expiry_date)
            if expiry < datetime.now():
                return False
        
        return bool(is_halal)
    
    def save_halal_strategy(self, strategy_id: str, is_halal: bool,
                           verification_authority: str, details: Dict[str, Any]):
        """Save Halal strategy information to database"""
        conn = sqlite3.connect(HALAL_DB_PATH)
        cursor = conn.cursor()
        
        verification_date = datetime.now().isoformat()
        encrypted_details = self.encryption.encrypt(json.dumps(details))
        
        cursor.execute('''
        INSERT OR REPLACE INTO halal_strategies (
            strategy_id, is_halal, verification_date, verification_authority, details
        ) VALUES (?, ?, ?, ?, ?)
        ''', (
            strategy_id,
            1 if is_halal else 0,
            verification_date,
            verification_authority,
            encrypted_details
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Saved Halal strategy information for {strategy_id}")
    
    def is_strategy_halal(self, strategy_id: str) -> bool:
        """Check if a strategy is Halal compliant"""
        conn = sqlite3.connect(HALAL_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT is_halal FROM halal_strategies 
        WHERE strategy_id = ?
        ''', (strategy_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return False
        
        return bool(row[0])

class KYCManager:
    """Manager for KYC verification"""
    
    def __init__(self, db_manager: DatabaseManager, provider: str = "onfido"):
        self.db_manager = db_manager
        self.provider = provider
        self.api_url = KYC_PROVIDERS.get(provider)
        
        if not self.api_url:
            raise ValueError(f"Unsupported KYC provider: {provider}")
        
        # API keys would be loaded from secure storage in production
        self.api_key = os.environ.get(f"KYC_{provider.upper()}_API_KEY", "test_api_key")
    
    def create_verification(self, user_id: str, wallet_address: str, 
                           first_name: str, last_name: str, dob: str, 
                           country_code: str, region_code: str = None) -> str:
        """Create a new KYC verification request"""
        # In a real implementation, this would call the KYC provider's API
        # For this example, we'll simulate the API call
        
        verification_id = str(uuid.uuid4())
        
        # Create user profile
        profile = UserProfile(
            user_id=user_id,
            wallet_address=wallet_address,
            kyc_status="pending",
            kyc_level=0,
            kyc_provider=self.provider,
            kyc_reference_id=verification_id,
            country_code=country_code,
            region_code=region_code,
            is_restricted=self._is_restricted_location(country_code, region_code)
        )
        
        # Add personal information to additional data
        profile.additional_data = {
            "first_name": first_name,
            "last_name": last_name,
            "dob": dob
        }
        
        # Save to database
        self.db_manager.save_user_profile(profile)
        
        # Log compliance event
        event = ComplianceEvent(
            event_id=str(uuid.uuid4()),
            event_type="kyc_request_created",
            user_id=user_id,
            wallet_address=wallet_address,
            timestamp=datetime.now(),
            details={
                "provider": self.provider,
                "verification_id": verification_id,
                "country_code": country_code,
                "region_code": region_code
            }
        )
        self.db_manager.log_compliance_event(event)
        
        logger.info(f"Created KYC verification request for {user_id}")
        return verification_id
    
    def update_verification_status(self, user_id: str, status: str, level: int = 1):
        """Update KYC verification status"""
        profile = self.db_manager.get_user_profile(user_id=user_id)
        
        if not profile:
            raise ValueError(f"User profile not found: {user_id}")
        
        profile.kyc_status = status
        profile.kyc_level = level if status == "approved" else 0
        profile.updated_at = datetime.now()
        
        if status == "approved":
            # Set expiry date (1 year from now)
            profile.kyc_expiry = datetime.now() + timedelta(days=365)
        
        # Save updated profile
        self.db_manager.save_user_profile(profile)
        
        # Log compliance event
        event = ComplianceEvent(
            event_id=str(uuid.uuid4()),
            event_type="kyc_status_updated",
            user_id=user_id,
            wallet_address=profile.wallet_address,
            timestamp=datetime.now(),
            details={
                "status": status,
                "level": level,
                "expiry": profile.kyc_expiry.isoformat() if profile.kyc_expiry else None
            }
        )
        self.db_manager.log_compliance_event(event)
        
        logger.info(f"Updated KYC status for {user_id} to {status} (level {level})")
    
    def check_verification_status(self, user_id: str) -> Dict[str, Any]:
        """Check KYC verification status"""
        profile = self.db_manager.get_user_profile(user_id=user_id)
        
        if not profile:
            raise ValueError(f"User profile not found: {user_id}")
        
        # Check if KYC has expired
        if profile.kyc_status == "approved" and profile.kyc_expiry:
            if profile.kyc_expiry < datetime.now():
                profile.kyc_status = "expired"
                profile.updated_at = datetime.now()
                self.db_manager.save_user_profile(profile)
                
                # Log compliance event
                event = ComplianceEvent(
                    event_id=str(uuid.uuid4()),
                    event_type="kyc_expired",
                    user_id=user_id,
                    wallet_address=profile.wallet_address,
                    timestamp=datetime.now(),
                    details={
                        "expiry_date": profile.kyc_expiry.isoformat()
                    }
                )
                self.db_manager.log_compliance_event(event)
        
        return {
            "status": profile.kyc_status,
            "level": profile.kyc_level,
            "expiry": profile.kyc_expiry.isoformat() if profile.kyc_expiry else None,
            "is_restricted": profile.is_restricted
        }
    
    def _is_restricted_location(self, country_code: str, region_code: str = None) -> bool:
        """Check if location is restricted"""
        if country_code in RESTRICTED_COUNTRIES:
            restricted_regions = RESTRICTED_COUNTRIES[country_code]
            
            # If no specific regions are listed, the entire country is restricted
            if not restricted_regions:
                return True
            
            # Check if the specific region is restricted
            if region_code and region_code in restricted_regions:
                return True
        
        return False

class AMLManager:
    """Manager for AML monitoring"""
    
    def __init__(self, db_manager: DatabaseManager, provider: str = "chainalysis"):
        self.db_manager = db_manager
        self.provider = provider
        self.api_url = AML_PROVIDERS.get(provider)
        
        if not self.api_url:
            raise ValueError(f"Unsupported AML provider: {provider}")
        
        # API keys would be loaded from secure storage in production
        self.api_key = os.environ.get(f"AML_{provider.upper()}_API_KEY", "test_api_key")
    
    def check_wallet(self, wallet_address: str, user_id: str = None) -> Dict[str, Any]:
        """Check wallet for AML risk"""
        # In a real implementation, this would call the AML provider's API
        # For this example, we'll simulate the API call
        
        # Generate a deterministic but random-looking risk score based on wallet address
        wallet_hash = int(hashlib.sha256(wallet_address.encode()).hexdigest(), 16)
        risk_score = (wallet_hash % 1000) / 1000.0  # 0.0 to 1.0
        
        # Determine status based on risk score
        if risk_score < 0.2:
            status = "approved"
        elif risk_score < 0.7:
            status = "flagged"
        else:
            status = "blocked"
        
        # Generate details
        details = {
            "provider": self.provider,
            "check_time": datetime.now().isoformat(),
            "risk_factors": []
        }
        
        # Add some simulated risk factors
        if risk_score > 0.3:
            details["risk_factors"].append("unusual_transaction_patterns")
        if risk_score > 0.5:
            details["risk_factors"].append("connection_to_high_risk_entities")
        if risk_score > 0.8:
            details["risk_factors"].append("potential_illicit_activity")
        
        # Save to database
        self.db_manager.save_wallet_risk_score(
            wallet_address=wallet_address,
            risk_score=risk_score,
            provider=self.provider,
            details=details
        )
        
        # If user_id is provided, update user's AML status
        if user_id:
            self.db_manager.save_aml_check(
                user_id=user_id,
                wallet_address=wallet_address,
                aml_status=status,
                risk_score=risk_score,
                provider=self.provider,
                details=details
            )
        
        # Log compliance event
        event = ComplianceEvent(
            event_id=str(uuid.uuid4()),
            event_type="aml_wallet_check",
            user_id=user_id,
            wallet_address=wallet_address,
            timestamp=datetime.now(),
            risk_score=risk_score,
            details=details,
            action_taken=status
        )
        self.db_manager.log_compliance_event(event)
        
        logger.info(f"Performed AML check for wallet {wallet_address}: {status} (score: {risk_score:.2f})")
        
        return {
            "status": status,
            "risk_score": risk_score,
            "details": details
        }
    
    def check_transaction(self, tx_hash: str, from_address: str, to_address: str, 
                         amount: float, currency: str, user_id: str = None) -> Dict[str, Any]:
        """Check transaction for AML risk"""
        # Check both addresses
        from_risk, _ = self.db_manager.get_wallet_risk_score(from_address)
        to_risk, _ = self.db_manager.get_wallet_risk_score(to_address)
        
        # Use the higher risk score
        risk_score = max(from_risk, to_risk)
        
        # Check if transaction exceeds reporting threshold
        threshold = REGULATORY_REPORTING_THRESHOLDS.get(currency.upper(), float('inf'))
        requires_reporting = amount >= threshold
        
        # Determine status
        if risk_score < 0.2:
            status = "approved"
        elif risk_score < 0.7:
            status = "flagged"
        else:
            status = "blocked"
        
        # Generate details
        details = {
            "from_address": from_address,
            "to_address": to_address,
            "amount": amount,
            "currency": currency,
            "from_risk": from_risk,
            "to_risk": to_risk,
            "requires_reporting": requires_reporting
        }
        
        # Log transaction review
        conn = sqlite3.connect(AML_DB_PATH)
        cursor = conn.cursor()
        
        review_id = str(uuid.uuid4())
        
        cursor.execute('''
        INSERT INTO transaction_reviews (
            review_id, transaction_hash, user_id, wallet_address,
            amount, currency, timestamp, risk_score, status, review_notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            review_id,
            tx_hash,
            user_id,
            from_address,
            amount,
            currency,
            datetime.now().isoformat(),
            risk_score,
            status,
            json.dumps(details)
        ))
        
        conn.commit()
        conn.close()
        
        # Log compliance event
        event = ComplianceEvent(
            event_id=str(uuid.uuid4()),
            event_type="aml_transaction_check",
            user_id=user_id,
            wallet_address=from_address,
            timestamp=datetime.now(),
            related_tx_hash=tx_hash,
            risk_score=risk_score,
            details=details,
            action_taken=status
        )
        self.db_manager.log_compliance_event(event)
        
        # Create regulatory report if needed
        if requires_reporting:
            report = RegulatoryReport(
                report_id=str(uuid.uuid4()),
                report_type="CTR",  # Currency Transaction Report
                user_id=user_id,
                wallet_address=from_address,
                transaction_hash=tx_hash,
                amount=amount,
                currency=currency,
                timestamp=datetime.now(),
                reason="Exceeds reporting threshold",
                status="pending",
                additional_data=details
            )
            self.db_manager.save_regulatory_report(report)
        
        logger.info(f"Performed AML check for transaction {tx_hash}: {status} (score: {risk_score:.2f})")
        
        return {
            "status": status,
            "risk_score": risk_score,
            "requires_reporting": requires_reporting,
            "details": details
        }

class HalalComplianceManager:
    """Manager for Halal compliance verification"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def register_halal_asset(self, asset_address: str, asset_name: str, asset_symbol: str,
                            is_halal: bool, certification_authority: str):
        """Register an asset as Halal compliant"""
        certification_date = datetime.now()
        expiry_date = certification_date + timedelta(days=365)  # 1 year validity
        
        self.db_manager.save_halal_asset(
            asset_address=asset_address,
            asset_name=asset_name,
            asset_symbol=asset_symbol,
            is_halal=is_halal,
            certification_authority=certification_authority,
            certification_date=certification_date,
            expiry_date=expiry_date
        )
        
        # Log compliance event
        event = ComplianceEvent(
            event_id=str(uuid.uuid4()),
            event_type="halal_asset_registered",
            timestamp=datetime.now(),
            details={
                "asset_address": asset_address,
                "asset_name": asset_name,
                "asset_symbol": asset_symbol,
                "is_halal": is_halal,
                "certification_authority": certification_authority
            }
        )
        self.db_manager.log_compliance_event(event)
        
        logger.info(f"Registered asset {asset_symbol} as {'Halal' if is_halal else 'non-Halal'}")
    
    def verify_strategy_halal_compliance(self, strategy_id: str, assets: List[str], 
                                        operations: List[str]) -> bool:
        """Verify if a strategy is Halal compliant"""
        # Check if all assets are Halal compliant
        for asset in assets:
            if not self.db_manager.is_asset_halal(asset):
                logger.warning(f"Strategy {strategy_id} uses non-Halal asset {asset}")
                
                # Save strategy as non-Halal
                self.db_manager.save_halal_strategy(
                    strategy_id=strategy_id,
                    is_halal=False,
                    verification_authority="Automated System",
                    details={
                        "reason": f"Uses non-Halal asset {asset}",
                        "assets": assets,
                        "operations": operations
                    }
                )
                
                return False
        
        # Check operations for compliance
        non_compliant_ops = []
        for op in operations:
            # Check for non-compliant operations like interest-based lending
            if "interest" in op.lower() or "lending" in op.lower() or "borrowing" in op.lower():
                non_compliant_ops.append(op)
        
        is_halal = len(non_compliant_ops) == 0
        
        # Save strategy compliance status
        self.db_manager.save_halal_strategy(
            strategy_id=strategy_id,
            is_halal=is_halal,
            verification_authority="Automated System",
            details={
                "assets": assets,
                "operations": operations,
                "non_compliant_operations": non_compliant_ops
            }
        )
        
        # Log compliance event
        event = ComplianceEvent(
            event_id=str(uuid.uuid4()),
            event_type="halal_strategy_verification",
            timestamp=datetime.now(),
            details={
                "strategy_id": strategy_id,
                "is_halal": is_halal,
                "assets": assets,
                "non_compliant_operations": non_compliant_ops
            }
        )
        self.db_manager.log_compliance_event(event)
        
        logger.info(f"Verified strategy {strategy_id} as {'Halal' if is_halal else 'non-Halal'}")
        return is_halal

class RegulatoryReportingManager:
    """Manager for regulatory reporting"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def create_report(self, report_type: str, user_id: str, wallet_address: str,
                     transaction_hash: str, amount: float, currency: str, reason: str,
                     additional_data: Dict[str, Any] = None) -> str:
        """Create a regulatory report"""
        report_id = str(uuid.uuid4())
        
        report = RegulatoryReport(
            report_id=report_id,
            report_type=report_type,
            user_id=user_id,
            wallet_address=wallet_address,
            transaction_hash=transaction_hash,
            amount=amount,
            currency=currency,
            timestamp=datetime.now(),
            reason=reason,
            status="pending",
            additional_data=additional_data or {}
        )
        
        self.db_manager.save_regulatory_report(report)
        
        # Log compliance event
        event = ComplianceEvent(
            event_id=str(uuid.uuid4()),
            event_type="regulatory_report_created",
            user_id=user_id,
            wallet_address=wallet_address,
            timestamp=datetime.now(),
            related_tx_hash=transaction_hash,
            details={
                "report_id": report_id,
                "report_type": report_type,
                "amount": amount,
                "currency": currency,
                "reason": reason
            }
        )
        self.db_manager.log_compliance_event(event)
        
        logger.info(f"Created {report_type} report for {user_id or wallet_address}")
        return report_id
    
    def submit_report(self, report_id: str) -> str:
        """Submit a regulatory report to authorities"""
        # In a real implementation, this would call an API to submit the report
        # For this example, we'll simulate the submission
        
        conn = sqlite3.connect(AUDIT_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM regulatory_reports WHERE report_id = ?", (report_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            raise ValueError(f"Report not found: {report_id}")
        
        # Generate a reference number
        reference_number = f"REF-{datetime.now().strftime('%Y%m%d')}-{report_id[:8]}"
        
        # Update report status
        cursor.execute('''
        UPDATE regulatory_reports
        SET status = ?, submission_date = ?, reference_number = ?
        WHERE report_id = ?
        ''', (
            "submitted",
            datetime.now().isoformat(),
            reference_number,
            report_id
        ))
        
        conn.commit()
        conn.close()
        
        # Log compliance event
        event = ComplianceEvent(
            event_id=str(uuid.uuid4()),
            event_type="regulatory_report_submitted",
            user_id=row['user_id'],
            wallet_address=row['wallet_address'],
            timestamp=datetime.now(),
            related_tx_hash=row['transaction_hash'],
            details={
                "report_id": report_id,
                "report_type": row['report_type'],
                "reference_number": reference_number
            }
        )
        self.db_manager.log_compliance_event(event)
        
        logger.info(f"Submitted report {report_id} with reference {reference_number}")
        return reference_number

class ComplianceFramework:
    """Main compliance framework integrating all compliance components"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.kyc_manager = KYCManager(self.db_manager)
        self.aml_manager = AMLManager(self.db_manager)
        self.halal_manager = HalalComplianceManager(self.db_manager)
        self.reporting_manager = RegulatoryReportingManager(self.db_manager)
    
    def onboard_user(self, wallet_address: str, first_name: str, last_name: str,
                    dob: str, country_code: str, region_code: str = None) -> Dict[str, Any]:
        """Onboard a new user with KYC"""
        # Generate user ID
        user_id = str(uuid.uuid4())
        
        # Create KYC verification
        verification_id = self.kyc_manager.create_verification(
            user_id=user_id,
            wallet_address=wallet_address,
            first_name=first_name,
            last_name=last_name,
            dob=dob,
            country_code=country_code,
            region_code=region_code
        )
        
        # Check if location is restricted
        is_restricted = self.kyc_manager._is_restricted_location(country_code, region_code)
        
        # Perform initial AML check
        aml_result = self.aml_manager.check_wallet(wallet_address, user_id)
        
        return {
            "user_id": user_id,
            "verification_id": verification_id,
            "kyc_status": "pending",
            "is_restricted": is_restricted,
            "aml_status": aml_result["status"],
            "aml_risk_score": aml_result["risk_score"]
        }
    
    def check_transaction_compliance(self, tx_hash: str, from_address: str, to_address: str,
                                   amount: float, currency: str, user_id: str = None,
                                   strategy_id: str = None) -> Dict[str, Any]:
        """Check if a transaction is compliant"""
        result = {
            "is_compliant": True,
            "reasons": [],
            "aml_check": None,
            "kyc_check": None,
            "halal_check": None
        }
        
        # Check KYC status if user_id is provided
        if user_id:
            kyc_status = self.kyc_manager.check_verification_status(user_id)
            result["kyc_check"] = kyc_status
            
            if kyc_status["status"] != "approved":
                result["is_compliant"] = False
                result["reasons"].append(f"KYC not approved: {kyc_status['status']}")
            
            if kyc_status["is_restricted"]:
                result["is_compliant"] = False
                result["reasons"].append("User is in a restricted location")
        
        # Check AML status
        aml_result = self.aml_manager.check_transaction(
            tx_hash=tx_hash,
            from_address=from_address,
            to_address=to_address,
            amount=amount,
            currency=currency,
            user_id=user_id
        )
        result["aml_check"] = aml_result
        
        if aml_result["status"] == "blocked":
            result["is_compliant"] = False
            result["reasons"].append("Transaction blocked by AML check")
        
        # Check if strategy is Halal compliant if strategy_id is provided
        if strategy_id:
            is_halal = self.db_manager.is_strategy_halal(strategy_id)
            result["halal_check"] = {"is_halal": is_halal}
            
            # Note: We don't block non-Halal transactions, just flag them
            if not is_halal:
                result["reasons"].append("Strategy is not Halal compliant")
        
        # Create regulatory report if needed
        if aml_result["requires_reporting"]:
            report_id = self.reporting_manager.create_report(
                report_type="CTR",
                user_id=user_id,
                wallet_address=from_address,
                transaction_hash=tx_hash,
                amount=amount,
                currency=currency,
                reason="Exceeds reporting threshold",
                additional_data=aml_result["details"]
            )
            result["regulatory_report"] = {"report_id": report_id, "type": "CTR"}
        
        # Log compliance check
        event = ComplianceEvent(
            event_id=str(uuid.uuid4()),
            event_type="transaction_compliance_check",
            user_id=user_id,
            wallet_address=from_address,
            timestamp=datetime.now(),
            related_tx_hash=tx_hash,
            details=result,
            action_taken="allowed" if result["is_compliant"] else "blocked"
        )
        self.db_manager.log_compliance_event(event)
        
        logger.info(f"Compliance check for tx {tx_hash}: {'PASS' if result['is_compliant'] else 'FAIL'}")
        return result
    
    def verify_strategy_compliance(self, strategy_id: str, assets: List[str],
                                 operations: List[str]) -> Dict[str, Any]:
        """Verify if a strategy is compliant with regulations"""
        # Check Halal compliance
        is_halal = self.halal_manager.verify_strategy_halal_compliance(
            strategy_id=strategy_id,
            assets=assets,
            operations=operations
        )
        
        # Check for other compliance issues
        compliance_issues = []
        
        # Example: Check for restricted assets
        for asset in assets:
            # This would check against a database of restricted assets
            # For this example, we'll just flag assets with "RESTRICTED" in the name
            if "RESTRICTED" in asset:
                compliance_issues.append(f"Asset {asset} is restricted")
        
        # Example: Check for restricted operations
        for op in operations:
            # This would check against a database of restricted operations
            # For this example, we'll just flag operations with "PROHIBITED" in the name
            if "PROHIBITED" in op:
                compliance_issues.append(f"Operation {op} is prohibited")
        
        is_compliant = len(compliance_issues) == 0
        
        result = {
            "strategy_id": strategy_id,
            "is_compliant": is_compliant,
            "is_halal": is_halal,
            "compliance_issues": compliance_issues
        }
        
        # Log compliance check
        event = ComplianceEvent(
            event_id=str(uuid.uuid4()),
            event_type="strategy_compliance_check",
            timestamp=datetime.now(),
            details={
                "strategy_id": strategy_id,
                "assets": assets,
                "operations": operations,
                "is_compliant": is_compliant,
                "is_halal": is_halal,
                "compliance_issues": compliance_issues
            }
        )
        self.db_manager.log_compliance_event(event)
        
        logger.info(f"Compliance check for strategy {strategy_id}: {'PASS' if is_compliant else 'FAIL'}")
        return result
    
    def generate_compliance_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate a compliance report for a time period"""
        conn = sqlite3.connect(AUDIT_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all compliance events in the period
        cursor.execute('''
        SELECT * FROM compliance_events 
        WHERE timestamp BETWEEN ? AND ?
        ''', (
            start_date.isoformat(),
            end_date.isoformat()
        ))
        
        events = [dict(row) for row in cursor.fetchall()]
        
        # Get all regulatory reports in the period
        cursor.execute('''
        SELECT * FROM regulatory_reports 
        WHERE timestamp BETWEEN ? AND ?
        ''', (
            start_date.isoformat(),
            end_date.isoformat()
        ))
        
        reports = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        # Analyze events
        event_types = {}
        for event in events:
            event_type = event["event_type"]
            if event_type not in event_types:
                event_types[event_type] = 0
            event_types[event_type] += 1
        
        # Analyze reports
        report_types = {}
        for report in reports:
            report_type = report["report_type"]
            if report_type not in report_types:
                report_types[report_type] = 0
            report_types[report_type] += 1
        
        # Generate summary
        summary = {
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "total_events": len(events),
            "event_types": event_types,
            "total_reports": len(reports),
            "report_types": report_types,
            "generated_at": datetime.now().isoformat()
        }
        
        logger.info(f"Generated compliance report for {start_date} to {end_date}")
        return summary

# Example usage
if __name__ == "__main__":
    # Initialize compliance framework
    compliance = ComplianceFramework()
    
    # Example: Onboard a user
    user_result = compliance.onboard_user(
        wallet_address="0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        first_name="John",
        last_name="Doe",
        dob="1980-01-01",
        country_code="US",
        region_code="CA"
    )
    
    print("User onboarding result:", user_result)
    
    # Example: Register a Halal asset
    compliance.halal_manager.register_halal_asset(
        asset_address="0x6B175474E89094C44Da98b954EedeAC495271d0F",
        asset_name="Dai Stablecoin",
        asset_symbol="DAI",
        is_halal=True,
        certification_authority="Shariyah Review Bureau"
    )
    
    # Example: Check transaction compliance
    tx_result = compliance.check_transaction_compliance(
        tx_hash="0x123456789abcdef",
        from_address="0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        to_address="0x6B175474E89094C44Da98b954EedeAC495271d0F",
        amount=5000,
        currency="USD",
        user_id=user_result["user_id"]
    )
    
    print("Transaction compliance result:", tx_result)
    
    # Example: Verify strategy compliance
    strategy_result = compliance.verify_strategy_compliance(
        strategy_id="strategy-123",
        assets=[
            "0x6B175474E89094C44Da98b954EedeAC495271d0F",  # DAI
            "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"   # WETH
        ],
        operations=[
            "swap",
            "liquidity_provision"
        ]
    )
    
    print("Strategy compliance result:", strategy_result)
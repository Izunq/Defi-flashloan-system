"""
AML/KYC Integration Module

This module implements integration with Anti-Money Laundering (AML) and
Know Your Customer (KYC) services for regulatory compliance.

Features:
- User identity verification
- Address screening against sanctions lists
- Risk scoring for users and transactions
- Ongoing monitoring
- Integration with external AML/KYC providers
"""

import json
import time
import hashlib
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Union, Callable, Set
from enum import Enum
from dataclasses import dataclass
import uuid
import random
import datetime
import re
import os
import base64
import hmac
import requests
from urllib.parse import urlencode

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("aml_kyc_integration")

class VerificationStatus(Enum):
    """Status of identity verification"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    REQUIRES_ADDITIONAL_INFO = "requires_additional_info"


class VerificationLevel(Enum):
    """Verification levels for KYC"""
    BASIC = "basic"         # Email + basic info
    STANDARD = "standard"   # ID document verification
    ENHANCED = "enhanced"   # ID + proof of address + face match
    BUSINESS = "business"   # Business verification


class RiskLevel(Enum):
    """Risk levels for users and transactions"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    PROHIBITED = "prohibited"


class ScreeningResult(Enum):
    """Results of sanctions and PEP screening"""
    NO_MATCH = "no_match"
    POSSIBLE_MATCH = "possible_match"
    MATCH = "match"
    ERROR = "error"


class KYCProvider(Enum):
    """Supported KYC providers"""
    ONFIDO = "onfido"
    JUMIO = "jumio"
    SUMSUB = "sumsub"
    VERIFF = "veriff"
    SARDINE = "sardine"
    TRULIOO = "trulioo"
    INTERNAL = "internal"


class AMLProvider(Enum):
    """Supported AML providers"""
    CHAINALYSIS = "chainalysis"
    ELLIPTIC = "elliptic"
    COINFIRM = "coinfirm"
    MERKLE_SCIENCE = "merkle_science"
    SCORECHAIN = "scorechain"
    TRM_LABS = "trm_labs"
    INTERNAL = "internal"


@dataclass
class UserIdentity:
    """User identity information"""
    user_id: str
    email: str
    first_name: str
    last_name: str
    date_of_birth: Optional[str]
    nationality: Optional[str]
    country_of_residence: Optional[str]
    address: Optional[Dict[str, str]]
    phone_number: Optional[str]
    id_documents: List[Dict[str, Any]]
    verification_status: VerificationStatus
    verification_level: VerificationLevel
    risk_level: RiskLevel
    created_at: int
    updated_at: int
    metadata: Dict[str, Any]


@dataclass
class VerificationAttempt:
    """Verification attempt information"""
    attempt_id: str
    user_id: str
    provider: KYCProvider
    verification_type: str
    status: VerificationStatus
    provider_reference: Optional[str]
    submitted_at: int
    updated_at: int
    expires_at: Optional[int]
    result: Optional[Dict[str, Any]]
    documents_submitted: List[Dict[str, Any]]
    notes: Optional[str]


@dataclass
class ScreeningResult:
    """Screening result information"""
    screening_id: str
    user_id: Optional[str]
    address: Optional[str]
    provider: AMLProvider
    screening_type: str
    result: ScreeningResult
    risk_score: float
    matches: List[Dict[str, Any]]
    timestamp: int
    raw_response: Dict[str, Any]


@dataclass
class OngoingMonitoring:
    """Ongoing monitoring configuration"""
    monitoring_id: str
    user_id: str
    address: Optional[str]
    provider: AMLProvider
    monitoring_type: str
    status: str
    provider_reference: Optional[str]
    created_at: int
    updated_at: int
    last_checked_at: Optional[int]
    alert_threshold: float
    notification_emails: List[str]


class AMLKYCIntegration:
    """
    AML/KYC Integration system.
    
    This class provides integration with Anti-Money Laundering (AML) and
    Know Your Customer (KYC) services for regulatory compliance.
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the AML/KYC Integration system.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config = self._load_config(config_path)
        self.users: Dict[str, UserIdentity] = {}
        self.verification_attempts: Dict[str, VerificationAttempt] = {}
        self.screening_results: Dict[str, ScreeningResult] = {}
        self.ongoing_monitoring: Dict[str, OngoingMonitoring] = {}
        
        self.kyc_providers: Dict[KYCProvider, Dict[str, Any]] = {}
        self.aml_providers: Dict[AMLProvider, Dict[str, Any]] = {}
        
        self.callbacks: Dict[str, List[Callable]] = {
            "user_created": [],
            "verification_updated": [],
            "screening_completed": [],
            "risk_level_changed": [],
            "monitoring_alert": []
        }
        
        # Initialize configurations
        self._initialize_configs()
        
        # Start background tasks
        self.running = True
        self.background_tasks = [
            asyncio.create_task(self._check_verification_status()),
            asyncio.create_task(self._run_ongoing_monitoring()),
            asyncio.create_task(self._refresh_expired_verifications())
        ]
        
        logger.info(f"AML/KYC Integration initialized with {len(self.kyc_providers)} KYC providers and {len(self.aml_providers)} AML providers")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load configuration from file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Configuration dictionary
        """
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            # Use default configuration as fallback
            return {
                "kyc_providers": [],
                "aml_providers": [],
                "global_settings": {
                    "verification_check_interval_seconds": 300,
                    "monitoring_interval_seconds": 3600,
                    "expired_verification_check_interval_seconds": 86400,
                    "verification_expiry_days": 90,
                    "default_verification_level": "STANDARD",
                    "default_risk_level": "MEDIUM",
                    "notification_enabled": True,
                    "default_notification_emails": []
                }
            }
    
    def _initialize_configs(self):
        """Initialize configurations from the loaded config"""
        # Initialize KYC providers
        for provider_config in self.config.get("kyc_providers", []):
            try:
                provider_name = provider_config["name"]
                provider = KYCProvider(provider_name)
                
                self.kyc_providers[provider] = provider_config
                logger.info(f"Initialized KYC provider: {provider.value}")
            except Exception as e:
                logger.error(f"Failed to initialize KYC provider: {e}")
        
        # Initialize AML providers
        for provider_config in self.config.get("aml_providers", []):
            try:
                provider_name = provider_config["name"]
                provider = AMLProvider(provider_name)
                
                self.aml_providers[provider] = provider_config
                logger.info(f"Initialized AML provider: {provider.value}")
            except Exception as e:
                logger.error(f"Failed to initialize AML provider: {e}")
    
    async def create_user(self, user_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new user for KYC verification.
        
        Args:
            user_data: User data
            
        Returns:
            User ID if successful, None otherwise
        """
        try:
            # Generate user ID
            user_id = str(uuid.uuid4())
            
            # Extract required fields
            email = user_data.get("email")
            first_name = user_data.get("first_name")
            last_name = user_data.get("last_name")
            
            if not email or not first_name or not last_name:
                logger.error("Missing required user fields: email, first_name, last_name")
                return None
            
            # Create user identity
            current_time = int(time.time())
            user = UserIdentity(
                user_id=user_id,
                email=email,
                first_name=first_name,
                last_name=last_name,
                date_of_birth=user_data.get("date_of_birth"),
                nationality=user_data.get("nationality"),
                country_of_residence=user_data.get("country_of_residence"),
                address=user_data.get("address"),
                phone_number=user_data.get("phone_number"),
                id_documents=[],
                verification_status=VerificationStatus.PENDING,
                verification_level=VerificationLevel(self.config["global_settings"]["default_verification_level"].lower()),
                risk_level=RiskLevel(self.config["global_settings"]["default_risk_level"].lower()),
                created_at=current_time,
                updated_at=current_time,
                metadata=user_data.get("metadata", {})
            )
            
            # Store user
            self.users[user_id] = user
            
            # Trigger callback
            self._trigger_callbacks("user_created", user)
            
            logger.info(f"Created user {user_id} ({email})")
            
            return user_id
        
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    async def start_verification(self, user_id: str, verification_type: str, provider_name: Optional[str] = None) -> Optional[str]:
        """
        Start a verification process for a user.
        
        Args:
            user_id: User ID
            verification_type: Type of verification
            provider_name: Optional provider name (if not specified, default provider will be used)
            
        Returns:
            Verification attempt ID if successful, None otherwise
        """
        if user_id not in self.users:
            logger.error(f"User {user_id} not found")
            return None
        
        user = self.users[user_id]
        
        # Determine provider
        if provider_name:
            try:
                provider = KYCProvider(provider_name)
            except ValueError:
                logger.error(f"Invalid KYC provider: {provider_name}")
                return None
        else:
            # Use first available provider
            if not self.kyc_providers:
                logger.error("No KYC providers configured")
                return None
            provider = next(iter(self.kyc_providers.keys()))
        
        # Check if provider is configured
        if provider not in self.kyc_providers:
            logger.error(f"KYC provider {provider.value} not configured")
            return None
        
        try:
            # Create verification attempt
            attempt_id = str(uuid.uuid4())
            current_time = int(time.time())
            
            # Calculate expiration time
            expiry_days = self.config["global_settings"]["verification_expiry_days"]
            expires_at = current_time + (expiry_days * 86400)
            
            attempt = VerificationAttempt(
                attempt_id=attempt_id,
                user_id=user_id,
                provider=provider,
                verification_type=verification_type,
                status=VerificationStatus.PENDING,
                provider_reference=None,
                submitted_at=current_time,
                updated_at=current_time,
                expires_at=expires_at,
                result=None,
                documents_submitted=[],
                notes=None
            )
            
            # Store attempt
            self.verification_attempts[attempt_id] = attempt
            
            # Update user status
            user.verification_status = VerificationStatus.IN_PROGRESS
            user.updated_at = current_time
            
            # Initiate verification with provider
            provider_reference = await self._initiate_provider_verification(attempt, user)
            
            if provider_reference:
                attempt.provider_reference = provider_reference
                attempt.status = VerificationStatus.IN_PROGRESS
                attempt.updated_at = current_time
                
                # Trigger callback
                self._trigger_callbacks("verification_updated", attempt)
                
                logger.info(
                    f"Started verification {attempt_id} for user {user_id} "
                    f"with provider {provider.value} (Reference: {provider_reference})"
                )
                
                return attempt_id
            else:
                # Failed to initiate with provider
                attempt.status = VerificationStatus.REJECTED
                attempt.notes = "Failed to initiate verification with provider"
                
                # Trigger callback
                self._trigger_callbacks("verification_updated", attempt)
                
                logger.error(f"Failed to initiate verification with provider {provider.value}")
                return None
        
        except Exception as e:
            logger.error(f"Error starting verification for user {user_id}: {e}")
            return None
    
    async def _initiate_provider_verification(self, attempt: VerificationAttempt, user: UserIdentity) -> Optional[str]:
        """
        Initiate verification with the provider.
        
        Args:
            attempt: Verification attempt
            user: User identity
            
        Returns:
            Provider reference if successful, None otherwise
        """
        # In a real implementation, this would make API calls to the KYC provider
        # For demonstration, we'll simulate provider integration
        
        provider = attempt.provider
        provider_config = self.kyc_providers.get(provider, {})
        
        # Simulate API call delay
        await asyncio.sleep(random.uniform(0.5, 2.0))
        
        if provider == KYCProvider.ONFIDO:
            # Simulate Onfido API call
            return f"onfido-{hashlib.sha256(f'{attempt.attempt_id}'.encode()).hexdigest()[:12]}"
        
        elif provider == KYCProvider.JUMIO:
            # Simulate Jumio API call
            return f"jumio-{hashlib.sha256(f'{attempt.attempt_id}'.encode()).hexdigest()[:12]}"
        
        elif provider == KYCProvider.SUMSUB:
            # Simulate SumSub API call
            return f"sumsub-{hashlib.sha256(f'{attempt.attempt_id}'.encode()).hexdigest()[:12]}"
        
        elif provider == KYCProvider.VERIFF:
            # Simulate Veriff API call
            return f"veriff-{hashlib.sha256(f'{attempt.attempt_id}'.encode()).hexdigest()[:12]}"
        
        elif provider == KYCProvider.INTERNAL:
            # Simulate internal verification
            return f"internal-{hashlib.sha256(f'{attempt.attempt_id}'.encode()).hexdigest()[:12]}"
        
        else:
            logger.error(f"Unsupported KYC provider: {provider.value}")
            return None
    
    async def submit_document(self, attempt_id: str, document_type: str, document_data: Dict[str, Any]) -> bool:
        """
        Submit a document for verification.
        
        Args:
            attempt_id: Verification attempt ID
            document_type: Type of document
            document_data: Document data
            
        Returns:
            True if successful, False otherwise
        """
        if attempt_id not in self.verification_attempts:
            logger.error(f"Verification attempt {attempt_id} not found")
            return False
        
        attempt = self.verification_attempts[attempt_id]
        
        # Check if attempt is in a valid state
        if attempt.status not in [VerificationStatus.PENDING, VerificationStatus.IN_PROGRESS, VerificationStatus.REQUIRES_ADDITIONAL_INFO]:
            logger.error(f"Verification attempt {attempt_id} is not in a valid state for document submission (current status: {attempt.status.value})")
            return False
        
        try:
            # Create document record
            document = {
                "document_id": str(uuid.uuid4()),
                "document_type": document_type,
                "submitted_at": int(time.time()),
                "metadata": document_data.get("metadata", {})
            }
            
            # In a real implementation, this would upload the document to the KYC provider
            # For demonstration, we'll simulate document submission
            
            # Simulate API call delay
            await asyncio.sleep(random.uniform(0.5, 2.0))
            
            # Add document to attempt
            attempt.documents_submitted.append(document)
            attempt.updated_at = int(time.time())
            
            # If this is the first document, update status
            if len(attempt.documents_submitted) == 1:
                attempt.status = VerificationStatus.IN_PROGRESS
            
            # Add document to user's ID documents
            user_id = attempt.user_id
            if user_id in self.users:
                user = self.users[user_id]
                user.id_documents.append(document)
                user.updated_at = int(time.time())
            
            # Trigger callback
            self._trigger_callbacks("verification_updated", attempt)
            
            logger.info(
                f"Submitted {document_type} document for verification attempt {attempt_id}"
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Error submitting document for verification attempt {attempt_id}: {e}")
            return False
    
    async def check_verification_status(self, attempt_id: str) -> Dict[str, Any]:
        """
        Check the status of a verification attempt.
        
        Args:
            attempt_id: Verification attempt ID
            
        Returns:
            Verification status information
        """
        if attempt_id not in self.verification_attempts:
            logger.error(f"Verification attempt {attempt_id} not found")
            return {"status": "not_found"}
        
        attempt = self.verification_attempts[attempt_id]
        
        # In a real implementation, this would check the status with the KYC provider
        # For demonstration, we'll simulate status checking
        
        # If the attempt is already completed, just return the current status
        if attempt.status in [VerificationStatus.APPROVED, VerificationStatus.REJECTED, VerificationStatus.EXPIRED]:
            return {
                "attempt_id": attempt.attempt_id,
                "user_id": attempt.user_id,
                "provider": attempt.provider.value,
                "status": attempt.status.value,
                "updated_at": attempt.updated_at,
                "result": attempt.result
            }
        
        # Simulate checking with provider
        await self._check_provider_verification_status(attempt)
        
        return {
            "attempt_id": attempt.attempt_id,
            "user_id": attempt.user_id,
            "provider": attempt.provider.value,
            "status": attempt.status.value,
            "updated_at": attempt.updated_at,
            "result": attempt.result
        }
    
    async def _check_provider_verification_status(self, attempt: VerificationAttempt) -> None:
        """
        Check verification status with the provider.
        
        Args:
            attempt: Verification attempt
        """
        # In a real implementation, this would make API calls to the KYC provider
        # For demonstration, we'll simulate provider integration
        
        # Skip if no provider reference
        if not attempt.provider_reference:
            return
        
        # Simulate API call delay
        await asyncio.sleep(random.uniform(0.5, 1.0))
        
        # Simulate random status update
        current_time = int(time.time())
        
        # 70% chance of completion if the attempt has been in progress for a while
        if (attempt.status == VerificationStatus.IN_PROGRESS and 
            current_time - attempt.updated_at > 60 and  # At least 60 seconds old
            random.random() < 0.7):
            
            # 80% chance of approval
            if random.random() < 0.8:
                new_status = VerificationStatus.APPROVED
                result = {
                    "verification_id": attempt.provider_reference,
                    "status": "approved",
                    "completed_at": current_time,
                    "verification_score": random.uniform(0.8, 1.0),
                    "document_checks": {
                        "authenticity": "passed",
                        "face_match": "passed",
                        "data_consistency": "passed"
                    },
                    "provider_notes": "All checks passed successfully."
                }
            else:
                new_status = VerificationStatus.REJECTED
                result = {
                    "verification_id": attempt.provider_reference,
                    "status": "rejected",
                    "completed_at": current_time,
                    "verification_score": random.uniform(0.1, 0.5),
                    "document_checks": {
                        "authenticity": random.choice(["failed", "passed"]),
                        "face_match": random.choice(["failed", "passed"]),
                        "data_consistency": random.choice(["failed", "passed"])
                    },
                    "provider_notes": "One or more checks failed."
                }
            
            # Update attempt
            attempt.status = new_status
            attempt.updated_at = current_time
            attempt.result = result
            
            # Update user status
            user_id = attempt.user_id
            if user_id in self.users:
                user = self.users[user_id]
                user.verification_status = new_status
                
                # Update verification level if approved
                if new_status == VerificationStatus.APPROVED:
                    if attempt.verification_type == "enhanced":
                        user.verification_level = VerificationLevel.ENHANCED
                    elif attempt.verification_type == "business":
                        user.verification_level = VerificationLevel.BUSINESS
                    else:
                        user.verification_level = VerificationLevel.STANDARD
                
                user.updated_at = current_time
            
            # Trigger callback
            self._trigger_callbacks("verification_updated", attempt)
            
            logger.info(
                f"Verification attempt {attempt.attempt_id} completed with status {new_status.value}"
            )
        
        # 10% chance of requiring additional info
        elif (attempt.status == VerificationStatus.IN_PROGRESS and 
              random.random() < 0.1):
            
            new_status = VerificationStatus.REQUIRES_ADDITIONAL_INFO
            result = {
                "verification_id": attempt.provider_reference,
                "status": "requires_additional_info",
                "updated_at": current_time,
                "required_documents": ["utility_bill", "bank_statement"],
                "provider_notes": "Additional documents required for verification."
            }
            
            # Update attempt
            attempt.status = new_status
            attempt.updated_at = current_time
            attempt.result = result
            
            # Update user status
            user_id = attempt.user_id
            if user_id in self.users:
                user = self.users[user_id]
                user.verification_status = new_status
                user.updated_at = current_time
            
            # Trigger callback
            self._trigger_callbacks("verification_updated", attempt)
            
            logger.info(
                f"Verification attempt {attempt.attempt_id} requires additional information"
            )
    
    async def _check_verification_status(self):
        """Background task to check verification status"""
        interval = self.config["global_settings"]["verification_check_interval_seconds"]
        while self.running:
            try:
                # Find verification attempts that need checking
                for attempt_id, attempt in self.verification_attempts.items():
                    # Only check attempts that are in progress
                    if attempt.status == VerificationStatus.IN_PROGRESS:
                        await self._check_provider_verification_status(attempt)
            
            except Exception as e:
                logger.error(f"Error checking verification status: {e}")
            
            await asyncio.sleep(interval)
    
    async def _refresh_expired_verifications(self):
        """Background task to refresh expired verifications"""
        interval = self.config["global_settings"]["expired_verification_check_interval_seconds"]
        while self.running:
            try:
                current_time = int(time.time())
                
                # Find expired verification attempts
                for attempt_id, attempt in self.verification_attempts.items():
                    if (attempt.expires_at and 
                        current_time > attempt.expires_at and 
                        attempt.status not in [VerificationStatus.EXPIRED, VerificationStatus.REJECTED]):
                        
                        # Mark as expired
                        attempt.status = VerificationStatus.EXPIRED
                        attempt.updated_at = current_time
                        attempt.notes = "Verification expired"
                        
                        # Update user status if this was their active verification
                        user_id = attempt.user_id
                        if user_id in self.users:
                            user = self.users[user_id]
                            
                            # Only update user status if it matches this attempt's status
                            if user.verification_status in [VerificationStatus.PENDING, VerificationStatus.IN_PROGRESS, VerificationStatus.REQUIRES_ADDITIONAL_INFO]:
                                user.verification_status = VerificationStatus.EXPIRED
                                user.updated_at = current_time
                        
                        # Trigger callback
                        self._trigger_callbacks("verification_updated", attempt)
                        
                        logger.info(f"Marked verification attempt {attempt_id} as expired")
            
            except Exception as e:
                logger.error(f"Error refreshing expired verifications: {e}")
            
            await asyncio.sleep(interval)
    
    async def screen_address(self, address: str, screening_type: str, provider_name: Optional[str] = None) -> Optional[str]:
        """
        Screen an address against sanctions lists.
        
        Args:
            address: Blockchain address to screen
            screening_type: Type of screening
            provider_name: Optional provider name (if not specified, default provider will be used)
            
        Returns:
            Screening ID if successful, None otherwise
        """
        # Determine provider
        if provider_name:
            try:
                provider = AMLProvider(provider_name)
            except ValueError:
                logger.error(f"Invalid AML provider: {provider_name}")
                return None
        else:
            # Use first available provider
            if not self.aml_providers:
                logger.error("No AML providers configured")
                return None
            provider = next(iter(self.aml_providers.keys()))
        
        # Check if provider is configured
        if provider not in self.aml_providers:
            logger.error(f"AML provider {provider.value} not configured")
            return None
        
        try:
            # Create screening ID
            screening_id = str(uuid.uuid4())
            
            # Perform screening with provider
            result = await self._perform_provider_screening(address, screening_type, provider)
            
            if result:
                # Store screening result
                screening = ScreeningResult(
                    screening_id=screening_id,
                    user_id=None,
                    address=address,
                    provider=provider,
                    screening_type=screening_type,
                    result=result["result"],
                    risk_score=result["risk_score"],
                    matches=result["matches"],
                    timestamp=int(time.time()),
                    raw_response=result["raw_response"]
                )
                
                self.screening_results[screening_id] = screening
                
                # Trigger callback
                self._trigger_callbacks("screening_completed", screening)
                
                logger.info(
                    f"Completed {screening_type} screening for address {address} "
                    f"with provider {provider.value} (Result: {result['result'].value})"
                )
                
                return screening_id
            else:
                logger.error(f"Failed to perform screening with provider {provider.value}")
                return None
        
        except Exception as e:
            logger.error(f"Error screening address {address}: {e}")
            return None
    
    async def screen_user(self, user_id: str, screening_type: str, provider_name: Optional[str] = None) -> Optional[str]:
        """
        Screen a user against sanctions lists.
        
        Args:
            user_id: User ID
            screening_type: Type of screening
            provider_name: Optional provider name (if not specified, default provider will be used)
            
        Returns:
            Screening ID if successful, None otherwise
        """
        if user_id not in self.users:
            logger.error(f"User {user_id} not found")
            return None
        
        user = self.users[user_id]
        
        # Determine provider
        if provider_name:
            try:
                provider = AMLProvider(provider_name)
            except ValueError:
                logger.error(f"Invalid AML provider: {provider_name}")
                return None
        else:
            # Use first available provider
            if not self.aml_providers:
                logger.error("No AML providers configured")
                return None
            provider = next(iter(self.aml_providers.keys()))
        
        # Check if provider is configured
        if provider not in self.aml_providers:
            logger.error(f"AML provider {provider.value} not configured")
            return None
        
        try:
            # Create screening ID
            screening_id = str(uuid.uuid4())
            
            # Perform screening with provider
            result = await self._perform_provider_user_screening(user, screening_type, provider)
            
            if result:
                # Store screening result
                screening = ScreeningResult(
                    screening_id=screening_id,
                    user_id=user_id,
                    address=None,
                    provider=provider,
                    screening_type=screening_type,
                    result=result["result"],
                    risk_score=result["risk_score"],
                    matches=result["matches"],
                    timestamp=int(time.time()),
                    raw_response=result["raw_response"]
                )
                
                self.screening_results[screening_id] = screening
                
                # Update user risk level if necessary
                if result["result"] == ScreeningResult.MATCH:
                    user.risk_level = RiskLevel.PROHIBITED
                    user.updated_at = int(time.time())
                    
                    # Trigger risk level changed callback
                    self._trigger_callbacks("risk_level_changed", {
                        "user_id": user_id,
                        "old_risk_level": user.risk_level.value,
                        "new_risk_level": RiskLevel.PROHIBITED.value,
                        "reason": f"Sanctions match found in {screening_type} screening"
                    })
                
                # Trigger screening completed callback
                self._trigger_callbacks("screening_completed", screening)
                
                logger.info(
                    f"Completed {screening_type} screening for user {user_id} "
                    f"with provider {provider.value} (Result: {result['result'].value})"
                )
                
                return screening_id
            else:
                logger.error(f"Failed to perform screening with provider {provider.value}")
                return None
        
        except Exception as e:
            logger.error(f"Error screening user {user_id}: {e}")
            return None
    
    async def _perform_provider_screening(self, address: str, screening_type: str, provider: AMLProvider) -> Optional[Dict[str, Any]]:
        """
        Perform address screening with the provider.
        
        Args:
            address: Address to screen
            screening_type: Type of screening
            provider: AML provider
            
        Returns:
            Screening result if successful, None otherwise
        """
        # In a real implementation, this would make API calls to the AML provider
        # For demonstration, we'll simulate provider integration
        
        provider_config = self.aml_providers.get(provider, {})
        
        # Simulate API call delay
        await asyncio.sleep(random.uniform(0.5, 2.0))
        
        # Generate a random result
        random_value = random.random()
        
        if random_value < 0.8:  # 80% chance of no match
            result = ScreeningResult.NO_MATCH
            risk_score = random.uniform(0, 0.3)
            matches = []
        elif random_value < 0.95:  # 15% chance of possible match
            result = ScreeningResult.POSSIBLE_MATCH
            risk_score = random.uniform(0.3, 0.7)
            matches = [
                {
                    "entity_id": f"entity-{hashlib.sha256(str(random.random()).encode()).hexdigest()[:8]}",
                    "name": f"Similar Entity {random.randint(1, 100)}",
                    "match_score": random.uniform(0.6, 0.9),
                    "category": random.choice(["sanctions", "pep", "adverse_media"]),
                    "country": random.choice(["US", "UK", "EU", "RU", "CN"])
                }
            ]
        else:  # 5% chance of match
            result = ScreeningResult.MATCH
            risk_score = random.uniform(0.7, 1.0)
            matches = [
                {
                    "entity_id": f"entity-{hashlib.sha256(str(random.random()).encode()).hexdigest()[:8]}",
                    "name": f"Sanctioned Entity {random.randint(1, 100)}",
                    "match_score": random.uniform(0.9, 1.0),
                    "category": "sanctions",
                    "country": random.choice(["KP", "IR", "SY", "CU"])
                }
            ]
        
        # Create raw response
        raw_response = {
            "provider": provider.value,
            "query": {
                "address": address,
                "screening_type": screening_type
            },
            "timestamp": int(time.time()),
            "result": result.value,
            "risk_score": risk_score,
            "matches": matches
        }
        
        return {
            "result": result,
            "risk_score": risk_score,
            "matches": matches,
            "raw_response": raw_response
        }
    
    async def _perform_provider_user_screening(self, user: UserIdentity, screening_type: str, provider: AMLProvider) -> Optional[Dict[str, Any]]:
        """
        Perform user screening with the provider.
        
        Args:
            user: User to screen
            screening_type: Type of screening
            provider: AML provider
            
        Returns:
            Screening result if successful, None otherwise
        """
        # In a real implementation, this would make API calls to the AML provider
        # For demonstration, we'll simulate provider integration
        
        provider_config = self.aml_providers.get(provider, {})
        
        # Simulate API call delay
        await asyncio.sleep(random.uniform(0.5, 2.0))
        
        # Generate a random result
        random_value = random.random()
        
        if random_value < 0.85:  # 85% chance of no match
            result = ScreeningResult.NO_MATCH
            risk_score = random.uniform(0, 0.3)
            matches = []
        elif random_value < 0.97:  # 12% chance of possible match
            result = ScreeningResult.POSSIBLE_MATCH
            risk_score = random.uniform(0.3, 0.7)
            matches = [
                {
                    "entity_id": f"entity-{hashlib.sha256(str(random.random()).encode()).hexdigest()[:8]}",
                    "name": f"{user.first_name} {user.last_name[0]}",
                    "match_score": random.uniform(0.6, 0.9),
                    "category": random.choice(["pep", "adverse_media", "watchlist"]),
                    "country": user.nationality or random.choice(["US", "UK", "EU", "RU", "CN"])
                }
            ]
        else:  # 3% chance of match
            result = ScreeningResult.MATCH
            risk_score = random.uniform(0.7, 1.0)
            matches = [
                {
                    "entity_id": f"entity-{hashlib.sha256(str(random.random()).encode()).hexdigest()[:8]}",
                    "name": f"{user.first_name} {user.last_name}",
                    "match_score": random.uniform(0.9, 1.0),
                    "category": "sanctions",
                    "country": user.nationality or random.choice(["KP", "IR", "SY", "CU"])
                }
            ]
        
        # Create raw response
        raw_response = {
            "provider": provider.value,
            "query": {
                "user_id": user.user_id,
                "name": f"{user.first_name} {user.last_name}",
                "screening_type": screening_type
            },
            "timestamp": int(time.time()),
            "result": result.value,
            "risk_score": risk_score,
            "matches": matches
        }
        
        return {
            "result": result,
            "risk_score": risk_score,
            "matches": matches,
            "raw_response": raw_response
        }
    
    async def setup_ongoing_monitoring(self, user_id: Optional[str] = None, address: Optional[str] = None, 
                                      monitoring_type: str = "sanctions", provider_name: Optional[str] = None) -> Optional[str]:
        """
        Set up ongoing monitoring for a user or address.
        
        Args:
            user_id: Optional user ID
            address: Optional blockchain address
            monitoring_type: Type of monitoring
            provider_name: Optional provider name (if not specified, default provider will be used)
            
        Returns:
            Monitoring ID if successful, None otherwise
        """
        if not user_id and not address:
            logger.error("Either user_id or address must be provided")
            return None
        
        if user_id and user_id not in self.users:
            logger.error(f"User {user_id} not found")
            return None
        
        # Determine provider
        if provider_name:
            try:
                provider = AMLProvider(provider_name)
            except ValueError:
                logger.error(f"Invalid AML provider: {provider_name}")
                return None
        else:
            # Use first available provider
            if not self.aml_providers:
                logger.error("No AML providers configured")
                return None
            provider = next(iter(self.aml_providers.keys()))
        
        # Check if provider is configured
        if provider not in self.aml_providers:
            logger.error(f"AML provider {provider.value} not configured")
            return None
        
        try:
            # Create monitoring ID
            monitoring_id = str(uuid.uuid4())
            current_time = int(time.time())
            
            # Set up monitoring with provider
            provider_reference = await self._setup_provider_monitoring(user_id, address, monitoring_type, provider)
            
            if provider_reference:
                # Create monitoring configuration
                monitoring = OngoingMonitoring(
                    monitoring_id=monitoring_id,
                    user_id=user_id,
                    address=address,
                    provider=provider,
                    monitoring_type=monitoring_type,
                    status="active",
                    provider_reference=provider_reference,
                    created_at=current_time,
                    updated_at=current_time,
                    last_checked_at=current_time,
                    alert_threshold=0.7,
                    notification_emails=self.config["global_settings"].get("default_notification_emails", [])
                )
                
                # Store monitoring configuration
                self.ongoing_monitoring[monitoring_id] = monitoring
                
                logger.info(
                    f"Set up ongoing {monitoring_type} monitoring for "
                    f"{'user ' + user_id if user_id else 'address ' + address} "
                    f"with provider {provider.value} (Reference: {provider_reference})"
                )
                
                return monitoring_id
            else:
                logger.error(f"Failed to set up monitoring with provider {provider.value}")
                return None
        
        except Exception as e:
            logger.error(f"Error setting up monitoring: {e}")
            return None
    
    async def _setup_provider_monitoring(self, user_id: Optional[str], address: Optional[str], 
                                        monitoring_type: str, provider: AMLProvider) -> Optional[str]:
        """
        Set up monitoring with the provider.
        
        Args:
            user_id: Optional user ID
            address: Optional blockchain address
            monitoring_type: Type of monitoring
            provider: AML provider
            
        Returns:
            Provider reference if successful, None otherwise
        """
        # In a real implementation, this would make API calls to the AML provider
        # For demonstration, we'll simulate provider integration
        
        provider_config = self.aml_providers.get(provider, {})
        
        # Simulate API call delay
        await asyncio.sleep(random.uniform(0.5, 2.0))
        
        # Generate a provider reference
        if user_id:
            return f"{provider.value}-user-{hashlib.sha256(f'{user_id}'.encode()).hexdigest()[:12]}"
        else:
            return f"{provider.value}-addr-{hashlib.sha256(f'{address}'.encode()).hexdigest()[:12]}"
    
    async def _run_ongoing_monitoring(self):
        """Background task to run ongoing monitoring"""
        interval = self.config["global_settings"]["monitoring_interval_seconds"]
        while self.running:
            try:
                current_time = int(time.time())
                
                # Check each active monitoring configuration
                for monitoring_id, monitoring in self.ongoing_monitoring.items():
                    # Skip inactive monitoring
                    if monitoring.status != "active":
                        continue
                    
                    # Check if it's time to run monitoring
                    if not monitoring.last_checked_at or current_time - monitoring.last_checked_at >= interval:
                        # Run monitoring check
                        alerts = await self._check_monitoring(monitoring)
                        
                        # Update last checked time
                        monitoring.last_checked_at = current_time
                        monitoring.updated_at = current_time
                        
                        # Process alerts
                        if alerts:
                            for alert in alerts:
                                # Trigger alert callback
                                self._trigger_callbacks("monitoring_alert", {
                                    "monitoring_id": monitoring_id,
                                    "user_id": monitoring.user_id,
                                    "address": monitoring.address,
                                    "alert": alert
                                })
                                
                                logger.warning(
                                    f"Monitoring alert for {'user ' + monitoring.user_id if monitoring.user_id else 'address ' + monitoring.address}: "
                                    f"{alert['alert_type']} (Score: {alert['risk_score']})"
                                )
                                
                                # Update user risk level if applicable
                                if monitoring.user_id and alert["risk_score"] >= monitoring.alert_threshold:
                                    user_id = monitoring.user_id
                                    if user_id in self.users:
                                        user = self.users[user_id]
                                        old_risk_level = user.risk_level
                                        
                                        # Determine new risk level based on alert
                                        if alert["risk_score"] >= 0.9:
                                            new_risk_level = RiskLevel.PROHIBITED
                                        elif alert["risk_score"] >= 0.7:
                                            new_risk_level = RiskLevel.HIGH
                                        elif alert["risk_score"] >= 0.4:
                                            new_risk_level = RiskLevel.MEDIUM
                                        else:
                                            new_risk_level = RiskLevel.LOW
                                        
                                        # Only update if new risk level is higher
                                        risk_levels = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.PROHIBITED]
                                        if risk_levels.index(new_risk_level) > risk_levels.index(old_risk_level):
                                            user.risk_level = new_risk_level
                                            user.updated_at = current_time
                                            
                                            # Trigger risk level changed callback
                                            self._trigger_callbacks("risk_level_changed", {
                                                "user_id": user_id,
                                                "old_risk_level": old_risk_level.value,
                                                "new_risk_level": new_risk_level.value,
                                                "reason": f"Monitoring alert: {alert['alert_type']}"
                                            })
            
            except Exception as e:
                logger.error(f"Error running ongoing monitoring: {e}")
            
            await asyncio.sleep(60)  # Check every minute
    
    async def _check_monitoring(self, monitoring: OngoingMonitoring) -> List[Dict[str, Any]]:
        """
        Check monitoring with the provider.
        
        Args:
            monitoring: Monitoring configuration
            
        Returns:
            List of alerts if any, empty list otherwise
        """
        # In a real implementation, this would make API calls to the AML provider
        # For demonstration, we'll simulate provider integration
        
        # Simulate API call delay
        await asyncio.sleep(random.uniform(0.2, 1.0))
        
        # 10% chance of generating an alert
        if random.random() < 0.1:
            # Generate a random alert
            alert_types = [
                "sanctions_list_addition",
                "adverse_media",
                "suspicious_transaction",
                "high_risk_jurisdiction",
                "unusual_activity"
            ]
            
            alert_type = random.choice(alert_types)
            risk_score = random.uniform(0.4, 0.95)
            
            return [{
                "alert_id": str(uuid.uuid4()),
                "alert_type": alert_type,
                "risk_score": risk_score,
                "timestamp": int(time.time()),
                "description": f"Monitoring alert: {alert_type}",
                "details": {
                    "provider": monitoring.provider.value,
                    "monitoring_type": monitoring.monitoring_type,
                    "entity": monitoring.user_id or monitoring.address
                }
            }]
        
        return []
    
    def update_user_risk_level(self, user_id: str, risk_level: RiskLevel, reason: str) -> bool:
        """
        Update a user's risk level.
        
        Args:
            user_id: User ID
            risk_level: New risk level
            reason: Reason for the update
            
        Returns:
            True if successful, False otherwise
        """
        if user_id not in self.users:
            logger.error(f"User {user_id} not found")
            return False
        
        user = self.users[user_id]
        old_risk_level = user.risk_level
        
        # Update risk level
        user.risk_level = risk_level
        user.updated_at = int(time.time())
        
        # Add to metadata
        if "risk_level_history" not in user.metadata:
            user.metadata["risk_level_history"] = []
        
        user.metadata["risk_level_history"].append({
            "timestamp": int(time.time()),
            "old_level": old_risk_level.value,
            "new_level": risk_level.value,
            "reason": reason
        })
        
        # Trigger callback
        self._trigger_callbacks("risk_level_changed", {
            "user_id": user_id,
            "old_risk_level": old_risk_level.value,
            "new_risk_level": risk_level.value,
            "reason": reason
        })
        
        logger.info(
            f"Updated risk level for user {user_id} from {old_risk_level.value} to {risk_level.value}: {reason}"
        )
        
        return True
    
    def get_user(self, user_id: str) -> Optional[UserIdentity]:
        """
        Get a user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User if found, None otherwise
        """
        return self.users.get(user_id)
    
    def get_verification_attempt(self, attempt_id: str) -> Optional[VerificationAttempt]:
        """
        Get a verification attempt by ID.
        
        Args:
            attempt_id: Verification attempt ID
            
        Returns:
            Verification attempt if found, None otherwise
        """
        return self.verification_attempts.get(attempt_id)
    
    def get_screening_result(self, screening_id: str) -> Optional[ScreeningResult]:
        """
        Get a screening result by ID.
        
        Args:
            screening_id: Screening ID
            
        Returns:
            Screening result if found, None otherwise
        """
        return self.screening_results.get(screening_id)
    
    def get_monitoring(self, monitoring_id: str) -> Optional[OngoingMonitoring]:
        """
        Get a monitoring configuration by ID.
        
        Args:
            monitoring_id: Monitoring ID
            
        Returns:
            Monitoring configuration if found, None otherwise
        """
        return self.ongoing_monitoring.get(monitoring_id)
    
    def get_user_verifications(self, user_id: str) -> List[VerificationAttempt]:
        """
        Get all verification attempts for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of verification attempts
        """
        return [attempt for attempt in self.verification_attempts.values() if attempt.user_id == user_id]
    
    def get_user_screenings(self, user_id: str) -> List[ScreeningResult]:
        """
        Get all screening results for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of screening results
        """
        return [screening for screening in self.screening_results.values() if screening.user_id == user_id]
    
    def get_address_screenings(self, address: str) -> List[ScreeningResult]:
        """
        Get all screening results for an address.
        
        Args:
            address: Blockchain address
            
        Returns:
            List of screening results
        """
        return [screening for screening in self.screening_results.values() if screening.address == address]
    
    def get_aml_kyc_statistics(self) -> Dict[str, Any]:
        """
        Get AML/KYC statistics.
        
        Returns:
            AML/KYC statistics
        """
        # Count users by verification status
        verification_status_counts = {}
        for user in self.users.values():
            verification_status_counts[user.verification_status.value] = verification_status_counts.get(user.verification_status.value, 0) + 1
        
        # Count users by verification level
        verification_level_counts = {}
        for user in self.users.values():
            verification_level_counts[user.verification_level.value] = verification_level_counts.get(user.verification_level.value, 0) + 1
        
        # Count users by risk level
        risk_level_counts = {}
        for user in self.users.values():
            risk_level_counts[user.risk_level.value] = risk_level_counts.get(user.risk_level.value, 0) + 1
        
        # Count screening results
        screening_result_counts = {}
        for screening in self.screening_results.values():
            screening_result_counts[screening.result.value] = screening_result_counts.get(screening.result.value, 0) + 1
        
        # Count active monitoring
        active_monitoring_count = sum(1 for monitoring in self.ongoing_monitoring.values() if monitoring.status == "active")
        
        return {
            "total_users": len(self.users),
            "total_verification_attempts": len(self.verification_attempts),
            "total_screenings": len(self.screening_results),
            "total_monitoring": len(self.ongoing_monitoring),
            "verification_status_distribution": verification_status_counts,
            "verification_level_distribution": verification_level_counts,
            "risk_level_distribution": risk_level_counts,
            "screening_result_distribution": screening_result_counts,
            "active_monitoring": active_monitoring_count,
            "prohibited_users": risk_level_counts.get(RiskLevel.PROHIBITED.value, 0),
            "approved_users": verification_status_counts.get(VerificationStatus.APPROVED.value, 0)
        }
    
    def _trigger_callbacks(self, event_type: str, data: Any):
        """
        Trigger registered callbacks for an event.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        for callback in self.callbacks.get(event_type, []):
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Error in {event_type} callback: {e}")
    
    def register_callback(self, event_type: str, callback: Callable):
        """
        Register a callback for a specific event type.
        
        Args:
            event_type: Type of event to register for
            callback: Callback function
        """
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
            logger.info(f"Registered callback for event type '{event_type}'")
        else:
            logger.error(f"Unknown event type: {event_type}")
    
    async def shutdown(self):
        """Shutdown the AML/KYC integration system"""
        logger.info("Shutting down AML/KYC Integration")
        self.running = False
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        logger.info("AML/KYC Integration shutdown complete")


async def main():
    """Example usage of the AML/KYC Integration system"""
    # Create AML/KYC integration system
    aml_kyc = AMLKYCIntegration("aml_kyc_config.json")
    
    # Register callbacks
    aml_kyc.register_callback("verification_updated", lambda attempt: print(f"Verification updated: {attempt.status.value}"))
    
    # Create a user
    user_id = await aml_kyc.create_user({
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1990-01-01",
        "nationality": "US",
        "country_of_residence": "US",
        "address": {
            "street": "123 Main St",
            "city": "New York",
            "state": "NY",
            "postal_code": "10001",
            "country": "US"
        },
        "phone_number": "+1234567890"
    })
    
    if user_id:
        # Start verification
        attempt_id = await aml_kyc.start_verification(user_id, "standard")
        
        if attempt_id:
            # Submit a document
            await aml_kyc.submit_document(attempt_id, "passport", {
                "metadata": {
                    "country": "US",
                    "document_number": "123456789"
                }
            })
            
            # Check verification status
            status = await aml_kyc.check_verification_status(attempt_id)
            print(f"Verification status: {status}")
        
        # Screen user
        screening_id = await aml_kyc.screen_user(user_id, "sanctions")
        
        if screening_id:
            # Get screening result
            screening = aml_kyc.get_screening_result(screening_id)
            print(f"Screening result: {screening.result.value if screening else 'Not found'}")
        
        # Set up monitoring
        monitoring_id = await aml_kyc.setup_ongoing_monitoring(user_id=user_id)
        
        if monitoring_id:
            print(f"Monitoring set up with ID: {monitoring_id}")
    
    # Screen an address
    address_screening_id = await aml_kyc.screen_address("${CONTRACT_ADDRESS}", "sanctions")
    
    if address_screening_id:
        # Get screening result
        address_screening = aml_kyc.get_screening_result(address_screening_id)
        print(f"Address screening result: {address_screening.result.value if address_screening else 'Not found'}")
    
    # Get statistics
    stats = aml_kyc.get_aml_kyc_statistics()
    print(f"AML/KYC statistics: {stats}")
    
    # Run for a while to process verifications and monitoring
    await asyncio.sleep(10)
    
    # Shutdown
    await aml_kyc.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
"""
Quantum-Resistant Security Module
Provides post-quantum cryptographic algorithms and security features.
"""
from quantum_security.quantum_crypto import (
    DilithiumSignature,
    SPHINCSPlusSignature,
    QuantumKeyDistribution,
    QuantumResistantEncryption,
    GnuPGQuantumExtensions,
    get_quantum_security_status
)
from quantum_security.gnupg_quantum import (
    GnuPGQuantumConfig,
    get_gnupg_quantum_commands,
    execute_gnupg_command
)
from quantum_security.gnupg_integration import (
    GnuPGTransactionSigner,
    GnuPGEncryption
)
from quantum_security.hardware_token import HardwareTokenManager
from quantum_security.quantum_security_manager import QuantumSecurityManager

__version__ = "0.1.0"
__all__ = [
    "DilithiumSignature",
    "SPHINCSPlusSignature",
    "QuantumKeyDistribution",
    "QuantumResistantEncryption",
    "GnuPGQuantumExtensions",
    "get_quantum_security_status",
    "GnuPGQuantumConfig",
    "get_gnupg_quantum_commands",
    "execute_gnupg_command",
    "GnuPGTransactionSigner",
    "GnuPGEncryption",
    "HardwareTokenManager",
    "QuantumSecurityManager"
]
"""
Hardware Token Integration Module
Provides integration with hardware security tokens like YubiKey.
"""
import os
import subprocess
import logging
import json
import tempfile
from typing import Dict, List, Optional, Any, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HardwareTokenManager:
    """
    Manager for hardware security tokens.
    """
    
    def __init__(self, gnupghome: str = None):
        """
        Initialize hardware token manager.
        
        Args:
            gnupghome: Path to GnuPG home directory
        """
        self.gnupghome = gnupghome or os.path.expanduser('~/.gnupg')
        
        # Ensure GnuPG home directory exists
        os.makedirs(self.gnupghome, exist_ok=True)
        
        logger.info("Initialized Hardware Token Manager")
    
    def detect_tokens(self) -> List[Dict[str, Any]]:
        """
        Detect connected hardware tokens.
        
        Returns:
            List of dictionaries containing token information
        """
        tokens = []
        
        try:
            # Run gpg --card-status to detect tokens
            env = os.environ.copy()
            env['GNUPGHOME'] = self.gnupghome
            
            result = subprocess.run(
                ['gpg', '--card-status'],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                # Parse output to extract token information
                lines = result.stdout.split('\n')
                current_token = {}
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    if line.startswith('Reader'):
                        # New token
                        if current_token:
                            tokens.append(current_token)
                        current_token = {'reader': line.split(':', 1)[1].strip()}
                    elif ':' in line:
                        key, value = line.split(':', 1)
                        current_token[key.strip().lower().replace(' ', '_')] = value.strip()
                
                if current_token:
                    tokens.append(current_token)
            else:
                logger.warning(f"Failed to detect tokens: {result.stderr}")
        except Exception as e:
            logger.error(f"Error detecting tokens: {e}")
        
        logger.info(f"Detected {len(tokens)} hardware tokens")
        return tokens
    
    def setup_token(self, name: str, email: str, backup_dir: Optional[str] = None) -> bool:
        """
        Set up a hardware token with GPG keys.
        
        Args:
            name: Name for the key
            email: Email for the key
            backup_dir: Directory to store key backups (optional)
            
        Returns:
            True if setup was successful, False otherwise
        """
        try:
            # Create temporary script file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as script_file:
                script_path = script_file.name
                
                # Write setup script
                script_file.write(f"""#!/bin/bash
# GnuPG Hardware Token Setup Script

# Set GnuPG home directory
export GNUPGHOME="{self.gnupghome}"

# 1. Configure GPG for hardware tokens
echo "Setting up GPG hardware token integration..."

# 2. YubiKey configuration
gpg --card-edit << EOF
admin
passwd
3
new_pin
new_pin
1
new_pin
new_pin
q
quit
EOF

# 3. Generate on-card keys
gpg --card-edit << EOF
admin
generate
n
0
y
{name}
{email}
O
quit
EOF

# 4. Create backup
""")
                
                if backup_dir:
                    os.makedirs(backup_dir, exist_ok=True)
                    script_file.write(f"""
gpg --armor --export-secret-keys > "{backup_dir}/trading_keys_backup.asc"
gpg --armor --export-secret-subkeys > "{backup_dir}/trading_subkeys_backup.asc"
""")
                
                script_file.write("""
echo "Hardware token setup complete!"
""")
            
            # Make script executable
            os.chmod(script_path, 0o755)
            
            # Run setup script
            env = os.environ.copy()
            env['GNUPGHOME'] = self.gnupghome
            
            logger.info(f"Running hardware token setup script for {name} <{email}>")
            result = subprocess.run(
                [script_path],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            # Clean up script file
            os.unlink(script_path)
            
            if result.returncode == 0:
                logger.info("Hardware token setup completed successfully")
                return True
            else:
                logger.error(f"Hardware token setup failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error setting up hardware token: {e}")
            return False
    
    def get_token_status(self) -> Dict[str, Any]:
        """
        Get status of connected hardware token.
        
        Returns:
            Dictionary containing token status
        """
        status = {
            'detected': False,
            'has_keys': False,
            'details': {}
        }
        
        try:
            # Run gpg --card-status to get token status
            env = os.environ.copy()
            env['GNUPGHOME'] = self.gnupghome
            
            result = subprocess.run(
                ['gpg', '--card-status'],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                status['detected'] = True
                
                # Parse output to extract token information
                lines = result.stdout.split('\n')
                details = {}
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    if ':' in line:
                        key, value = line.split(':', 1)
                        details[key.strip().lower().replace(' ', '_')] = value.strip()
                
                status['details'] = details
                
                # Check if token has keys
                if 'key_attributes' in details:
                    status['has_keys'] = True
            else:
                logger.warning(f"Failed to get token status: {result.stderr}")
        except Exception as e:
            logger.error(f"Error getting token status: {e}")
        
        return status
    
    def backup_keys(self, backup_dir: str) -> bool:
        """
        Backup GPG keys.
        
        Args:
            backup_dir: Directory to store key backups
            
        Returns:
            True if backup was successful, False otherwise
        """
        try:
            os.makedirs(backup_dir, exist_ok=True)
            
            # Run gpg to export keys
            env = os.environ.copy()
            env['GNUPGHOME'] = self.gnupghome
            
            # Export public keys
            public_result = subprocess.run(
                ['gpg', '--armor', '--export'],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            if public_result.returncode == 0:
                with open(os.path.join(backup_dir, 'public_keys_backup.asc'), 'w') as f:
                    f.write(public_result.stdout)
                logger.info(f"Backed up public keys to {backup_dir}/public_keys_backup.asc")
            else:
                logger.error(f"Failed to export public keys: {public_result.stderr}")
                return False
            
            # Export secret keys
            secret_result = subprocess.run(
                ['gpg', '--armor', '--export-secret-keys'],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            if secret_result.returncode == 0:
                with open(os.path.join(backup_dir, 'secret_keys_backup.asc'), 'w') as f:
                    f.write(secret_result.stdout)
                logger.info(f"Backed up secret keys to {backup_dir}/secret_keys_backup.asc")
            else:
                logger.error(f"Failed to export secret keys: {secret_result.stderr}")
                return False
            
            # Export secret subkeys
            subkey_result = subprocess.run(
                ['gpg', '--armor', '--export-secret-subkeys'],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            if subkey_result.returncode == 0:
                with open(os.path.join(backup_dir, 'secret_subkeys_backup.asc'), 'w') as f:
                    f.write(subkey_result.stdout)
                logger.info(f"Backed up secret subkeys to {backup_dir}/secret_subkeys_backup.asc")
            else:
                logger.error(f"Failed to export secret subkeys: {subkey_result.stderr}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error backing up keys: {e}")
            return False
    
    def restore_keys(self, backup_dir: str) -> bool:
        """
        Restore GPG keys from backup.
        
        Args:
            backup_dir: Directory containing key backups
            
        Returns:
            True if restore was successful, False otherwise
        """
        try:
            # Check if backup files exist
            public_key_path = os.path.join(backup_dir, 'public_keys_backup.asc')
            secret_key_path = os.path.join(backup_dir, 'secret_keys_backup.asc')
            
            if not os.path.exists(public_key_path) or not os.path.exists(secret_key_path):
                logger.error(f"Backup files not found in {backup_dir}")
                return False
            
            # Run gpg to import keys
            env = os.environ.copy()
            env['GNUPGHOME'] = self.gnupghome
            
            # Import secret keys first
            with open(secret_key_path, 'r') as f:
                secret_key_data = f.read()
            
            secret_result = subprocess.run(
                ['gpg', '--import'],
                input=secret_key_data,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            if secret_result.returncode != 0:
                logger.error(f"Failed to import secret keys: {secret_result.stderr}")
                return False
            
            # Import public keys
            with open(public_key_path, 'r') as f:
                public_key_data = f.read()
            
            public_result = subprocess.run(
                ['gpg', '--import'],
                input=public_key_data,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            if public_result.returncode != 0:
                logger.error(f"Failed to import public keys: {public_result.stderr}")
                return False
            
            logger.info(f"Restored keys from {backup_dir}")
            return True
        except Exception as e:
            logger.error(f"Error restoring keys: {e}")
            return False


if __name__ == "__main__":
    # Example usage
    token_manager = HardwareTokenManager()
    
    # Detect tokens
    tokens = token_manager.detect_tokens()
    print(f"Detected {len(tokens)} tokens:")
    for token in tokens:
        print(f"- {token.get('reader', 'Unknown')}")
    
    # Get token status
    status = token_manager.get_token_status()
    print(f"Token detected: {status['detected']}")
    print(f"Token has keys: {status['has_keys']}")
    
    # Backup keys
    backup_dir = os.path.expanduser("~/key_backup")
    if status['detected'] and status['has_keys']:
        print(f"Backing up keys to {backup_dir}")
        token_manager.backup_keys(backup_dir)
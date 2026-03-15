#!/bin/bash
# GnuPG Hardware Token Setup Script

# Check if arguments are provided
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <name> <email> [backup_dir]"
    echo "Example: $0 \"Trading System Key\" trading@arbitrage.system /secure/backup"
    exit 1
fi

NAME="$1"
EMAIL="$2"
BACKUP_DIR="${3:-./backup}"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "Setting up GPG hardware token integration..."
echo "Name: $NAME"
echo "Email: $EMAIL"
echo "Backup directory: $BACKUP_DIR"

# 1. Configure GPG for hardware tokens
echo "Configuring GPG for hardware tokens..."

# 2. YubiKey configuration
echo "Configuring YubiKey..."
echo "You will be prompted to set PINs for the YubiKey."
echo "Admin PIN (default: 12345678)"
echo "User PIN (default: 123456)"

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
echo "Generating on-card keys..."
echo "This will create a new key pair on the YubiKey."

gpg --card-edit << EOF
admin
generate
n
0
y
$NAME
$EMAIL
O
quit
EOF

# 4. Create backup
echo "Creating key backups..."

gpg --armor --export > "$BACKUP_DIR/trading_public_keys.asc"
gpg --armor --export-secret-keys > "$BACKUP_DIR/trading_keys_backup.asc"
gpg --armor --export-secret-subkeys > "$BACKUP_DIR/trading_subkeys_backup.asc"

echo "Hardware token setup complete!"
echo "Backups saved to $BACKUP_DIR"
echo ""
echo "IMPORTANT: Store these backups securely!"
echo "- Public keys: $BACKUP_DIR/trading_public_keys.asc"
echo "- Secret keys: $BACKUP_DIR/trading_keys_backup.asc"
echo "- Secret subkeys: $BACKUP_DIR/trading_subkeys_backup.asc"
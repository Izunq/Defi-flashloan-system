# Environment Configuration Script
param(
    [ValidateSet("production", "test", "development")]
    [string]$Environment = "development"
)

Write-Host "Setting up environment configuration for: $Environment" -ForegroundColor Cyan

function Copy-EnvironmentTemplate {
    param($env)
    $templateFile = ".env.$env.template"
    $targetFile = ".env.$env"
    
    if (Test-Path $templateFile) {
        Copy-Item $templateFile $targetFile -Force
        Write-Host "Created $targetFile from template" -ForegroundColor Green
        return $true
    } else {
        Write-Host "Template file $templateFile not found" -ForegroundColor Red
        return $false
    }
}

function Update-EnvironmentFile {
    param($envFile)
    
    Write-Host "`n🔧 Updating $envFile with secure defaults..." -ForegroundColor Yellow
    
    # Generate secure random values
    $encryptionKey = [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((New-Guid).ToString().Replace("-", "").Substring(0, 32)))
    $jwtSecret = (New-Guid).ToString() + (New-Guid).ToString()
    
    # Update the file with generated values
    if (Test-Path $envFile) {
        $content = Get-Content $envFile
        
        # Replace template values with generated ones
        $content = $content -replace "YOUR_32_BYTE_ENCRYPTION_KEY_HERE", $encryptionKey
        $content = $content -replace "YOUR_JWT_SECRET_KEY_HERE", $jwtSecret
        
        # Save updated content
        $content | Out-File $envFile -Encoding UTF8
        
        Write-Host "✅ Updated $envFile with secure generated values" -ForegroundColor Green
        Write-Host "⚠️ Please update the API keys and other configuration values manually" -ForegroundColor Yellow
    }
}

# Main execution
switch ($Environment) {
    "production" {
        if (Copy-EnvironmentTemplate "production") {
            Update-EnvironmentFile ".env.production"
            Write-Host "`n🔒 IMPORTANT: Update all API keys and sensitive data in .env.production" -ForegroundColor Red
        }
    }
    "test" {
        if (Copy-EnvironmentTemplate "test") {
            Update-EnvironmentFile ".env.test"
            Write-Host "`n✅ Test environment configured" -ForegroundColor Green
        }
    }
    "development" {
        # Create development environment from test template
        if (Test-Path ".env.test.template") {
            Copy-Item ".env.test.template" ".env"
            Update-EnvironmentFile ".env"
            Write-Host "✅ Development environment configured (.env)" -ForegroundColor Green
        }
    }
}

# Create environment validation script
$validationScript = @"
# Environment Variable Validation Script
import os
import sys
from typing import List, Dict, Any

class EnvironmentValidator:
    def __init__(self, env_file: str = '.env'):
        self.env_file = env_file
        self.required_vars = {
            'production': [
                'ETHEREUM_MAINNET_RPC_URL',
                'PRIVATE_KEY',
                'OPENAI_API_KEY',
                'ENCRYPTION_KEY',
                'JWT_SECRET'
            ],
            'test': [
                'ETHEREUM_TESTNET_RPC_URL',
                'OPENAI_API_KEY',
                'ENCRYPTION_KEY',
                'JWT_SECRET'
            ],
            'development': [
                'OPENAI_API_KEY'
            ]
        }
    
    def load_env_file(self) -> Dict[str, str]:
        env_vars = {}
        try:
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key] = value
        except FileNotFoundError:
            print(f"❌ Environment file {self.env_file} not found")
            return {}
        return env_vars
    
    def validate_environment(self, environment: str = 'development') -> bool:
        print(f"🔍 Validating {environment} environment...")
        
        env_vars = self.load_env_file()
        if not env_vars:
            return False
        
        required = self.required_vars.get(environment, [])
        missing_vars = []
        placeholder_vars = []
        
        for var in required:
            if var not in env_vars:
                missing_vars.append(var)
            elif 'YOUR_' in env_vars[var] or 'CHANGE_ME' in env_vars[var]:
                placeholder_vars.append(var)
        
        # Report results
        if missing_vars:
            print(f"❌ Missing required variables: {', '.join(missing_vars)}")
        
        if placeholder_vars:
            print(f"⚠️ Variables still using placeholders: {', '.join(placeholder_vars)}")
        
        if not missing_vars and not placeholder_vars:
            print("✅ All environment variables properly configured!")
            return True
        
        return False
    
    def generate_config_summary(self) -> None:
        env_vars = self.load_env_file()
        print(f"📊 Configuration Summary ({len(env_vars)} variables loaded):")
        
        categories = {
            'Blockchain': ['ETHEREUM_', 'POLYGON_', 'BSC_', 'ARBITRUM_'],
            'APIs': ['OPENAI_', 'INFURA_', 'ALCHEMY_', 'COINGECKO_'],
            'Security': ['PRIVATE_KEY', 'ENCRYPTION_KEY', 'JWT_SECRET'],
            'Trading': ['MAX_POSITION_SIZE', 'MIN_PROFIT_THRESHOLD', 'MAX_SLIPPAGE'],
            'Monitoring': ['SLACK_', 'TELEGRAM_', 'EMAIL_']
        }
        
        for category, prefixes in categories.items():
            count = sum(1 for var in env_vars if any(var.startswith(prefix) for prefix in prefixes))
            if count > 0:
                print(f"  {category}: {count} variables")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate environment configuration')
    parser.add_argument('--env', choices=['production', 'test', 'development'], 
                       default='development', help='Environment to validate')
    parser.add_argument('--file', default='.env', help='Environment file to validate')
    
    args = parser.parse_args()
    
    validator = EnvironmentValidator(args.file)
    
    if validator.validate_environment(args.env):
        validator.generate_config_summary()
        sys.exit(0)
    else:
        print("❌ Environment validation failed")
        sys.exit(1)
"@

$validationScript | Out-File -FilePath "validate_environment.py" -Encoding UTF8
Write-Host "✅ Created environment validation script: validate_environment.py" -ForegroundColor Green

Write-Host "`n🎯 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Update API keys in your environment file" -ForegroundColor White
Write-Host "2. Run validation: python validate_environment.py --env $Environment" -ForegroundColor White
Write-Host "3. Test configuration with your application" -ForegroundColor White

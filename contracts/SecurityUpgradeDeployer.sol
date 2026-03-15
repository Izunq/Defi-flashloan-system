// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

import "./SecurityEnhancedExecutor.sol";
import "./SecureMultiOracle.sol";
import "./GasOptimizedArbitrageExecutor.sol";

/**
 * @title SecurityUpgradeDeployer
 * @notice Deploys and configures the new security-enhanced contracts
 * @dev This contract ensures secure deployment and proper configuration
 */
contract SecurityUpgradeDeployer {
    event SecurityContractsDeployed(
        address securityExecutor,
        address multiOracle,
        address upgradeAdmin
    );
    
    event SecurityConfigurationComplete(
        address executor,
        uint256 timelockDelay,
        uint256 maxGasPrice
    );
    
    address public immutable deployer;
    address public securityExecutor;
    address public multiOracle;
    bool public deployed;
    
    modifier onlyDeployer() {
        require(msg.sender == deployer, "Only deployer");
        _;
    }
    
    modifier notDeployed() {
        require(!deployed, "Already deployed");
        _;
    }
    
    constructor() {
        deployer = msg.sender;
    }
    
    /**
     * @notice Deploy security-enhanced contracts
     * @param _timelockDelay Delay for timelock operations (recommended: 24 hours)
     * @param _maxGasPrice Maximum gas price protection (in wei)
     * @param _oracles Array of oracle addresses for multi-oracle setup
     */
    function deploySecurity(
        uint256 _timelockDelay,
        uint256 _maxGasPrice,
        address[] calldata _oracles
    ) external onlyDeployer notDeployed nonReentrant{
        require(_timelockDelay >= 1 hours, "Timelock too short");
        require(_maxGasPrice > 0, "Invalid gas price");
        require(_oracles.length >= 3, "Need at least 3 oracles");
        
        // Deploy SecurityEnhancedExecutor
        securityExecutor = address(new SecurityEnhancedExecutor(
            _timelockDelay,
            _maxGasPrice
        ));
        
        // Deploy SecureMultiOracle
        multiOracle = address(new SecureMultiOracle(_oracles));
        
        deployed = true;
        
        emit SecurityContractsDeployed(
            securityExecutor,
            multiOracle,
            deployer
        );
    }
    
    /**
     * @notice Configure the deployed security contracts
     * @param _multisigWallet Multi-signature wallet for admin operations
     * @param _emergencyAdmin Emergency admin for circuit breaker
     */
    function configureSecurity(
        address _multisigWallet,
        address _emergencyAdmin
    ) external onlyDeployer nonReentrant{
        require(deployed, "Not deployed yet");
        require(_multisigWallet != address(0), "Invalid multisig");
        require(_emergencyAdmin != address(0), "Invalid emergency admin");
        
        SecurityEnhancedExecutor executor = SecurityEnhancedExecutor(securityExecutor);
        SecureMultiOracle oracle = SecureMultiOracle(multiOracle);
        
        // Grant roles to multi-sig wallet
        executor.grantRole(executor.ADMIN_ROLE(), _multisigWallet);
        oracle.grantRole(oracle.ADMIN_ROLE(), _multisigWallet);
        
        // Grant emergency roles
        executor.grantRole(executor.EMERGENCY_ROLE(), _emergencyAdmin);
        oracle.grantRole(oracle.EMERGENCY_ROLE(), _emergencyAdmin);
        
        // Revoke deployer roles for security
        executor.revokeRole(executor.DEFAULT_ADMIN_ROLE(), deployer);
        oracle.revokeRole(oracle.DEFAULT_ADMIN_ROLE(), deployer);
        
        emit SecurityConfigurationComplete(
            securityExecutor,
            executor.timelockDelay(),
            executor.maxGasPrice()
        );
    }
    
    /**
     * @notice Get deployment status and addresses
     */
    function getDeploymentInfo() external view returns (
        bool _deployed,
        address _securityExecutor,
        address _multiOracle,
        address _deployer
    ) {
        return (deployed, securityExecutor, multiOracle, deployer);
    }
}

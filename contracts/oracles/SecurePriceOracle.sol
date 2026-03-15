// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

import "../security/SystemAccessControl.sol";

interface IPriceOracle {
    function getLatestPrice(address asset) external view returns (uint256);
}

/**
 * @title SecurePriceOracle
 * @dev Aggregates prices from multiple oracles and returns a median price.
 */
contract SecurePriceOracle is SystemAccessControl, ReentrancyGuard {
    
    mapping(address => IPriceOracle[]) public priceOracles;

    event OracleAdded(address indexed asset, address indexed oracle);
    event OracleRemoved(address indexed asset, address indexed oracle);

    modifier onlyOracleManager() {
        require(hasRole(ORACLE_MANAGER_ROLE, msg.sender), "Caller is not an oracle manager");
        _;
    }

    function addOracle(address asset, address oracle) external onlyOracleManager nonReentrant{
        priceOracles[asset].push(IPriceOracle(oracle));
        emit OracleAdded(asset, oracle);
    }

    function getMedianPrice(address asset) external view returns (uint256)  {
        // TODO: Add nonReentrant modifier
        IPriceOracle[] memory oracles = priceOracles[asset];
        require(oracles.length > 0, "No oracles for this asset");

        uint256[] memory prices = new uint256[](oracles.length);
        for (uint i = 0; i < oracles.length; i++) {
            prices[i] = oracles[i].getLatestPrice(asset);
        }

        // Simple sorting for median calculation (for up to ~20 oracles this is fine)
        for (uint i = 0; i < prices.length - 1; i++) {
            for (uint j = i + 1; j < prices.length; j++) {
                if (prices[i] > prices[j]) {
                    (prices[i], prices[j]) = (prices[j], prices[i]);
                }
            }
        }

        // Return the median price
        return prices[prices.length / 2];
    }
}

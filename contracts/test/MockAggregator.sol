// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title MockAggregator — Chainlink AggregatorV3 mock for testing PriceOracle
contract MockAggregator {
    int256 public price;
    uint8 public decimals_ = 8;
    uint256 public updatedAt;

    constructor(int256 _price) {
        price = _price;
        updatedAt = block.timestamp;
    }

    function setPrice(int256 _price) external {
        price = _price;
        updatedAt = block.timestamp;
    }

    function setStale(uint256 _updatedAt) external {
        updatedAt = _updatedAt;
    }

    function decimals() external view returns (uint8) {
        return decimals_;
    }

    function latestRoundData()
        external
        view
        returns (uint80, int256, uint256, uint256, uint80)
    {
        return (0, price, 0, updatedAt, 0);
    }
}

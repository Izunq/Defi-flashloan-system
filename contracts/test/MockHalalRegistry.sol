// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title MockHalalRegistry — Simplified halal registry for testing MudarabahPool
contract MockHalalRegistry {
    mapping(address => bool) public compliant;

    function setCompliant(address token, bool value) external {
        compliant[token] = value;
    }

    function isHalalCompliant(address token) external view returns (bool) {
        return compliant[token];
    }

    function isBlacklisted(address /* token */) external pure returns (bool) {
        return false;
    }
}

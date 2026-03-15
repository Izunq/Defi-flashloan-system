// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

/// @title MockMudarib — Simulates a mudarib that receives tokens, does a "trade",
///        and returns tokens (possibly with profit) to the pool.
contract MockMudarib {
    /// @dev Accept ETH so tests can fund this address for gas when impersonating.
    receive() external payable {}

    /// @notice Execute a "trade": simply transfer `returnAmount` of `token` back to `pool`.
    /// @dev    The mock must hold enough tokens to return.
    function execute(
        address token,
        address pool,
        uint256 returnAmount
    ) external {
        IERC20(token).transfer(pool, returnAmount);
    }
}

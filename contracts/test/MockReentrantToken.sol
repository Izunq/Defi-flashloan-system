// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";

interface IPool {
    function deposit(address token, uint256 amount) external;
}

/// @title MockReentrantToken — ERC20 that attempts reentrancy on transferFrom
/// @dev Used to test that MudarabahPool.deposit() is protected by nonReentrant.
///      When `armed` is true, transferFrom will call pool.deposit() before
///      completing the transfer, simulating an ERC-777-style hook attack.
contract MockReentrantToken is ERC20 {
    address public pool;
    bool public armed;
    uint256 public reentrantAmount;

    constructor() ERC20("Reentrant Token", "REENTER") {}

    function mint(address to, uint256 amount) external {
        _mint(to, amount);
    }

    function arm(address _pool, uint256 _amount) external {
        pool = _pool;
        armed = true;
        reentrantAmount = _amount;
    }

    function disarm() external {
        armed = false;
    }

    function transferFrom(address from, address to, uint256 amount) public override returns (bool) {
        // Attempt reentry into pool.deposit() before completing the transfer
        if (armed && to == pool) {
            armed = false; // prevent infinite recursion
            IPool(pool).deposit(address(this), reentrantAmount);
        }
        return super.transferFrom(from, to, amount);
    }

    function decimals() public pure override returns (uint8) {
        return 18;
    }
}

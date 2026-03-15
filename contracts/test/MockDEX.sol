// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {ISwapRouter} from "../interfaces/ISwapRouter.sol";

/// @title MockDEX — Simulates a Uniswap V3 style DEX for testing
/// @notice Exchanges tokens at a configurable rate expressed in basis points
///         (e.g. 10100 = 1.01x, 10000 = 1.00x, 9900 = 0.99x)
contract MockDEX {
    uint256 public exchangeRate; // in basis points, e.g., 10100 = 1.01x

    constructor(uint256 _rate) {
        exchangeRate = _rate;
    }

    function setRate(uint256 _rate) external {
        exchangeRate = _rate;
    }

    function exactInputSingle(
        ISwapRouter.ExactInputSingleParams calldata params
    ) external payable returns (uint256) {
        IERC20(params.tokenIn).transferFrom(
            msg.sender,
            address(this),
            params.amountIn
        );

        uint256 amountOut = (params.amountIn * exchangeRate) / 10000;
        require(amountOut >= params.amountOutMinimum, "Slippage");

        IERC20(params.tokenOut).transfer(msg.sender, amountOut);
        return amountOut;
    }
}

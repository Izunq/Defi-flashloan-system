// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {ISwapRouter} from "../interfaces/ISwapRouter.sol";

/// @title SwapHelper — Uniswap V3 single-hop swap helper
/// @notice Library that wraps the approval + exactInputSingle pattern into a
///         single reusable call.  Designed for use inside flash-loan callbacks
///         where capital is only available for the duration of the transaction.
library SwapHelper {
    using SafeERC20 for IERC20;

    /// @notice Execute a single-hop exact-input swap on a Uniswap V3 style router
    /// @param router           The ISwapRouter-compatible DEX router
    /// @param tokenIn          Token being sold
    /// @param tokenOut         Token being bought
    /// @param fee              Pool fee tier (e.g. 500, 3000, 10000)
    /// @param amountIn         Amount of `tokenIn` to sell
    /// @param amountOutMinimum Minimum acceptable amount of `tokenOut` (slippage guard)
    /// @return amountOut       Actual amount of `tokenOut` received
    function executeSwap(
        ISwapRouter router,
        address tokenIn,
        address tokenOut,
        uint24 fee,
        uint256 amountIn,
        uint256 amountOutMinimum
    ) internal returns (uint256 amountOut) {
        // Approve the router to pull tokenIn
        IERC20(tokenIn).safeIncreaseAllowance(address(router), amountIn);

        // Build the swap parameters
        ISwapRouter.ExactInputSingleParams memory params = ISwapRouter
            .ExactInputSingleParams({
                tokenIn: tokenIn,
                tokenOut: tokenOut,
                fee: fee,
                recipient: address(this),
                deadline: block.timestamp,
                amountIn: amountIn,
                amountOutMinimum: amountOutMinimum,
                sqrtPriceLimitX96: 0
            });

        // Execute the swap
        amountOut = router.exactInputSingle(params);
    }
}

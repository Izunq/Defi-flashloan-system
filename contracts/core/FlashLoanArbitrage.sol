// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {Pausable} from "@openzeppelin/contracts/utils/Pausable.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

import {IAaveV3Pool} from "../interfaces/IAaveV3Pool.sol";
import {ISwapRouter} from "../interfaces/ISwapRouter.sol";
import {SwapHelper} from "../libraries/SwapHelper.sol";

/// @title FlashLoanArbitrage — Core flash-loan arbitrage executor for Arbitrum One
/// @notice Borrows a single asset from Aave V3 via `flashLoanSimple`, arbitrages
///         across two Uniswap-V3-style DEXes, repays the loan + premium, and
///         forwards the remaining profit to a configurable receiver.
/// @dev    All swap logic is delegated to the `SwapHelper` library.  The two-leg
///         arbitrage parameters are packed into a `SwapRoute` struct to stay within
///         the EVM stack-depth limit.
contract FlashLoanArbitrage is AccessControl, ReentrancyGuard, Pausable {
    using SafeERC20 for IERC20;

    // ─── Types ──────────────────────────────────────────────────────────
    /// @notice Describes a two-leg swap route for the arbitrage
    struct SwapRoute {
        address dexA; // Router for leg 1 (asset -> tokenOut)
        address dexB; // Router for leg 2 (tokenOut -> asset)
        address tokenOut; // Intermediate token
        uint24 feeA; // Pool fee tier on dexA
        uint24 feeB; // Pool fee tier on dexB
        uint256 amountOutMinA; // Min output for leg 1
        uint256 amountOutMinB; // Min output for leg 2
    }

    // ─── Roles ───────────────────────────────────────────────────────────
    /// @notice EXECUTOR_ROLE holders are permitted to trigger flash loans
    bytes32 public constant EXECUTOR_ROLE = keccak256("EXECUTOR_ROLE");

    // ─── Immutables ──────────────────────────────────────────────────────
    /// @notice The Aave V3 pool used for flash loans
    IAaveV3Pool public immutable aavePool;

    // ─── State ───────────────────────────────────────────────────────────
    /// @notice Address that receives arbitrage profits
    address public profitReceiver;

    // ─── Events ──────────────────────────────────────────────────────────
    event FlashLoanExecuted(
        address indexed asset,
        uint256 amount,
        uint256 profit
    );
    event ProfitReceiverUpdated(
        address indexed oldReceiver,
        address indexed newReceiver
    );
    event TokenWithdrawn(
        address indexed token,
        uint256 amount,
        address indexed to
    );

    // ─── Errors ──────────────────────────────────────────────────────────
    error ZeroAddress();
    error InsufficientBalanceToRepay(uint256 balance, uint256 totalOwed);
    error UnauthorizedCaller();
    error UnauthorizedInitiator();

    // ─── Constructor ─────────────────────────────────────────────────────
    /// @param _aavePool       Address of the Aave V3 Pool on Arbitrum
    /// @param _profitReceiver Address that will receive arbitrage profits
    constructor(address _aavePool, address _profitReceiver) {
        if (_aavePool == address(0) || _profitReceiver == address(0)) {
            revert ZeroAddress();
        }

        aavePool = IAaveV3Pool(_aavePool);
        profitReceiver = _profitReceiver;

        // OZ 5.x: use _grantRole (not _setupRole)
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(EXECUTOR_ROLE, msg.sender);
    }

    // ─── External — trigger ──────────────────────────────────────────────

    /// @notice Request a flash loan from Aave V3
    /// @param asset  The ERC-20 token to borrow
    /// @param amount The amount to borrow
    /// @param params ABI-encoded `SwapRoute` consumed by `executeOperation`
    function executeFlashLoan(
        address asset,
        uint256 amount,
        bytes calldata params
    ) external onlyRole(EXECUTOR_ROLE) whenNotPaused nonReentrant {
        aavePool.flashLoanSimple(address(this), asset, amount, params, 0);
    }

    // ─── External — Aave callback ────────────────────────────────────────

    /// @notice Aave V3 flash-loan callback executed atomically after funds arrive
    /// @dev    Only the Aave pool may call this, and only if *this* contract
    ///         initiated the loan.  Decodes a `SwapRoute` from `params`, runs
    ///         both swap legs, repays the loan + premium, and forwards profit.
    /// @param asset     The borrowed asset
    /// @param amount    The borrowed amount
    /// @param premium   The flash-loan fee owed to Aave
    /// @param initiator The address that initiated the flash loan
    /// @param params    ABI-encoded (address, address, address, uint24, uint24, uint256, uint256)
    /// @return true on success (required by Aave)
    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address initiator,
        bytes calldata params
    ) external returns (bool) {
        // ── Guards ───────────────────────────────────────────────────────
        if (msg.sender != address(aavePool)) revert UnauthorizedCaller();
        if (initiator != address(this)) revert UnauthorizedInitiator();

        // ── Decode & execute ─────────────────────────────────────────────
        SwapRoute memory route = abi.decode(params, (SwapRoute));
        uint256 profit = _executeArbitrage(asset, amount, premium, route);

        emit FlashLoanExecuted(asset, amount, profit);
        return true;
    }

    // ─── Internal — arbitrage logic ──────────────────────────────────────

    /// @dev Runs both swap legs, repays Aave, and sends profit to the receiver.
    ///      Separated from `executeOperation` to keep local-variable count within
    ///      the EVM stack-depth limit.
    function _executeArbitrage(
        address asset,
        uint256 amount,
        uint256 premium,
        SwapRoute memory route
    ) private returns (uint256 profit) {
        // Leg 1: asset -> tokenOut on dexA
        uint256 intermediateAmount = SwapHelper.executeSwap(
            ISwapRouter(route.dexA),
            asset,
            route.tokenOut,
            route.feeA,
            amount,
            route.amountOutMinA
        );

        // Leg 2: tokenOut -> asset on dexB
        SwapHelper.executeSwap(
            ISwapRouter(route.dexB),
            route.tokenOut,
            asset,
            route.feeB,
            intermediateAmount,
            route.amountOutMinB
        );

        // Repay loan
        uint256 totalOwed = amount + premium;
        uint256 balance = IERC20(asset).balanceOf(address(this));
        if (balance < totalOwed) {
            revert InsufficientBalanceToRepay(balance, totalOwed);
        }

        // Approve Aave pool to pull back the owed amount
        IERC20(asset).safeIncreaseAllowance(address(aavePool), totalOwed);

        // Forward profit
        profit = balance - totalOwed;
        if (profit > 0) {
            IERC20(asset).safeTransfer(profitReceiver, profit);
        }
    }

    // ─── Admin helpers ───────────────────────────────────────────────────

    /// @notice Update the address that receives arbitrage profits
    /// @param _receiver New profit receiver (must be non-zero)
    function setProfitReceiver(
        address _receiver
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        if (_receiver == address(0)) revert ZeroAddress();
        address old = profitReceiver;
        profitReceiver = _receiver;
        emit ProfitReceiverUpdated(old, _receiver);
    }

    /// @notice Recover tokens accidentally sent to this contract
    /// @param token  ERC-20 token address
    /// @param amount Amount to withdraw
    function withdrawToken(
        address token,
        uint256 amount
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        IERC20(token).safeTransfer(msg.sender, amount);
        emit TokenWithdrawn(token, amount, msg.sender);
    }

    /// @notice Pause flash-loan execution (emergency circuit-breaker)
    function pause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _pause();
    }

    /// @notice Resume flash-loan execution
    function unpause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _unpause();
    }
}

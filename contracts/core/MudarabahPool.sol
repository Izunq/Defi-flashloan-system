// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "../interfaces/IHalalAssetRegistry.sol";
import "../interfaces/IMudarabahPool.sol";

/// @title MudarabahPool
/// @notice A Sharia-compliant alternative to traditional flash loans using a
///         Mudarabah (profit-sharing partnership) model.
///
///         Capital providers (rab al-mal) deposit tokens into the pool.
///         Authorized traders (mudaribs) borrow from the pool within a single
///         transaction. If the trade is profitable, profit is split according to
///         a configurable ratio (default 70/30 provider/mudarib). If the trade
///         breaks even or loses, NO fee is charged -- the principal must still be
///         returned. This is Sharia-compliant because the fee is profit-sharing
///         on actual economic activity, not a predetermined interest charge.
contract MudarabahPool is IMudarabahPool, AccessControl, ReentrancyGuard, Pausable {
    using SafeERC20 for IERC20;

    // -----------------------------------------------------------------------
    //  Roles
    // -----------------------------------------------------------------------

    bytes32 public constant MUDARIB_ROLE = keccak256("MUDARIB_ROLE");

    // -----------------------------------------------------------------------
    //  Custom errors
    // -----------------------------------------------------------------------

    error InsufficientShares();
    error InsufficientPoolBalance();
    error PrincipalNotReturned();
    error InvalidRatio();
    error TimelockNotExpired();
    error NoRatioChangePending();
    error AssetNotHalalCompliant();
    error ZeroAddress();

    // -----------------------------------------------------------------------
    //  Events
    // -----------------------------------------------------------------------

    event Deposit(
        address indexed provider,
        address indexed token,
        uint256 amount,
        uint256 sharesIssued
    );

    event Withdrawal(
        address indexed provider,
        address indexed token,
        uint256 tokenAmount,
        uint256 sharesBurned
    );

    event ProfitClaimed(
        address indexed provider,
        address indexed token,
        uint256 amount
    );

    event MudarabahExecuted(
        address indexed mudarib,
        address indexed token,
        uint256 amount,
        uint256 profit,
        uint256 providerProfit,
        uint256 mudaribProfit
    );

    event RatioChangeProposed(
        uint256 newProviderBps,
        uint256 newMudaribBps,
        uint256 effectiveAt
    );

    event RatioChangeApplied(
        uint256 providerShareBps,
        uint256 mudaribShareBps
    );

    // -----------------------------------------------------------------------
    //  State -- halal registry
    // -----------------------------------------------------------------------

    IHalalAssetRegistry public halalRegistry;

    // -----------------------------------------------------------------------
    //  State -- profit-sharing ratio (basis points, 10 000 = 100%)
    // -----------------------------------------------------------------------

    uint256 public providerShareBps = 7000; // 70 %
    uint256 public mudaribShareBps  = 3000; // 30 %

    uint256 public constant RATIO_TIMELOCK = 24 hours;

    uint256 public pendingProviderShareBps;
    uint256 public pendingMudaribShareBps;
    uint256 public ratioChangeTimestamp;

    // -----------------------------------------------------------------------
    //  State -- share-based accounting (per token)
    // -----------------------------------------------------------------------

    /// @notice Total shares outstanding for a given token.
    mapping(address => uint256) public totalShares;

    /// @notice Total tokens deposited by providers for a given token.
    mapping(address => uint256) public totalDeposited;

    /// @notice Shares held by each provider for a given token.
    mapping(address => mapping(address => uint256)) public shares;

    /// @notice Accumulated profit per share, scaled by 1e18 (MasterChef pattern).
    mapping(address => uint256) public accProfitPerShare;

    /// @notice Tracks profit already accounted for (debt pattern).
    mapping(address => mapping(address => uint256)) public claimedProfit;

    /// @notice Unclaimed profit buffered during share changes.
    mapping(address => mapping(address => uint256)) public pendingProfit;

    // -----------------------------------------------------------------------
    //  Constructor
    // -----------------------------------------------------------------------

    /// @param _halalRegistry Address of the IHalalAssetRegistry implementation.
    constructor(address _halalRegistry) {
        if (_halalRegistry == address(0)) revert ZeroAddress();

        halalRegistry = IHalalAssetRegistry(_halalRegistry);

        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(MUDARIB_ROLE, msg.sender);
    }

    // -----------------------------------------------------------------------
    //  Provider functions
    // -----------------------------------------------------------------------

    /// @notice Deposit tokens into the pool and receive shares in return.
    /// @param token  The ERC-20 token to deposit.
    /// @param amount The number of tokens to deposit.
    function deposit(address token, uint256 amount) external nonReentrant whenNotPaused {
        if (!halalRegistry.isHalalCompliant(token)) {
            revert AssetNotHalalCompliant();
        }

        // Snapshot pending earnings before changing shares.
        _updatePendingProfit(token, msg.sender);

        // Calculate shares to issue.
        uint256 sharesIssued;
        if (totalShares[token] == 0 || totalDeposited[token] == 0) {
            sharesIssued = amount;
        } else {
            sharesIssued = (amount * totalShares[token]) / totalDeposited[token];
        }

        // Pull tokens from the provider.
        IERC20(token).safeTransferFrom(msg.sender, address(this), amount);

        // Update bookkeeping.
        totalShares[token]          += sharesIssued;
        totalDeposited[token]       += amount;
        shares[token][msg.sender]   += sharesIssued;

        // Re-align the debt so the new shares don't count toward past profit.
        claimedProfit[token][msg.sender] =
            (shares[token][msg.sender] * accProfitPerShare[token]) / 1e18;

        emit Deposit(msg.sender, token, amount, sharesIssued);
    }

    /// @notice Burn shares and withdraw the corresponding tokens.
    /// @param token        The ERC-20 token to withdraw.
    /// @param sharesToBurn The number of shares to redeem.
    function withdraw(address token, uint256 sharesToBurn) external nonReentrant {
        if (sharesToBurn > shares[token][msg.sender]) {
            revert InsufficientShares();
        }

        // Snapshot pending earnings before changing shares.
        _updatePendingProfit(token, msg.sender);

        // Calculate the token amount the shares are worth.
        uint256 tokenAmount =
            (sharesToBurn * totalDeposited[token]) / totalShares[token];

        // Update bookkeeping.
        shares[token][msg.sender]   -= sharesToBurn;
        totalShares[token]          -= sharesToBurn;
        totalDeposited[token]       -= tokenAmount;

        // Re-align the debt after the share change.
        claimedProfit[token][msg.sender] =
            (shares[token][msg.sender] * accProfitPerShare[token]) / 1e18;

        // Transfer tokens back to the provider.
        IERC20(token).safeTransfer(msg.sender, tokenAmount);

        emit Withdrawal(msg.sender, token, tokenAmount, sharesToBurn);
    }

    /// @notice Claim accumulated profit for a given token.
    /// @param token The ERC-20 token whose profit to claim.
    function claimProfit(address token) external nonReentrant {
        uint256 accumulated =
            (shares[token][msg.sender] * accProfitPerShare[token]) / 1e18;
        uint256 pending =
            accumulated
            - claimedProfit[token][msg.sender]
            + pendingProfit[token][msg.sender];

        // Reset buffered profit and re-align the debt.
        pendingProfit[token][msg.sender]  = 0;
        claimedProfit[token][msg.sender]  = accumulated;

        // Transfer profit to the provider.
        IERC20(token).safeTransfer(msg.sender, pending);

        emit ProfitClaimed(msg.sender, token, pending);
    }

    // -----------------------------------------------------------------------
    //  Mudarib (trader) functions
    // -----------------------------------------------------------------------

    /// @notice Execute a Mudarabah: borrow tokens, perform an operation, and
    ///         return at least the principal.  Profit (if any) is split between
    ///         the pool's providers and the mudarib.
    /// @param token  The ERC-20 token to borrow.
    /// @param amount The number of tokens to borrow.
    /// @param data   The calldata to execute on the mudarib's contract.
    function executeMudarabah(
        address token,
        uint256 amount,
        bytes calldata data
    )
        external
        onlyRole(MUDARIB_ROLE)
        whenNotPaused
        nonReentrant
    {
        if (!halalRegistry.isHalalCompliant(token)) {
            revert AssetNotHalalCompliant();
        }
        if (amount > IERC20(token).balanceOf(address(this))) {
            revert InsufficientPoolBalance();
        }

        uint256 balanceBefore = IERC20(token).balanceOf(address(this));

        // Lend tokens to the mudarib.
        IERC20(token).safeTransfer(msg.sender, amount);

        // The mudarib executes their strategy.
        (bool success, ) = msg.sender.call(data);
        require(success, "MudarabahPool: mudarib call failed");

        uint256 balanceAfter = IERC20(token).balanceOf(address(this));

        // The principal must be fully returned.
        if (balanceAfter < balanceBefore) {
            revert PrincipalNotReturned();
        }

        uint256 profit         = balanceAfter - balanceBefore;
        uint256 providerProfit = 0;
        uint256 mudaribProfit  = 0;

        if (profit > 0) {
            providerProfit = (profit * providerShareBps) / 10_000;
            mudaribProfit  = profit - providerProfit;

            // Distribute provider share across all share-holders.
            accProfitPerShare[token] +=
                (providerProfit * 1e18) / totalShares[token];

            // Provider profit accrues to the pool's deposited base.
            totalDeposited[token] += providerProfit;

            // Send the mudarib their share.
            IERC20(token).safeTransfer(msg.sender, mudaribProfit);
        }

        emit MudarabahExecuted(
            msg.sender,
            token,
            amount,
            profit,
            providerProfit,
            mudaribProfit
        );
    }

    // -----------------------------------------------------------------------
    //  Admin functions -- ratio governance
    // -----------------------------------------------------------------------

    /// @notice Propose a new profit-sharing ratio.  Subject to a 24-hour
    ///         timelock before it can be applied.
    /// @param newProviderBps New provider share in basis points.
    /// @param newMudaribBps  New mudarib share in basis points.
    function proposeRatioChange(
        uint256 newProviderBps,
        uint256 newMudaribBps
    )
        external
        onlyRole(DEFAULT_ADMIN_ROLE)
    {
        if (newProviderBps + newMudaribBps != 10_000) {
            revert InvalidRatio();
        }

        pendingProviderShareBps = newProviderBps;
        pendingMudaribShareBps  = newMudaribBps;
        ratioChangeTimestamp    = block.timestamp + RATIO_TIMELOCK;

        emit RatioChangeProposed(
            newProviderBps,
            newMudaribBps,
            ratioChangeTimestamp
        );
    }

    /// @notice Apply a previously proposed ratio change once the timelock has
    ///         expired.  Callable by anyone.
    function applyRatioChange() external {
        if (ratioChangeTimestamp == 0) {
            revert NoRatioChangePending();
        }
        if (block.timestamp < ratioChangeTimestamp) {
            revert TimelockNotExpired();
        }

        providerShareBps = pendingProviderShareBps;
        mudaribShareBps  = pendingMudaribShareBps;

        // Reset pending state.
        pendingProviderShareBps = 0;
        pendingMudaribShareBps  = 0;
        ratioChangeTimestamp    = 0;

        emit RatioChangeApplied(providerShareBps, mudaribShareBps);
    }

    // -----------------------------------------------------------------------
    //  Admin functions -- misc
    // -----------------------------------------------------------------------

    /// @notice Update the halal asset registry address.
    /// @param _registry The new registry address.
    function setHalalRegistry(address _registry)
        external
        onlyRole(DEFAULT_ADMIN_ROLE)
    {
        if (_registry == address(0)) revert ZeroAddress();
        halalRegistry = IHalalAssetRegistry(_registry);
    }

    /// @notice Pause all deposits and Mudarabah executions.
    function pause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _pause();
    }

    /// @notice Unpause the contract.
    function unpause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _unpause();
    }

    // -----------------------------------------------------------------------
    //  Interface view functions
    // -----------------------------------------------------------------------

    /// @notice Get the total pool balance for a given token.
    function getPoolBalance(address token) external view returns (uint256) {
        return IERC20(token).balanceOf(address(this));
    }

    /// @notice Get the share balance for a specific capital provider.
    function getShareBalance(address token, address provider) external view returns (uint256) {
        return shares[token][provider];
    }

    /// @notice Get the profit-sharing ratio.
    function getProfitRatio() external view returns (uint256 providerShare, uint256 mudaribShare) {
        return (providerShareBps, mudaribShareBps);
    }

    // -----------------------------------------------------------------------
    //  Internal helpers
    // -----------------------------------------------------------------------

    /// @dev Snapshot a provider's unclaimed earnings into `pendingProfit`
    ///      before their share balance changes.  This ensures that earnings
    ///      accrued up to this point are not lost or diluted.
    /// @param token    The token to snapshot.
    /// @param provider The provider whose profit to snapshot.
    function _updatePendingProfit(address token, address provider) internal {
        if (shares[token][provider] > 0) {
            uint256 accumulated =
                (shares[token][provider] * accProfitPerShare[token]) / 1e18;
            pendingProfit[token][provider] +=
                accumulated - claimedProfit[token][provider];
        }
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title IAavePool
 * @notice Interface for Aave V3 Pool
 * @dev Simplified interface for flash loan functionality
 */
interface IAavePool {
    /**
     * @dev Allows smart contracts to access the liquidity of the pool within one transaction,
     * as long as the amount taken plus a fee is returned.
     * @param receiverAddress The address of the contract receiving the funds, implementing IFlashLoanSimpleReceiver interface
     * @param asset The address of the asset being flash-borrowed
     * @param amount The amount of the asset being flash-borrowed
     * @param params Encoded parameters to pass to the receiver contract
     * @param referralCode Referral code for the referral program
     */
    function flashLoanSimple(
        address receiverAddress,
        address asset,
        uint256 amount,
        bytes calldata params,
        uint16 referralCode
    ) external;
    
    /**
     * @dev Allows smart contracts to access the liquidity of the pool within one transaction,
     * as long as the amount taken plus a fee is returned.
     * @param receiverAddress The address of the contract receiving the funds, implementing IFlashLoanReceiver interface
     * @param assets The addresses of the assets being flash-borrowed
     * @param amounts The amounts of the assets being flash-borrowed
     * @param modes Types of debt to open if the flash loan is not returned (0 = no debt, 1 = stable, 2 = variable)
     * @param onBehalfOf Address of the user who will receive the debt in case of using on behalf of mode
     * @param params Encoded parameters to pass to the receiver contract
     * @param referralCode Referral code for the referral program
     */
    function flashLoan(
        address receiverAddress,
        address[] calldata assets,
        uint256[] calldata amounts,
        uint256[] calldata modes,
        address onBehalfOf,
        bytes calldata params,
        uint16 referralCode
    ) external;
    
    /**
     * @dev Returns the fee on flash loans
     * @return The flash loan fee
     */
    function FLASHLOAN_PREMIUM_TOTAL() external view returns (uint128);
    
    /**
     * @dev Returns the fee to protocol on flash loans
     * @return The flash loan protocol fee
     */
    function FLASHLOAN_PREMIUM_TO_PROTOCOL() external view returns (uint128);
}
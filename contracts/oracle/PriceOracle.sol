// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";

/// @notice Minimal Chainlink AggregatorV3 interface (defined inline to avoid
///         an external dependency on the Chainlink contracts package).
interface AggregatorV3Interface {
    function latestRoundData()
        external
        view
        returns (
            uint80 roundId,
            int256 answer,
            uint256 startedAt,
            uint256 updatedAt,
            uint80 answeredInRound
        );

    function decimals() external view returns (uint8);
}

/// @title PriceOracle — Multi-source Chainlink price oracle with manipulation resistance
/// @notice Aggregates prices from multiple Chainlink feeds per asset pair,
///         filters stale data, computes the median, and reverts when the spread
///         between the highest and lowest valid prices exceeds a configurable
///         deviation threshold.  Designed for use on Arbitrum One where multiple
///         Chainlink feeds may be available for the same underlying pair.
contract PriceOracle is AccessControl {
    // ─── Roles ───────────────────────────────────────────────────────────
    bytes32 public constant ORACLE_MANAGER_ROLE =
        keccak256("ORACLE_MANAGER_ROLE");

    // ─── Constants (defaults) ────────────────────────────────────────────
    uint256 private constant DEFAULT_STALENESS_THRESHOLD = 3600; // 1 hour
    uint256 private constant DEFAULT_MAX_DEVIATION = 500; // 5 % in bps
    uint256 private constant BPS_DENOMINATOR = 10_000;

    // ─── State ───────────────────────────────────────────────────────────
    /// @dev pairId = keccak256(abi.encodePacked(base, quote))
    mapping(bytes32 => address[]) private _feeds;
    mapping(bytes32 => uint256) private _stalenessThreshold;
    mapping(bytes32 => uint256) private _maxDeviation;

    // ─── Events ──────────────────────────────────────────────────────────
    event FeedAdded(
        address indexed base,
        address indexed quote,
        address feed
    );
    event FeedRemoved(
        address indexed base,
        address indexed quote,
        address feed
    );
    event StalenessThresholdUpdated(
        address indexed base,
        address indexed quote,
        uint256 threshold
    );
    event MaxDeviationUpdated(
        address indexed base,
        address indexed quote,
        uint256 deviation
    );

    // ─── Custom errors ───────────────────────────────────────────────────
    error NoPriceAvailable();
    error PriceDeviationTooHigh(uint256 deviation, uint256 maxAllowed);
    error InvalidFeed(address feed);

    // ─── Constructor ─────────────────────────────────────────────────────
    constructor() {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ORACLE_MANAGER_ROLE, msg.sender);
    }

    // ─── Feed management ─────────────────────────────────────────────────

    /// @notice Register a Chainlink feed for an asset pair
    function addFeed(
        address base,
        address quote,
        address feed
    ) external onlyRole(ORACLE_MANAGER_ROLE) {
        if (feed == address(0)) revert InvalidFeed(feed);

        bytes32 pairId = _pairId(base, quote);
        _feeds[pairId].push(feed);

        // Initialise thresholds on first feed
        if (_stalenessThreshold[pairId] == 0) {
            _stalenessThreshold[pairId] = DEFAULT_STALENESS_THRESHOLD;
        }
        if (_maxDeviation[pairId] == 0) {
            _maxDeviation[pairId] = DEFAULT_MAX_DEVIATION;
        }

        emit FeedAdded(base, quote, feed);
    }

    /// @notice Remove a Chainlink feed for an asset pair
    function removeFeed(
        address base,
        address quote,
        address feed
    ) external onlyRole(ORACLE_MANAGER_ROLE) {
        bytes32 pairId = _pairId(base, quote);
        address[] storage feeds = _feeds[pairId];

        uint256 len = feeds.length;
        for (uint256 i = 0; i < len; i++) {
            if (feeds[i] == feed) {
                // Swap-and-pop removal
                feeds[i] = feeds[len - 1];
                feeds.pop();
                emit FeedRemoved(base, quote, feed);
                return;
            }
        }
        revert InvalidFeed(feed);
    }

    /// @notice Set the staleness window (seconds) after which a price is ignored
    function setStalenessThreshold(
        address base,
        address quote,
        uint256 threshold
    ) external onlyRole(ORACLE_MANAGER_ROLE) {
        bytes32 pairId = _pairId(base, quote);
        _stalenessThreshold[pairId] = threshold;
        emit StalenessThresholdUpdated(base, quote, threshold);
    }

    /// @notice Set the maximum allowed deviation between feeds (basis points)
    function setMaxDeviation(
        address base,
        address quote,
        uint256 deviation
    ) external onlyRole(ORACLE_MANAGER_ROLE) {
        bytes32 pairId = _pairId(base, quote);
        _maxDeviation[pairId] = deviation;
        emit MaxDeviationUpdated(base, quote, deviation);
    }

    // ─── Price query ─────────────────────────────────────────────────────

    /// @notice Fetch the manipulation-resistant median price for an asset pair
    /// @param base  The base token address
    /// @param quote The quote token address
    /// @return price    The median price across all valid feeds
    /// @return decimals The number of decimals in the returned price (from the
    ///                  first valid feed)
    function getPrice(
        address base,
        address quote
    ) external view returns (uint256 price, uint8 decimals) {
        bytes32 pairId = _pairId(base, quote);
        address[] storage feeds = _feeds[pairId];
        uint256 staleness = _stalenessThreshold[pairId];
        if (staleness == 0) staleness = DEFAULT_STALENESS_THRESHOLD;

        uint256 len = feeds.length;
        // Temporary arrays (upper-bounded by feed count)
        uint256[] memory validPrices = new uint256[](len);
        uint8 firstDecimals;
        uint256 validCount;

        for (uint256 i = 0; i < len; i++) {
            try AggregatorV3Interface(feeds[i]).latestRoundData() returns (
                uint80,
                int256 answer,
                uint256,
                uint256 updatedAt,
                uint80
            ) {
                // Skip negative or zero answers
                if (answer <= 0) continue;
                // Skip stale data
                if (updatedAt + staleness < block.timestamp) continue;

                if (validCount == 0) {
                    firstDecimals = AggregatorV3Interface(feeds[i]).decimals();
                }
                validPrices[validCount] = uint256(answer);
                validCount++;
            } catch {
                // Feed reverted — skip silently
                continue;
            }
        }

        if (validCount == 0) revert NoPriceAvailable();

        // Trim the array to valid entries
        uint256[] memory trimmed = new uint256[](validCount);
        for (uint256 i = 0; i < validCount; i++) {
            trimmed[i] = validPrices[i];
        }

        // Sort and compute median
        _sort(trimmed);
        uint256 medianPrice = _median(trimmed);

        // Deviation check (only meaningful when >1 valid price)
        if (validCount > 1) {
            uint256 minPrice = trimmed[0];
            uint256 maxPrice = trimmed[validCount - 1];
            uint256 maxDev = _maxDeviation[pairId];
            if (maxDev == 0) maxDev = DEFAULT_MAX_DEVIATION;

            // deviation = (maxPrice - minPrice) * BPS_DENOMINATOR / minPrice
            uint256 deviation = ((maxPrice - minPrice) * BPS_DENOMINATOR) /
                minPrice;
            if (deviation > maxDev) {
                revert PriceDeviationTooHigh(deviation, maxDev);
            }
        }

        return (medianPrice, firstDecimals);
    }

    // ─── Internal helpers ────────────────────────────────────────────────

    /// @dev Deterministic pair identifier
    function _pairId(
        address base,
        address quote
    ) internal pure returns (bytes32) {
        return keccak256(abi.encodePacked(base, quote));
    }

    /// @dev In-place insertion sort (fine for small arrays typical of oracle feeds)
    function _sort(uint256[] memory arr) internal pure {
        uint256 len = arr.length;
        for (uint256 i = 1; i < len; i++) {
            uint256 key = arr[i];
            uint256 j = i;
            while (j > 0 && arr[j - 1] > key) {
                arr[j] = arr[j - 1];
                j--;
            }
            arr[j] = key;
        }
    }

    /// @dev Return the median of a **sorted** array
    function _median(uint256[] memory arr) internal pure returns (uint256) {
        uint256 len = arr.length;
        if (len % 2 == 1) {
            return arr[len / 2];
        } else {
            return (arr[len / 2 - 1] + arr[len / 2]) / 2;
        }
    }
}

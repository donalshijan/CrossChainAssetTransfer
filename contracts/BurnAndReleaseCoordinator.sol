// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/AccessControl.sol";


interface IBurnTokensEscrow {
    function escrowTokens(uint256 _amount, address fromUserAddressOnBinanceChain) external;
    function returnTokens(address _userAddress, uint256 _amount) external;
    function burnTokens(address _userAddress, uint256 _amount) external;
}

contract BurnAndReleaseCoordinator is AccessControl {
    IBurnTokensEscrow public burnTokensEscrow;

    bytes32 public constant OWNER_ROLE = keccak256("OWNER_ROLE");


    event BurnInitiated(address tokenAddress,address indexed fromUserAddressOnBinanceChain, uint256 amount, address indexed toUserAddressOnEthereumChain);
    event TransferCompleted(address fromUserAddressOnBinanceChain,address  toUserAddressOnEthereumChain, uint256 amount,address tokenAddress);
    event ReleaseFailed(address indexed fromUserAddressOnBinanceChain, uint256 amount);
    event ReturnedTokens(address toUserAddressOnBinanceChain, uint256 amount);

    constructor(address _bep20MintableAddress, address _burnTokensEscrowAddress) {
        burnTokensEscrow = IBurnTokensEscrow(_burnTokensEscrowAddress);

        // Set up the roles
        _setupRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _setupRole(OWNER_ROLE, msg.sender);
    }

    function initateBurnAndRelease(address tokenAddress, address _fromUserAddressOnBinanceChain, uint256 _amount, address _toUserAddressOnEthereumChain) external onlyRole(OWNER_ROLE) {
        // Escrow the tokens before starting the burn process
        try burnTokensEscrow.escrowTokens(_amount, _fromUserAddressOnBinanceChain) {
            // If successful, emit the BurnInitiated event
            emit BurnInitiated(tokenAddress,_fromUserAddressOnBinanceChain, _amount, _toUserAddressOnEthereumChain);
        } catch {
            // If escrowTokens fails, emit BurnFailed event and revert transaction
            emit ReleaseFailed(_fromUserAddressOnBinanceChain, _amount);
            revert("Escrow failed. Burn operation aborted.");
        }
    }

    function releaseCompleted(address _tokenAddress, address _userAddressOnEthereumChain, uint256 _amount, address _fromUserAddressOnBinanceChain) external onlyRole(OWNER_ROLE) {
        // Attempt to burn the escrowed tokens
        try burnTokensEscrow.burnTokens(_fromUserAddressOnBinanceChain, _amount) {
            // If successful, emit the ReleaseCompleted event
            emit TransferCompleted(_fromUserAddressOnBinanceChain,_userAddressOnEthereumChain, _amount,_tokenAddress);
        } catch {
            // If burnTokens fails, revert the transaction
            revert("Burning tokens failed. ReleaseCompleted event not emitted.");
        }
    }

    function releaseFailed(address _tokenAddress, address _userAddressOnEthereumChain, uint256 _amount, address _fromUserAddressOnBinanceChain) external onlyRole(OWNER_ROLE) {
        // Attempt to return the tokens to the user
        try burnTokensEscrow.returnTokens(_fromUserAddressOnBinanceChain, _amount) {
            // If successful, emit the ReleaseFailed event
            emit ReturnedTokens(_fromUserAddressOnBinanceChain, _amount);
        } catch {
            // If returnTokens fails, revert the transaction
            revert("Returning tokens failed. ReleaseFailed event not emitted.");
        }
    }


    function addOwner(address newOwner) external onlyRole(DEFAULT_ADMIN_ROLE) {
        grantRole(OWNER_ROLE, newOwner);
    }

    function removeOwner(address owner) external onlyRole(DEFAULT_ADMIN_ROLE) {
        revokeRole(OWNER_ROLE, owner);
    }
}

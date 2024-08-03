// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/AccessControl.sol";

interface IBEP20Mintable {
    function burn(address _fromUserAddressOnBinanceChain, uint256 _amount, address _toUserAddressOnEthereumChain) external;
}

interface IBurnTokensEscrow {
    function escrowTokens(uint256 _amount, address fromUserAddressOnBinanceChain) external;
    function returnTokens(address _userAddress, uint256 _amount) external;
    function burnTokens(address _userAddress, uint256 _amount) external;
}

contract BurnAndReleaseCoordinator is AccessControl {
    IBEP20Mintable public bep20Mintable;
    IBurnTokensEscrow public burnTokensEscrow;

    bytes32 public constant OWNER_ROLE = keccak256("OWNER_ROLE");

    uint256 public coordinatorFee; // Fee amount for coordinator's operations

    event BurnInitiated(address tokenAddress,address indexed fromUserAddressOnBinanceChain, uint256 amount, address indexed toUserAddressOnEthereumChain);
    event TransferCompleted(address fromUserAddressOnBinanceChain,address  toUserAddressOnEthereumChain, uint256 amount,address tokenAddress);
    event ReleaseFailed(address indexed fromUserAddressOnBinanceChain, uint256 amount);
    event ReturnedTokens(address toUserAddressOnBinanceChain, uint256 amount);
    event CoordinatorFeePaid(address indexed payer, uint256 amount);

    constructor(address _bep20MintableAddress, address _burnTokensEscrowAddress, uint256 _coordinatorFee) {
        bep20Mintable = IBEP20Mintable(_bep20MintableAddress);
        burnTokensEscrow = IBurnTokensEscrow(_burnTokensEscrowAddress);
        coordinatorFee = _coordinatorFee;

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

    function payCoordinatorFee() external payable {
        require(msg.value >= coordinatorFee, "Insufficient fee paid");
        // Refund excess fee
        if (msg.value > coordinatorFee) {
            payable(msg.sender).transfer(msg.value - coordinatorFee);
        }
        emit CoordinatorFeePaid(msg.sender, msg.value);
    }

    function withdrawFees() external onlyRole(DEFAULT_ADMIN_ROLE) {
        uint256 balance = address(this).balance;
        require(balance > 0, "No fees to withdraw");
        payable(owner()).transfer(balance);
    }

    function setCoordinatorFee(uint256 _coordinatorFee) external onlyRole(DEFAULT_ADMIN_ROLE) {
        coordinatorFee = _coordinatorFee;
    }

    function addOwner(address newOwner) external onlyRole(DEFAULT_ADMIN_ROLE) {
        grantRole(OWNER_ROLE, newOwner);
    }

    function removeOwner(address owner) external onlyRole(DEFAULT_ADMIN_ROLE) {
        revokeRole(OWNER_ROLE, owner);
    }
}

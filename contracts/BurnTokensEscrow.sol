// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract BurnTokensEscrow is Ownable {
    IERC20 public bep20Token;
    uint256 public escrowFee;
    mapping(address => uint256) public escrowBalances;
    address private constant BURN_ADDRESS = 0x0000000000000000000000000000000000000000; // or a dedicated burn address

    event EscrowFeePaid(address indexed payer, uint256 amount);

    constructor(address _bep20TokenAddress, uint256 _escrowFee) {
        bep20Token = IERC20(_bep20TokenAddress);
        escrowFee = _escrowFee;
    }
    function payEscrowCostFee() external payable {
        require(msg.value >= escrowFee, "Insufficient fee paid");
        // Refund excess fee
        if (msg.value > escrowFee) {
            payable(msg.sender).transfer(msg.value - escrowFee);
        }
        emit EscrowFeePaid(msg.sender, msg.value);
    }

    function escrowTokens(uint256 _amount,fromUserAddressOnBinanceChain) external onlyOwner{
        require(bep20Token.transferFrom(fromUserAddressOnBinanceChain, address(this), _amount), "Transfer failed");
        escrowBalances[fromUserAddressOnBinanceChain] += _amount;
    }

    function returnTokens(address _userAddressOnBinanceChain, uint256 _amount) external onlyOwner {
        require(escrowBalances[_userAddressOnBinanceChain] >= _amount, "Insufficient balance in escrow");
        escrowBalances[_userAddressOnBinanceChain] -= _amount;
        require(bep20Token.transfer(_userAddressOnBinanceChain, _amount), "Transfer failed");
    }

    function burnTokens(address _userAddress, uint256 _amount) external onlyOwner {
        require(escrowBalances[_userAddress] >= _amount, "Insufficient balance in escrow");
        escrowBalances[_userAddress] -= _amount;
        require(bep20Token.transfer(BURN_ADDRESS, _amount), "Burn transfer failed");
    }

    function setEscrowFee(uint256 _escrowFee) external onlyOwner {
        escrowFee = _escrowFee;
    }

    function withdrawFees() external onlyOwner {
        payable(owner()).transfer(address(this).balance);
    }
}

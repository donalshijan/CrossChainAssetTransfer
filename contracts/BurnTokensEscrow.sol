// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract BurnTokensEscrow is Ownable {
    IERC20 public bep20Token;
    mapping(address => uint256) public escrowBalances;
    address private constant BURN_ADDRESS = 0x0000000000000000000000000000000000000000; // or a dedicated burn address
    

    constructor() Ownable(msg.sender){
    }

    function escrowTokens(uint256 _amount,address fromUserAddressOnBinanceChain) external onlyOwner{
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
     function setBEP20TokenContractAddress(address _bep20TokenAddress) external onlyOwner {
        bep20Token = IERC20(_bep20TokenAddress);
    }

    // Function to destroy the contract and send remaining funds to the owner
    function destroyContract() external onlyOwner {
        selfdestruct(payable(owner()));
    }
}

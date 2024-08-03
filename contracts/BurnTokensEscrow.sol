// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract BurnTokensEscrow is Ownable {
    IERC20 public bep20Token;

    mapping(address => uint256) public escrowBalances;
    address private constant BURN_ADDRESS = 0x0000000000000000000000000000000000000000; // or a dedicated burn address
    event TokensEscrowed(address indexed fromUserAddressOnBinanceChain, uint256 amount);
    event TokensReturned(address indexed fromUserAddressOnBinanceChain, uint256 amount);
    event TokensBurned(address indexed fromUserAddressOnBinanceChain, uint256 amount);

    constructor(address _bep20TokenAddress) {
        bep20Token = IERC20(_bep20TokenAddress);
    }

    function escrowTokens(uint256 _amount,fromUserAddressOnBinanceChain) external onlyOwner{
        require(bep20Token.transferFrom(fromUserAddressOnBinanceChain, address(this), _amount), "Transfer failed");
        escrowBalances[fromUserAddressOnBinanceChain] += _amount;
        emit TokensEscrowed(fromUserAddressOnBinanceChain, _amount);
    }

    function returnTokens(address _userAddressOnBinanceChain, uint256 _amount) external onlyOwner {
        require(escrowBalances[_userAddressOnBinanceChain] >= _amount, "Insufficient balance in escrow");
        escrowBalances[_userAddressOnBinanceChain] -= _amount;
        require(bep20Token.transfer(_userAddressOnBinanceChain, _amount), "Transfer failed");
        emit TokensReturned(_userAddressOnBinanceChain, _amount);
    }

    function burnTokens(address _userAddress, uint256 _amount) external onlyOwner {
        require(escrowBalances[_userAddress] >= _amount, "Insufficient balance in escrow");
        escrowBalances[_userAddress] -= _amount;
        require(bep20Token.transfer(BURN_ADDRESS, _amount), "Burn transfer failed");
        emit TokensBurned(_userAddress, _amount);
    }
}

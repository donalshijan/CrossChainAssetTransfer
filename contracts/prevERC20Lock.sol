// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract ERC20Lock is Ownable {
    IERC20 public token;
    mapping(address => uint256) public lockedBalances;

    event TokensLocked(address indexed fromUserAddressOnEthereumChain, uint256 amount,address toUserAddressOnBinanceChain);
    event TokensReleased(address indexed toUserAddressOnEthereumChain, uint256 amount,address fromUserAddressOnBinanceChain);

    constructor(IERC20 _token) {
        token = _token;
    }

    function lockTokens(uint256 _amount,address _toUserAddressOnBinanceChain) external {
        require(_amount > 0, "Amount must be greater than zero");
        require(token.transferFrom(msg.sender, address(this), _amount), "Token transfer failed");

        lockedBalances[msg.sender] += _amount;

        emit TokensLocked(msg.sender, _amount, _toUserAddressOnBinanceChain);
    }

    function releaseTokens(address _userAddressOnEthereumChain, uint256 _amount,address _fromUserAddressOnBinanceChain) external onlyOwner {
        require(lockedBalances[_userAddressOnEthereumChain] >= _amount, "Insufficient locked balance");
        lockedBalances[_userAddressOnEthereumChain] -= _amount;

        require(token.transfer(_userAddressOnEthereumChain, _amount), "Token transfer failed");

        emit TokensReleased(_userAddressOnEthereumChain, _amount,_fromUserAddressOnBinanceChain);
    }
}

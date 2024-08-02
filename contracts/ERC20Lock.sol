// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract ERC20Lock is Ownable {
    // Mapping to handle multiple ERC20 tokens
    mapping(address => IERC20) public tokenByAddress;
    mapping(address => mapping(address => uint256)) public lockedBalances;

    event TokensLocked(address indexed fromUserAddressOnEthereumChain, address indexed tokenAddress, uint256 amount, address toUserAddressOnBinanceChain);
    event TokensReleased(address indexed toUserAddressOnEthereumChain, address indexed tokenAddress, uint256 amount, address fromUserAddressOnBinanceChain);

    constructor(address[] memory _tokens) {
        for (uint i = 0; i < _tokens.length; i++) {
            tokenByAddress[_tokens[i]] = IERC20(_tokens[i]);
        }
    }

    function addToken(address tokenAddress) external onlyOwner {
        tokens[tokenAddress] = IERC20(tokenAddress);
    }

    function lockTokens(address _tokenAddress, uint256 _amount, address _toUserAddressOnBinanceChain) external {
        IERC20 token = tokenByAddress[_tokenAddress];
        require(address(token) != address(0), "Token not supported");
        require(_amount > 0, "Amount must be greater than zero");
        require(token.transferFrom(msg.sender, address(this), _amount), "Token transfer failed");

        lockedBalances[_tokenAddress][msg.sender] += _amount;

        emit TokensLocked(msg.sender, _tokenAddress, _amount, _toUserAddressOnBinanceChain);
    }

    function releaseTokens(address _tokenAddress, address _userAddressOnEthereumChain, uint256 _amount, address _fromUserAddressOnBinanceChain) external onlyOwner {
        IERC20 token = tokenByAddress[_tokenAddress];
        require(address(token) != address(0), "Token not supported");
        require(lockedBalances[_tokenAddress][_userAddressOnEthereumChain] >= _amount, "Insufficient locked balance");
        lockedBalances[_tokenAddress][_userAddressOnEthereumChain] -= _amount;

        require(token.transfer(_userAddressOnEthereumChain, _amount), "Token transfer failed");

        emit TokensReleased(_userAddressOnEthereumChain, _tokenAddress, _amount, _fromUserAddressOnBinanceChain);
    }
}

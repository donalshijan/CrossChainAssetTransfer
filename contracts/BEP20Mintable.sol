// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract BEP20Mintable is ERC20, Ownable {
    constructor(string memory name, string memory symbol) ERC20(name, symbol) {}

    event TokensBurned(address indexed fromUserAddressOnBinanceChain, uint256 amount, address  toUserAddressOnEthereumChain);
    event TokensMinted(address indexed toUserAddressOnBinanceChain, uint256 amount, address fromUserAddresOnEthereumChain );

    function mint(address _toUserAddressOnBinanceChain, uint256 _amount, address _fromUserAddressOnEthereumChain) external onlyOwner {
        _mint(_toUserAddressOnBinanceChain, _amount);
        emit TokensMinted(_toUserAddressOnBinanceChain, amount, _fromUserAddressOnEthereumChain);
    }

    function burn(address _fromUserAddressOnBinanceChain, uint256 _amount, address _toUserAddressOnEthereumChain) external  {
        require(balanceOf(_fromUserAddressOnBinanceChain) >= _amount, "Insufficient balance to burn");
        _burn(_fromUserAddressOnBinanceChain, _amount);
        emit TokensBurned(_from, _amount, _toUserAddressOnEthereumChain);
    }
}

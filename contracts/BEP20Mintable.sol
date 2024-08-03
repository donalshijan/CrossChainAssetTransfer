// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";



contract BEP20Mintable is ERC20, Ownable {
    uint256 public mintFee; // Fee required to mint tokens
    mapping(address => uint256) public mintFeesCollected; // Mapping to track fees paid by each user
    address public burnEscrowTokenContractAddress;

    constructor(string memory name, string memory symbol, uint256 _mintFee,address _burnTokensEscrowAddress) ERC20(name, symbol) {
        mintFee = _mintFee;
        burnEscrowTokenContractAddress = _burnTokensEscrowAddress;
    }

    event TokensTransferInitiated(address indexed fromUserAddressOnBinanceChain, uint256 amount, address toUserAddressOnEthereumChain,address tokenAddress);
    event TokensMinted(address indexed toUserAddressOnBinanceChain, uint256 amount, address fromUserAddresOnEthereumChain);
    event MintFeePaid(address indexed user, uint256 amount);
    
    // Function for users to pay mint fee
    function payMintFee() external payable {
        require(msg.value >= mintFee, "Insufficient fee paid");
        mintFeesCollected[msg.sender] += msg.value;
        emit MintFeePaid(msg.sender, msg.value);
    }

    function mint(address _toUserAddressOnBinanceChain, uint256 _amount, address _fromUserAddressOnEthereumChain) external onlyOwner {
        require(mintFeesCollected[_toUserAddressOnBinanceChain] >= mintFee, "Mint fee not paid or insufficient");
        
        _mint(_toUserAddressOnBinanceChain, _amount);
        mintFeesCollected[_toUserAddressOnBinanceChain] -= mintFee; // Deduct the fee after successful minting
        emit TokensMinted(_toUserAddressOnBinanceChain, _amount, _fromUserAddressOnEthereumChain);
    }

    function burn(address _fromUserAddressOnBinanceChain, uint256 _amount, address _toUserAddressOnEthereumChain,address tokenAddress) external {
        require(balanceOf(_fromUserAddressOnBinanceChain) >= _amount, "Insufficient balance to burn");
        // Check if the contract has been approved to transfer tokens on behalf of the user
        uint256 allowance = bep20Token.allowance(_fromUserAddressOnBinanceChain, burnEscrowTokenContractAddress);
        require(allowance >= _amount, "Insufficient allowance to transfer tokens");
        emit TokensTransferInitiated(_fromUserAddressOnBinanceChain, _amount, _toUserAddressOnEthereumChain,tokenAddress);
    }

    // Function to set the mint fee, only callable by the owner
    function setMintFee(uint256 _mintFee) external onlyOwner {
        mintFee = _mintFee;
    }

    // Function to withdraw collected fees
    function withdrawFees() external onlyOwner {
        payable(owner()).transfer(address(this).balance);
    }
}

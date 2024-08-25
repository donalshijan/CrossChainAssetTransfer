// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract ERC20Lock is Ownable {
    // Mapping to handle multiple ERC20 tokens
    mapping(address => IERC20) public tokenByAddress;
    mapping(address => mapping(address => uint256)) public lockedBalances;
    mapping(address => mapping(uint256 => bool)) private usedReceipts;
    // Fee structure
    uint256 public releaseFee; // Fee required to release tokens
    address private bscContractOwner;
    mapping(address => uint256) public releaseFeesCollected; // Mapping to track fees paid by each user
    mapping(address => uint256) private nonces;
    event TokensLocked(address indexed fromUserAddressOnEthereumChain, address indexed tokenAddress, uint256 amount, address toUserAddressOnBinanceChain);
    event TokensReleased(address indexed toUserAddressOnEthereumChain, address indexed tokenAddress, uint256 amount, address fromUserAddressOnBinanceChain);
    event TokenReleaseFailed(address indexed toUserAddressOnEthereumChain, address indexed tokenAddress, uint256 amount, address fromUserAddressOnBinanceChain);
    event ReleaseFeePaid(address indexed payer, uint256 releaseFeeAmount,uint256 nonce,address contractAddress, uint256 userTimestamp, bytes32 receiptMessage );

    constructor(address[] memory _tokens, uint256 _releaseFee,address _bscContractOwner) {
        for (uint i = 0; i < _tokens.length; i++) {
            tokenByAddress[_tokens[i]] = IERC20(_tokens[i]);
        }
        releaseFee = _releaseFee;
        bscContractOwner=_bscContractOwner;
    }

    function addToken(address tokenAddress) external onlyOwner {
        tokenByAddress[tokenAddress] = IERC20(tokenAddress);
    }

    function lockTokens(address _tokenAddress, uint256 _amount, address _toUserAddressOnBinanceChain,uint256 mintFeeAmount,uint256 nonce, address contractAddress,bytes memory receipt) external {

        // Check that the receipt has not been used before
        require(!usedReceipts[msg.sender][nonce], "Receipt already used");
        // Ensure the signer is the owner of the BSC contract (or another authorized address)
        require(verifyReceipt(_toUserAddressOnBinanceChain, mintFeeAmount, nonce,contractAddress, receipt), "Invalid receipt");
        // Mark the receipt as used
        usedReceipts[msg.sender][nonce] = true;
        IERC20 token = tokenByAddress[_tokenAddress];
        require(address(token) != address(0), "Token not supported");
        require(_amount > 0, "Amount must be greater than zero");
        require(token.transferFrom(msg.sender, address(this), _amount), "Token transfer failed");

        lockedBalances[_tokenAddress][msg.sender] += _amount;

        emit TokensLocked(msg.sender, _tokenAddress, _amount, _toUserAddressOnBinanceChain);
    }

    function releaseTokens(address _tokenAddress, address _userAddressOnEthereumChain, uint256 _amount, address _fromUserAddressOnBinanceChain) external onlyOwner {
        require(releaseFeesCollected[msg.sender] >= releaseFee, "Release fee not paid or insufficient");

        IERC20 token = tokenByAddress[_tokenAddress];
        require(address(token) != address(0), "Token not supported");
        require(lockedBalances[_tokenAddress][_userAddressOnEthereumChain] >= _amount, "Insufficient locked balance");
        lockedBalances[_tokenAddress][_userAddressOnEthereumChain] -= _amount;

        bool success = token.transfer(_userAddressOnEthereumChain, _amount);
        if (!success) {
            emit TokenReleaseFailed(_userAddressOnEthereumChain, _tokenAddress, _amount, _fromUserAddressOnBinanceChain);
            revert("Token transfer failed");
        }

        emit TokensReleased(_userAddressOnEthereumChain, _tokenAddress, _amount, _fromUserAddressOnBinanceChain);
    }

    function payReleaseFee(uint256 userTimestamp) external payable {
        require(msg.value >= releaseFee, "Insufficient fee paid");
        releaseFeesCollected[msg.sender] += msg.value;
               // Increment the nonce for the user
        uint256 nonce = nonces[msg.sender]++;

        // Generate a receipt message including the nonce (but not the user-provided timestamp)
        bytes32 receiptMessage = keccak256(abi.encodePacked(msg.sender, msg.value, nonce, address(this)));

        // Emit the event with the user-provided timestamp
        emit ReleaseFeePaid(msg.sender, msg.value, nonce,address(this),userTimestamp,receiptMessage);
    }

    // Function to set the release fee, only callable by the owner
    function setReleaseFee(uint256 _releaseFee) external onlyOwner {
        releaseFee = _releaseFee;
    }

    // Function to withdraw collected fees
    function withdrawReleaseFee() external onlyOwner {
        require(address(this).balance >= releaseFee, "Insufficient balance to withdraw release fee");
        payable(owner()).transfer(address(this).balance);
    }

    function verifyReceipt(
        address user,
        uint256 amount,
        uint256 nonce,
        address contractAddress,
        bytes memory receipt
    ) internal view returns (bool) {
        // Recreate the message that was signed
        bytes32 receiptMessage = keccak256(abi.encodePacked(user, amount, nonce, contractAddress));

        // Recover the signer address
        address signer = recoverSigner(receiptMessage, receipt);

        // Check that the signer is the owner or authorized party
        return signer == bscContractOwner;
    }

    function recoverSigner(bytes32 message, bytes memory sig) internal pure returns (address) {
        (uint8 v, bytes32 r, bytes32 s) = splitSignature(sig);
        return ecrecover(message, v, r, s);
    }

    function splitSignature(bytes memory sig) internal pure returns (uint8, bytes32, bytes32) {
        require(sig.length == 65, "Invalid signature length");

        bytes32 r;
        bytes32 s;
        uint8 v;

        assembly {
            r := mload(add(sig, 32))
            s := mload(add(sig, 64))
            v := byte(0, mload(add(sig, 96)))
        }

        return (v, r, s);
    }

    // Function to destroy the contract and send remaining funds to the owner
    function destroyContract() external onlyOwner {
        selfdestruct(payable(owner()));
    }
}

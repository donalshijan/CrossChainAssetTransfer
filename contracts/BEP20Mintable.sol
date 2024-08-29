// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";


contract BEP20Mintable is ERC20, AccessControl, Ownable {
    uint256 public mintFee; // Fee required to mint tokens
    mapping(address => uint256) public mintFeesCollected; // Mapping to track fees paid by each user
    mapping(address => uint256) private nonces;
    mapping(address => mapping(uint256 => bool)) private usedReceipts;
    mapping(address => mapping(address => uint256)) private _allowances;
    address private burnEscrowTokenContractAddress;
    address private ethContractOwner;
    uint256 public coordinatorFee;

    // Define roles
    bytes32 public constant OWNER_ROLE = keccak256("OWNER_ROLE");

    constructor(string memory name, string memory symbol, uint256 _mintFee,address _ethContractOwner,uint256 _coordinatorFee) ERC20(name, symbol) Ownable(msg.sender) {
        mintFee = _mintFee;
        ethContractOwner=_ethContractOwner;
        coordinatorFee = _coordinatorFee;

        // Set up the roles
        grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        grantRole(OWNER_ROLE, msg.sender);
    }

    event TokensTransferInitiated(address indexed fromUserAddressOnBinanceChain, uint256 amount, address toUserAddressOnEthereumChain,address tokenAddress,bytes16 transferRequestId);
    event TokensMinted(address indexed toUserAddressOnBinanceChain, uint256 amount, address fromUserAddresOnEthereumChain,bytes16 transferRequestId);
    event MintFeePaid(address indexed payer, uint256 mintFeeAmount, uint256 nonce,address contractAddress, uint256 userTimestamp, bytes32 receiptMessage );
    
    // Function for users to pay mint fee
    function payMintFee(uint256 userTimestamp) external payable {
        require(msg.value >= mintFee, "Insufficient fee paid");
        mintFeesCollected[msg.sender] += msg.value;

        // Increment the nonce for the user
        uint256 nonce = nonces[msg.sender]++;

        // Generate a receipt message including the nonce (but not the user-provided timestamp)
        bytes32 receiptMessage = keccak256(abi.encodePacked(msg.sender, msg.value, nonce, address(this)));

        // Emit the event with the user-provided timestamp
        emit MintFeePaid(msg.sender, msg.value, nonce,address(this), userTimestamp,receiptMessage);
    }

    function mint(address _toUserAddressOnBinanceChain, uint256 _amount, address _fromUserAddressOnEthereumChain,bytes16 transferRequestId) external onlyOwner {
        require(mintFeesCollected[_toUserAddressOnBinanceChain] >= mintFee, "Mint fee not paid or insufficient");
        
        _mint(_toUserAddressOnBinanceChain, _amount);
        mintFeesCollected[_toUserAddressOnBinanceChain] -= mintFee; // Deduct the fee after successful minting
        emit TokensMinted(_toUserAddressOnBinanceChain, _amount, _fromUserAddressOnEthereumChain, transferRequestId);
    }

    function burn(address _fromUserAddressOnBinanceChain, uint256 _amount, address _toUserAddressOnEthereumChain,address tokenAddress,uint256 releaseFeeAmount,uint256 nonce, address contractAddress,bytes memory receipt,bytes16 transferRequestId) external payable{
        // Check that the receipt has not been used before
        require(!usedReceipts[msg.sender][nonce], "Receipt already used");
        // Ensure the signer is the owner of the BSC contract (or another authorized address)
        require(verifyReceipt(_toUserAddressOnEthereumChain, releaseFeeAmount, nonce,contractAddress, receipt), "Invalid receipt");
        // Mark the receipt as used
        usedReceipts[msg.sender][nonce] = true;
        require(balanceOf(_fromUserAddressOnBinanceChain) >= _amount, "Insufficient balance to burn");
        // Check if the contract has been approved to transfer tokens on behalf of the user
        require(this.allowance(_fromUserAddressOnBinanceChain, burnEscrowTokenContractAddress) >= _amount, "Insufficient allowance to transfer tokens");
        require(msg.value >= 3*coordinatorFee, "Insufficient Coordinator fee paid");
        emit TokensTransferInitiated(_fromUserAddressOnBinanceChain, _amount, _toUserAddressOnEthereumChain,tokenAddress, transferRequestId);
    }

    function setBurnEscrowTokenContractAddress(address _burnTokensEscrowAddress) external onlyOwner {
        burnEscrowTokenContractAddress = _burnTokensEscrowAddress;
    }
    

    // function approve(address spender, uint256 amount) public override returns (bool) {
    //     address owner = msg.sender;
    //     _approve(owner, spender, amount);
    //     return true;
    // }

    // function _approve(address owner, address spender, uint256 amount) internal {
    //     require(owner != address(0), "ERC20: approve from the zero address");
    //     require(spender != address(0), "ERC20: approve to the zero address");

    //     _allowances[owner][spender] = amount;
    //     emit Approval(owner, spender, amount);
    // }

    // function allowance(address owner, address spender) external view returns (uint256) {
    //     return _allowances[owner][spender];
    // }
    // Function to set the mint fee, only callable by the owner
    function setMintFee(uint256 _mintFee) external onlyOwner {
        mintFee = _mintFee;
    }

    function withdrawMintFee() external onlyOwner {
        require(address(this).balance >= mintFee, "Insufficient balance to withdraw mint fee");
        payable(owner()).transfer(mintFee);
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
        return signer == ethContractOwner;
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
    function withdrawCoordinatorFees() external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(address(this).balance >= coordinatorFee, "Insufficient balance to withdraw coordinator fee");
        payable(owner()).transfer(coordinatorFee);
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
    // Function to destroy the contract and send remaining funds to the owner
    function destroyContract() external onlyOwner {
        selfdestruct(payable(owner()));
    }
}

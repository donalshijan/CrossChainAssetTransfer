from web3 import Web3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Infura/Node URLs for Ethereum and Binance Smart Chain
ETHEREUM_NODE_URL = os.getenv('ETHEREUM_NODE_URL')
BSC_NODE_URL = os.getenv('BSC_NODE_URL')

# Private key and address of the account that will sign transactions
ETH_CONTRACT_USER_PRIVATE_KEY = os.getenv('ETH_CONTRACT_USER_PRIVATE_KEY')
BSC_CONTRACT_USER_PRIVATE_KEY = os.getenv('BSC_CONTRACT_USER_PRIVATE_KEY')

# Initialize Web3 instances for Ethereum and BSC
web3_eth = Web3(Web3.HTTPProvider(ETHEREUM_NODE_URL))
web3_bsc = Web3(Web3.HTTPProvider(BSC_NODE_URL))

# ABI and contract addresses (Replace with actual ABI and contract addresses)
ERC20_LOCK_ABI = [...]  # Replace with the ABI of your ERC20Lock contract
ERC20_LOCK_ADDRESS = os.getenv('ERC20_LOCK_ADDRESS')
BEP20_ABI = [...]  # Replace with the ABI of your BEP20Mintable contract
BEP20_ADDRESS = os.getenv('BEP20_MINTABLE_ADDRESS')

erc20_lock_contract = web3_eth.eth.contract(address=ERC20_LOCK_ADDRESS, abi=ERC20_LOCK_ABI)
bep20_contract = web3_bsc.eth.contract(address=BEP20_ADDRESS, abi=BEP20_ABI)

def transfer_tokens(fromChainUserAddress, toChainUserAddress, amount, direction, tokenContractAddressOfTokenToTransfer=None):
    if direction == "eth_to_bsc":
        # Ensure the token contract address is provided
        if tokenContractAddressOfTokenToTransfer is None:
            raise ValueError("tokenContractAddressOfTokenToTransfer is required when direction is 'eth_to_bsc'.")

        # Lock tokens on Ethereum
        tx = erc20_lock_contract.functions.lockTokens(tokenContractAddressOfTokenToTransfer, amount, toChainUserAddress).buildTransaction({
            'from': fromChainUserAddress,
            'nonce': web3_eth.eth.getTransactionCount(fromChainUserAddress),
            'gas': 2000000,
            'gasPrice': web3_eth.toWei('20', 'gwei')
        })
        signed_tx = web3_eth.eth.account.sign_transaction(tx, private_key=ETH_CONTRACT_USER_PRIVATE_KEY)
        tx_hash = web3_eth.eth.sendRawTransaction(signed_tx.rawTransaction)
        print(f'Tokens Locked on Ethereum. TxHash: {web3_eth.toHex(tx_hash)}')

    elif direction == "bsc_to_eth":
        # Burn tokens on BSC
        tx = bep20_contract.functions.burn(fromChainUserAddress, amount, toChainUserAddress).buildTransaction({
            'from': fromChainUserAddress,
            'nonce': web3_bsc.eth.getTransactionCount(fromChainUserAddress),
            'gas': 2000000,
            'gasPrice': web3_bsc.toWei('5', 'gwei')
        })
        signed_tx = web3_bsc.eth.account.sign_transaction(tx, private_key=BSC_CONTRACT_USER_PRIVATE_KEY)
        tx_hash = web3_bsc.eth.sendRawTransaction(signed_tx.rawTransaction)
        print(f'Tokens Burned on BSC. TxHash: {web3_bsc.toHex(tx_hash)}')

if __name__ == '__main__':
    from_address = input("Enter the from address: ")
    to_address = input("Enter the to address: ")
    amount = int(input("Enter the amount to transfer: "))
    direction = input("Enter the transfer direction (eth_to_bsc or bsc_to_eth): ")
    
    if direction == "eth_to_bsc":
        tokenContractAddress = input("Enter the ERC20 token contract address: ")
        transfer_tokens(from_address, to_address, amount, direction, tokenContractAddressOfTokenToTransfer=tokenContractAddress)
    else:
        transfer_tokens(from_address, to_address, amount, direction)

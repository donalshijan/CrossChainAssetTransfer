from web3 import Web3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Infura/Node URLs for Ethereum and Binance Smart Chain
ETHEREUM_NODE_URL = os.getenv('ETHEREUM_NODE_URL')
BSC_NODE_URL = os.getenv('BSC_NODE_URL')

# Private key and address of the account that will sign transactions
ETH_CONTRACT_OWNER_PRIVATE_KEY = os.getenv('ETH_CONTRACT_OWNER_PRIVATE_KEY')  # Use environment variable for Ethereum private key
BSC_CONTRACT_OWNER_PRIVATE_KEY = os.getenv('BSC_CONTRACT_OWNER_PRIVATE_KEY')  # Use environment variable for BSC private key
ETH_CONTRACT_OWNER_ADDRESS = os.getenv('ETH_CONTRACT_OWNER_ADDRESS')  # Use environment variable for Ethereum owner address
BSC_CONTRACT_OWNER_ADDRESS = os.getenv('BSC_CONTRACT_OWNER_ADDRESS')  # Use environment variable for BSC owner address

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

def mint_tokens_on_bsc(userAddressOnBinanceChain, amount,fromUserAddressOnEthereumChain):
    tx = bep20_contract.functions.mint(userAddressOnBinanceChain, amount,fromUserAddressOnEthereumChain).buildTransaction({
        'from': BSC_CONTRACT_OWNER_ADDRESS,
        'nonce': web3_bsc.eth.getTransactionCount(BSC_CONTRACT_OWNER_ADDRESS),
        'gas': 2000000,
        'gasPrice': web3_bsc.toWei('5', 'gwei')
    })

    signed_tx = web3_bsc.eth.account.sign_transaction(tx, private_key=BSC_CONTRACT_OWNER_PRIVATE_KEY)
    tx_hash = web3_bsc.eth.sendRawTransaction(signed_tx.rawTransaction)
    print(f'Created Transaction for Minting {amount} tokens for {userAddressOnBinanceChain} on BSC. TxHash: {web3_bsc.toHex(tx_hash)}')

def unlock_tokens_on_ethereum(tokenAddressOfTokenToRelease,userAddressOnEthereumChain, amount,fromUserAddressOnBinanceChain):
    tx = erc20_lock_contract.functions.releaseTokens(tokenAddressOfTokenToRelease,userAddressOnEthereumChain, amount,fromUserAddressOnBinanceChain).buildTransaction({
        'from': ETH_CONTRACT_OWNER_ADDRESS,
        'nonce': web3_eth.eth.getTransactionCount(ETH_CONTRACT_OWNER_ADDRESS),
        'gas': 2000000,
        'gasPrice': web3_eth.toWei('20', 'gwei')
    })

    signed_tx = web3_eth.eth.account.sign_transaction(tx, private_key=ETH_CONTRACT_OWNER_PRIVATE_KEY)
    tx_hash = web3_eth.eth.sendRawTransaction(signed_tx.rawTransaction)
    print(f'Created Transaction for Unlocking {amount} tokens for {userAddressOnEthereumChain} on Ethereum. TxHash: {web3_eth.toHex(tx_hash)}')


def listen_and_relay():
    while True:
        # Listen for TokensLocked event on Ethereum
        event_filter_eth = erc20_lock_contract.events.TokensLocked.createFilter(fromBlock='latest')
        events_eth = event_filter_eth.get_new_entries()
        
        for event in events_eth:
            fromUserAddressOnEthereumChain = event.args.fromUserAddressOnEthereumChain
            amount = event.args.amount
            toUserAddressOnBinanceChain= event.args.toUserAddressOnBinanceChain
            print(f'TokensLocked event detected: {fromUserAddressOnEthereumChain} locked {amount}')
            mint_tokens_on_bsc(toUserAddressOnBinanceChain, amount,fromUserAddressOnEthereumChain)
        # Listen for TokensReleased event on Ethereum
        event_filter_eth_released = erc20_lock_contract.events.TokensReleased.createFilter(fromBlock='latest')
        events_eth_released = event_filter_eth_released.get_new_entries()

        for event in events_eth_released:
            toUserAddressOnEthereumChain = event.args.toUserAddressOnEthereumChain
            amount = event.args.amount
            fromUserAddressOnBinanceChain = event.args.fromUserAddressOnBinanceChain
            print(f'TokensReleased event detected: {toUserAddressOnEthereumChain} released {amount}')
            print(f'{amount} Tokens have been transferred from Binance address {fromUserAddressOnBinanceChain} to Ethereum address {toUserAddressOnEthereumChain}')
            # Handle token release logic if needed

        # Listen for Transfer events on BSC
        event_filter_bsc = bep20_contract.events.TokensMinted.createFilter(fromBlock='latest')
        events_bsc = event_filter_bsc.get_new_entries()

        for event in events_bsc:
            from_address = event.args.fromUserAddresOnEthereumChain
            to_address = event.args.toUserAddressOnBinanceChain
            amount = event.args.amount
            # This indicates minting (tokens are created and sent to the 'to' address)
            print(f'TokensMinted event detected: {to_address} received {amount} Tokens')
            print(f'{amount} Tokens have been transferred from Ethereum wallet {from_address} to Binance Wallet {to_address}')
            # Optionally, handle minting logic if needed

        # Listen for custom TokensBurned event on BSC (to capture Ethereum address)
        event_filter_custom_burn_bsc = bep20_contract.events.TokensBurned.createFilter(fromBlock='latest')
        events_custom_burn_bsc = event_filter_custom_burn_bsc.get_new_entries()

        for event in events_custom_burn_bsc:
            from_ = event.args.fromUserAddressOnBinanceChain
            ethereum_address = event.args.toUserAddressOnEthereumChain
            amount = event.args.amount
            print(f' TokensBurned event detected: {from_} burned {amount} Tokens')
            unlock_tokens_on_ethereum(ethereum_address, amount,from_)

if __name__ == '__main__':
    listen_and_relay()

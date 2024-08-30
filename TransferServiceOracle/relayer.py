from web3 import Web3
import os
from dotenv import load_dotenv
from datetime import datetime
import json
import time
from utils.filelock import acquire_lock
from utils.filelock import release_lock

# Load environment variables
load_dotenv()

def load_abi(file_path):
    with open(file_path, 'r') as file:
        contract_json = json.load(file)
        return contract_json['abi']
    
# Infura/Node URLs for Ethereum and Binance Smart Chain
ETHEREUM_NODE_URL = os.getenv('ETHEREUM_NODE_URL')
BSC_NODE_URL = os.getenv('BSC_NODE_URL')

# Private key and address of the account that will sign transactions
ETH_CONTRACT_OWNER_PRIVATE_KEY = os.getenv('ETH_CONTRACT_OWNER_PRIVATE_KEY')  # Use environment variable for Ethereum private key
BSC_CONTRACT_OWNER_PRIVATE_KEY = os.getenv('BSC_CONTRACT_OWNER_PRIVATE_KEY')  # Use environment variable for BSC private key

ETH_CONTRACT_OWNER_ADDRESS = os.getenv('ETH_CONTRACT_OWNER_ADDRESS')  # Use environment variable for Ethereum owner address
BSC_CONTRACT_OWNER_ADDRESS = os.getenv('BSC_CONTRACT_OWNER_ADDRESS')  # Use environment variable for BSC owner address

BURN_AND_RELEASE_COORDINATOR_CONTRACT_OWNER_ADDRESS=os.getenv('BSC_CONTRACT_OWNER_ADDRESS')
BURN_AND_RELEASE_COORDINATOR_CONTRACT_PRIVATE_KEY=os.getenv('BSC_CONTRACT_OWNER_PRIVATE_KEY')

# ABI and contract addresses (Replace with actual ABI and contract addresses)
ERC20_LOCK_ABI = load_abi('../artifacts/contracts/ERC20Lock.sol/ERC20Lock.json')  # Replace with the ABI of your ERC20Lock contract
ERC20_LOCK_ADDRESS = os.getenv('ERC20_LOCK_ADDRESS')

BEP20_ABI = load_abi('../artifacts/contracts/BEP20Mintable.sol/BEP20Mintable.json') # Replace with the ABI of your BEP20Mintable contract
BEP20_ADDRESS = os.getenv('BEP20_MINTABLE_ADDRESS')

BURN_AND_RELEASE_COORDINATOR_ABI = load_abi('../artifacts/contracts/BurnAndReleaseCoordinator.sol/BurnAndReleaseCoordinator.json')  # Replace with the ABI of your BEP20Mintable contract
BURN_AND_RELEASE_COORDINATOR_ADDRESS = os.getenv('BURN_AND_RELEASE_COORDINATOR_ADDRESS')

# Initialize Web3 instances for Ethereum and BSC
web3_eth = Web3(Web3.HTTPProvider(ETHEREUM_NODE_URL))
web3_bsc = Web3(Web3.HTTPProvider(BSC_NODE_URL))

erc20_lock_contract = web3_eth.eth.contract(address=ERC20_LOCK_ADDRESS, abi=ERC20_LOCK_ABI)
bep20_contract = web3_bsc.eth.contract(address=BEP20_ADDRESS, abi=BEP20_ABI)
burnAndReleaseContract=web3_eth.eth.contract(address=BURN_AND_RELEASE_COORDINATOR_ADDRESS, abi=BURN_AND_RELEASE_COORDINATOR_ABI)

def withdraw_fee(contract_instance,web3_instance, method_name, address, private_key,feetype):
    withdraw_fee_tx = contract_instance.functions[method_name]().buildTransaction({
        'from': address,
        'nonce': web3_instance.eth.getTransactionCount(address),
        'gas': 100000,  # Adjust gas as needed for the withdraw transaction
        'gasPrice': web3_instance.toWei('5', 'gwei')
    })

    signed_withdraw_fee_tx = web3_instance.eth.account.sign_transaction(withdraw_fee_tx, private_key=private_key)
    withdraw_fee_tx_hash = web3_instance.eth.sendRawTransaction(signed_withdraw_fee_tx.rawTransaction)
    print(f'[Relayer] Withdrew {feetype} Fee to {address}. TxHash: {web3_instance.toHex(withdraw_fee_tx_hash)}')
    # Wait for the withdraw transaction to be mined
    web3_instance.eth.waitForTransactionReceipt(withdraw_fee_tx_hash)

def mint_tokens_on_bsc(userAddressOnBinanceChain, amount,fromUserAddressOnEthereumChain,transferRequestId):
    
    withdraw_fee(bep20_contract,web3_bsc,'withdrawMintFee',BSC_CONTRACT_OWNER_ADDRESS,BSC_CONTRACT_OWNER_PRIVATE_KEY,'Mint')
    
    tx = bep20_contract.functions.mint(userAddressOnBinanceChain, amount,fromUserAddressOnEthereumChain,transferRequestId).buildTransaction({
        'from': BSC_CONTRACT_OWNER_ADDRESS,
        'nonce': web3_bsc.eth.getTransactionCount(BSC_CONTRACT_OWNER_ADDRESS),
        'gas': 2000000,
        'gasPrice': web3_bsc.toWei('5', 'gwei')
    })

    signed_tx = web3_bsc.eth.account.sign_transaction(tx, private_key=BSC_CONTRACT_OWNER_PRIVATE_KEY)
    tx_hash = web3_bsc.eth.sendRawTransaction(signed_tx.rawTransaction)
    print(f'[Relayer] Created Transaction for Minting {amount} tokens for {userAddressOnBinanceChain} on BSC. TxHash: {web3_bsc.toHex(tx_hash)}')

def unlock_tokens_on_ethereum(tokenAddressOfTokenToRelease,userAddressOnEthereumChain, amount,fromUserAddressOnBinanceChain,transferRequestId):

    withdraw_fee(erc20_lock_contract,web3_eth,'withdrawReleaseFee',ETH_CONTRACT_OWNER_ADDRESS,ETH_CONTRACT_OWNER_PRIVATE_KEY,'Release')
    
    tx = erc20_lock_contract.functions.releaseTokens(tokenAddressOfTokenToRelease,userAddressOnEthereumChain, amount,fromUserAddressOnBinanceChain,transferRequestId).buildTransaction({
        'from': ETH_CONTRACT_OWNER_ADDRESS,
        'nonce': web3_eth.eth.getTransactionCount(ETH_CONTRACT_OWNER_ADDRESS),
        'gas': 2000000,
        'gasPrice': web3_eth.toWei('20', 'gwei')
    })

    signed_tx = web3_eth.eth.account.sign_transaction(tx, private_key=ETH_CONTRACT_OWNER_PRIVATE_KEY)
    tx_hash = web3_eth.eth.sendRawTransaction(signed_tx.rawTransaction)
    print(f'[Relayer] Created Transaction for Unlocking {amount} tokens for {userAddressOnEthereumChain} on Ethereum. TxHash: {web3_eth.toHex(tx_hash)}')

def initiateBurnAndRelease(tokenAddress,fromUserAddressOnBinanceChain,amount,toUserAddressOnEthereumChain,transferRequestId):
    
    withdraw_fee(bep20_contract,web3_bsc,'withdrawCoordinatorFees',BSC_CONTRACT_OWNER_ADDRESS,BSC_CONTRACT_OWNER_PRIVATE_KEY,'Coordinator')

    tx = burnAndReleaseContract.functions.initateBurnAndRelease(tokenAddress,fromUserAddressOnBinanceChain,amount,toUserAddressOnEthereumChain,transferRequestId).buildTransaction({
        'from': BURN_AND_RELEASE_COORDINATOR_CONTRACT_OWNER_ADDRESS,
        'nonce': web3_bsc.eth.getTransactionCount(BURN_AND_RELEASE_COORDINATOR_CONTRACT_OWNER_ADDRESS),
        'gas': 2000000,
        'gasPrice': web3_bsc.toWei('20', 'gwei')
    })

    signed_tx = web3_bsc.eth.account.sign_transaction(tx, private_key=BURN_AND_RELEASE_COORDINATOR_CONTRACT_PRIVATE_KEY)
    tx_hash = web3_bsc.eth.sendRawTransaction(signed_tx.rawTransaction)
    print(f'[Relayer] Created Transaction for Initiating Burn of {amount} tokens for {fromUserAddressOnBinanceChain} on Binance. TxHash: {web3_bsc.toHex(tx_hash)}')

def releaseCompleted(tokenAddress,fromUserAddressOnBinanceChain,amount,toUserAddressOnEthereumChain,transferRequestId):
    withdraw_fee(bep20_contract,web3_bsc,'withdrawCoordinatorFees',BSC_CONTRACT_OWNER_ADDRESS,BSC_CONTRACT_OWNER_PRIVATE_KEY,'Coordinator')
    
    tx = burnAndReleaseContract.functions.releaseCompleted(tokenAddress,toUserAddressOnEthereumChain,amount,fromUserAddressOnBinanceChain,transferRequestId).buildTransaction({
        'from': BURN_AND_RELEASE_COORDINATOR_CONTRACT_OWNER_ADDRESS,
        'nonce': web3_bsc.eth.getTransactionCount(BURN_AND_RELEASE_COORDINATOR_CONTRACT_OWNER_ADDRESS),
        'gas': 2000000,
        'gasPrice': web3_bsc.toWei('20', 'gwei')
    })

    signed_tx = web3_bsc.eth.account.sign_transaction(tx, private_key=BURN_AND_RELEASE_COORDINATOR_CONTRACT_PRIVATE_KEY)
    tx_hash = web3_bsc.eth.sendRawTransaction(signed_tx.rawTransaction)
    print(f'[Relayer] Created Transaction for Release completion of {amount} tokens for {toUserAddressOnEthereumChain} on Ethereum. TxHash: {web3_bsc.toHex(tx_hash)}')

def releaseFailed(tokenAddress,fromUserAddressOnBinanceChain,amount,toUserAddressOnEthereumChain,transferRequestId):
    withdraw_fee(bep20_contract,web3_bsc,'withdrawCoordinatorFees',BSC_CONTRACT_OWNER_ADDRESS,BSC_CONTRACT_OWNER_PRIVATE_KEY,'Coordinator')
    
    tx = burnAndReleaseContract.functions.releaseFailed(tokenAddress,toUserAddressOnEthereumChain,amount,fromUserAddressOnBinanceChain,transferRequestId).buildTransaction({
        'from': BURN_AND_RELEASE_COORDINATOR_CONTRACT_OWNER_ADDRESS,
        'nonce': web3_bsc.eth.getTransactionCount(BURN_AND_RELEASE_COORDINATOR_CONTRACT_OWNER_ADDRESS),
        'gas': 2000000,
        'gasPrice': web3_bsc.toWei('20', 'gwei')
    })

    signed_tx = web3_bsc.eth.account.sign_transaction(tx, private_key=BURN_AND_RELEASE_COORDINATOR_CONTRACT_PRIVATE_KEY)
    tx_hash = web3_bsc.eth.sendRawTransaction(signed_tx.rawTransaction)
    print(f'[Relayer] Created Transaction for Release Failure of {amount} tokens for {toUserAddressOnEthereumChain} on Ethereum. TxHash: {web3_bsc.toHex(tx_hash)}')


def listen_and_relay(logger=None):
    while True:
        # Listen for TokensLocked event on Ethereum
        event_filter_eth = erc20_lock_contract.events.TokensLocked.createFilter(fromBlock='latest')
        events_eth = event_filter_eth.get_new_entries()
        
        for event in events_eth:
            fromUserAddressOnEthereumChain = event.args.fromUserAddressOnEthereumChain
            amount = event.args.amount
            toUserAddressOnBinanceChain= event.args.toUserAddressOnBinanceChain
            transferRequestId=event.args.transferRequestId
            print(f'[Relayer] TokensLocked event detected: {fromUserAddressOnEthereumChain} locked {amount}')
            mint_tokens_on_bsc(toUserAddressOnBinanceChain, amount,fromUserAddressOnEthereumChain,transferRequestId)
        # Listen for TokensReleased event on Ethereum
        event_filter_eth_released = erc20_lock_contract.events.TokensReleased.createFilter(fromBlock='latest')
        events_eth_released = event_filter_eth_released.get_new_entries()

        for event in events_eth_released:
            toUserAddressOnEthereumChain = event.args.toUserAddressOnEthereumChain
            amount = event.args.amount
            tokenAddress=event.args.tokenAddress
            fromUserAddressOnBinanceChain = event.args.fromUserAddressOnBinanceChain
            transferRequestId=event.args.transferRequestId
            print(f'[Relayer] TokensReleased event detected: {toUserAddressOnEthereumChain} released {amount}')
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            releaseCompleted(tokenAddress,fromUserAddressOnBinanceChain,amount,toUserAddressOnEthereumChain,transferRequestId)
        
        event_filter_eth_TransferFailed = erc20_lock_contract.events.TokenReleaseFailed.createFilter(fromBlock='latest')
        events_eth_Failed = event_filter_eth_TransferFailed.get_new_entries()

        for event in events_eth_Failed:
            toUserAddressOnEthereumChain = event.args.toUserAddressOnEthereumChain
            amount = event.args.amount
            tokenAddress=event.args.tokenAddress
            fromUserAddressOnBinanceChain = event.args.fromUserAddressOnBinanceChain
            transferRequestId=event.args.transferRequestId
            print(f'[Relayer] TokenReleaseFailed event detected')
            releaseFailed(tokenAddress,fromUserAddressOnBinanceChain,amount,toUserAddressOnEthereumChain,transferRequestId)
            

        # Listen for Transfer events on BSC
        event_filter_bsc = bep20_contract.events.TokensMinted.createFilter(fromBlock='latest')
        events_bsc = event_filter_bsc.get_new_entries()

        for event in events_bsc:
            from_address = event.args.fromUserAddresOnEthereumChain
            to_address = event.args.toUserAddressOnBinanceChain
            amount = event.args.amount
            transferRequestId=event.args.transferRequestId
            # This indicates minting (tokens are created and sent to the 'to' address)
            print(f'[Relayer] TokensMinted event detected: {to_address} received {amount} Tokens')
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            while not acquire_lock():
                print('Lock is held by another process. Retrying...')
                time.sleep(1)
            logger.info(f'[Relayer] Transfer of {amount} tokens from Ethereum Address {from_address} to Binance Addres {to_address} completed at [{timestamp}] for the transfer request Id: {transferRequestId}')
            release_lock()
            print(f'[Relayer] Transfer of {amount} tokens from Ethereum Address {from_address} to Binance Addres {to_address} completed at [{timestamp}] for the transfer request Id: {transferRequestId}')
            # Optionally, handle minting logic if needed
            
        event_filter_bsc = bep20_contract.events.TokensTransferInitiated.createFilter(fromBlock='latest')
        events_bsc = event_filter_bsc.get_new_entries()
        
        for event in events_bsc:
            fromUserAddressOnBinanceChain = event.args.fromUserAddressOnBinanceChain
            toUserAddressOnEthereumChain= event.args.toUserAddressOnEthereumChain
            amount = event.args.amount
            tokenAddress=event.args.tokenAddress
            transferRequestId=event.args.transferRequestId
            # This indicates minting (tokens are created and sent to the 'to' address)
            print(f'[Relayer] TokensTransferInitiated event detected')
            initiateBurnAndRelease(tokenAddress,fromUserAddressOnBinanceChain,amount,toUserAddressOnEthereumChain,transferRequestId)

        event_filter_bsc = burnAndReleaseContract.events.BurnInitiated.createFilter(fromBlock='latest')
        events_bsc = event_filter_bsc.get_new_entries()

        for event in events_bsc:
            fromUserAddressOnBinanceChain = event.args.fromUserAddressOnBinanceChain
            toUserAddressOnEthereumChain = event.args.toUserAddressOnEthereumChain
            amount = event.args.amount
            tokenAddress = event.args.tokenAddress
            transferRequestId=event.args.transferRequestId
            # This indicates minting (tokens are created and sent to the 'to' address)
            print(f'[Relayer] TokensBurnInitiated event detected')
            unlock_tokens_on_ethereum(tokenAddress,toUserAddressOnEthereumChain, amount,fromUserAddressOnBinanceChain,transferRequestId)
            
        event_filter_bsc = burnAndReleaseContract.events.TransferCompleted.createFilter(fromBlock='latest')
        events_bsc = event_filter_bsc.get_new_entries()
    
        for event in events_bsc:
            fromUserAddressOnBinanceChain = event.args.fromUserAddressOnBinanceChain
            toUserAddressOnEthereumChain = event.args.toUserAddressOnEthereumChain
            amount = event.args.amount
            tokenAddress = event.args.tokenAddress
            transferRequestId=event.args.transferRequestId
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # This indicates minting (tokens are created and sent to the 'to' address)
            print(f'[Relayer] TransferCompleted event detected')
            while not acquire_lock():
                print('Lock is held by another process. Retrying...')
                time.sleep(1)
            logger.info(f'[Relayer] Transfer of {amount} tokens from Binance Address {fromUserAddressOnBinanceChain} to Ethereum Address {toUserAddressOnEthereumChain} into {tokenAddress} token completed at [{timestamp}] for the transfer request Id: {transferRequestId}')
            release_lock()
            print(f'[Relayer] Transfer of {amount} tokens from Binance Address {fromUserAddressOnBinanceChain} to Ethereum Address {toUserAddressOnEthereumChain} into {tokenAddress} token completed at [{timestamp}] for the transfer request Id: {transferRequestId}')
            
        event_filter_bsc = burnAndReleaseContract.events.ReturnedTokens.createFilter(fromBlock='latest')
        events_bsc = event_filter_bsc.get_new_entries()
    
        for event in events_bsc:
            toUserAddressOnBinanceChain = event.args.toUserAddressOnBinanceChain
            amount = event.args.amount
            transferRequestId=event.args.transferRequestId
            # This indicates minting (tokens are created and sent to the 'to' address)
            print(f'[Relayer] ReturnedTokens event detected')
            print(f'[Relayer] {amount} tokens Returned to {toUserAddressOnBinanceChain}')

if __name__ == '__main__':
    listen_and_relay(logger=None)

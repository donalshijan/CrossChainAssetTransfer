from web3 import Web3
import os
from dotenv import load_dotenv
import time
from datetime import datetime
import requests
import uuid
# Load environment variables
load_dotenv()

# Infura/Node URLs for Ethereum and Binance Smart Chain
ETHEREUM_NODE_URL = os.getenv('ETHEREUM_NODE_URL')
BSC_NODE_URL = os.getenv('BSC_NODE_URL')

# Private key and address of the account that will sign transactions
ETH_CONTRACT_USER_PRIVATE_KEY = os.getenv('ETH_CONTRACT_USER_PRIVATE_KEY')
BSC_CONTRACT_USER_PRIVATE_KEY = os.getenv('BSC_CONTRACT_USER_PRIVATE_KEY')

ETH_CONTRACT_USER_ADDRESS = os.getenv('ETH_CONTRACT_USER_ADDRESS')  
BSC_CONTRACT_USER_ADDRESS = os.getenv('BSC_CONTRACT_USER_ADDRESS')  

# Initialize Web3 instances for Ethereum and BSC
web3_eth = Web3(Web3.HTTPProvider(ETHEREUM_NODE_URL))
web3_bsc = Web3(Web3.HTTPProvider(BSC_NODE_URL))

# ABI and contract addresses (Replace with actual ABI and contract addresses)
ERC20_LOCK_ABI = [...]  # Replace with the ABI of your ERC20Lock contract
ERC20_LOCK_ADDRESS = os.getenv('ERC20_LOCK_ADDRESS')
BEP20_ABI = [...]  # Replace with the ABI of your BEP20Mintable contract
BEP20_ADDRESS = os.getenv('BEP20_MINTABLE_ADDRESS')
BURN_ESCROW_ADDRESS = os.getenv('BURN_ESCROW_ADDRESS')

ERC20_TOKEN_TO_TRANSFER_ABI = [...]
ERC20_TOKEN_TO_TRANSFER_ADDRESS = web3_eth.toChecksumAddress(os.getenv('ERC20_TOKEN_TO_TRANSFER_ADDRESS'))

erc20_token_contract = web3_eth.eth.contract(address=ERC20_TOKEN_TO_TRANSFER_ADDRESS, abi=ERC20_TOKEN_TO_TRANSFER_ABI)
erc20_lock_contract = web3_eth.eth.contract(address=ERC20_LOCK_ADDRESS, abi=ERC20_LOCK_ABI)
bep20_contract = web3_bsc.eth.contract(address=BEP20_ADDRESS, abi=BEP20_ABI)


def approve_transfer(web3_instance,contract,method,spender, amount, from_address, private_key):
    tx = contract.functions[method](spender, amount).buildTransaction({
        'from': from_address,
        'nonce': web3_instance.eth.getTransactionCount(from_address),
        'gas': 2000000,
        'gasPrice': web3_instance.toWei('20', 'gwei')
    })
    signed_tx = web3_instance.eth.account.sign_transaction(tx, private_key=private_key)
    tx_hash = web3_instance.eth.sendRawTransaction(signed_tx.rawTransaction)
    receipt = web3_instance.eth.waitForTransactionReceipt(tx_hash)
    print(f"Tokens Approved. TxHash: {web3_instance.toHex(tx_hash)}")
    return receipt

def pay_mint_fee(to_address, mint_fee):
    timestamp = int(time.time())
    receipt_id = f"{to_address}-{timestamp}"

    # Make the transaction to pay the mint fee
    txn = bep20_contract.functions.payMintFee(timestamp).buildTransaction({
        'from': to_address,
        'value': web3_bsc.toWei(mint_fee, 'ether'),  # Replace with the actual mint fee in ether
        'nonce': web3_bsc.eth.getTransactionCount(to_address),
        'gas': 2000000,
        'gasPrice': web3_bsc.toWei('20', 'gwei')
    })

    signed_txn = web3_bsc.eth.account.signTransaction(txn, private_key=BSC_CONTRACT_USER_PRIVATE_KEY)
    txn_hash = web3_bsc.eth.sendRawTransaction(signed_txn.rawTransaction)

    print(f"Mint fee transaction sent. Hash: {txn_hash.hex()}")

    # Poll for the receipt using the receipt_id via HTTP request
    url = f"http://localhost:8000/collect/"
    payload = {'receipt_id': receipt_id}
    
    while True:
        try:
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                receipt_data = response.json()
                print(f"Receipt found: {receipt_data}")
                break
            else:
                print("Receipt not found, polling again in 5 seconds...")
        except requests.exceptions.RequestException as e:
            print(f"Error during the HTTP request: {e}")
        
        time.sleep(5)

    return receipt_data

def pay_release_fee( to_address, release_fee):
    timestamp = int(time.time())
    receipt_id = f"{to_address}-{timestamp}"
    tx = erc20_lock_contract.functions.payReleaseFee(timestamp).buildTransaction({
        'from': from_address,
        'value': web3_eth.toWei(release_fee, 'ether'),
        'nonce': web3_eth.eth.getTransactionCount(from_address),
        'gas': 2000000,
        'gasPrice': web3_eth.toWei('20', 'gwei')
    })
    signed_tx = web3_eth.eth.account.sign_transaction(tx, private_key=ETH_CONTRACT_USER_PRIVATE_KEY)
    tx_hash = web3_eth.eth.sendRawTransaction(signed_tx.rawTransaction)
    receipt = web3_eth.eth.waitForTransactionReceipt(tx_hash)
    print(f"Release Fee Paid. TxHash: {web3_eth.toHex(tx_hash)}")
    
     # Poll for the receipt using the receipt_id via HTTP request
    url = f"http://localhost:8000/collect/"
    payload = {'receipt_id': receipt_id}
    
    while True:
        try:
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                receipt_data = response.json()
                print(f"Receipt found: {receipt_data}")
                break
            else:
                print("Receipt not found, polling again in 5 seconds...")
        except requests.exceptions.RequestException as e:
            print(f"Error during the HTTP request: {e}")
        
        time.sleep(5)

    return receipt_data

def transfer_tokens(from_chain_user_address, to_chain_user_address, amount, direction,receipt,token_contract_address_of_token_to_transfer_from_or_to_on_eth_chain):
    transferRequestId = uuid.uuid4()
    if direction == "eth_to_bsc":
        fee_amount = receipt['feeAmount']
        nonce = receipt['nonce']
        contract_address = receipt['contractAddress']
        receipt_signature = receipt['receipt']
        tx = erc20_lock_contract.functions.lockTokens(token_contract_address_of_token_to_transfer_from_or_to_on_eth_chain, amount, to_chain_user_address,fee_amount,nonce,contract_address,receipt_signature,transferRequestId).buildTransaction({
            'from': from_chain_user_address,
            'nonce': web3_eth.eth.getTransactionCount(from_chain_user_address),
            'gas': 2000000,
            'gasPrice': web3_eth.toWei('20', 'gwei')
        })
        signed_tx = web3_eth.eth.account.sign_transaction(tx, private_key=ETH_CONTRACT_USER_PRIVATE_KEY)
        tx_hash = web3_eth.eth.sendRawTransaction(signed_tx.rawTransaction)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f'Tokens Lock called on Ethereum. TxHash: {web3_eth.toHex(tx_hash)} ')
        print(f'Token Transfer for ${amount} tokens of {token_contract_address_of_token_to_transfer_from_or_to_on_eth_chain} from Ethereum  address {from_chain_user_address} to Binance  address {to_chain_user_address} initiated at [{timestamp}] with Transfer request id [{transferRequestId}]')

    elif direction == "bsc_to_eth":
        fee_amount = receipt['feeAmount']
        nonce = receipt['nonce']
        contract_address = receipt['contractAddress']
        receipt_signature = receipt['receipt']
        coordinator_fee = bep20_contract.functions.coordinatorFee().call()
        # Burn tokens on BSC
        tx = bep20_contract.functions.burn(from_chain_user_address, amount, to_chain_user_address,token_contract_address_of_token_to_transfer_from_or_to_on_eth_chain,fee_amount,nonce,contract_address,receipt_signature,transferRequestId).buildTransaction({
            'from': from_chain_user_address,
            'value': coordinator_fee,
            'nonce': web3_bsc.eth.getTransactionCount(from_chain_user_address),
            'gas': 2000000,
            'gasPrice': web3_bsc.toWei('5', 'gwei')
        })
        signed_tx = web3_bsc.eth.account.sign_transaction(tx, private_key=BSC_CONTRACT_USER_PRIVATE_KEY)
        tx_hash = web3_bsc.eth.sendRawTransaction(signed_tx.rawTransaction)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f'Tokens Burn called on BSC. TxHash: {web3_bsc.toHex(tx_hash)} at [{timestamp}]')
        print(f'Token Transfer for ${amount} tokens from Ethereum  address {from_chain_user_address} to Binance  address {to_chain_user_address} into  {token_contract_address_of_token_to_transfer_from_or_to_on_eth_chain} tokens initiated at [{timestamp}] with Transfer request id [{transferRequestId}]')

def transfer(from_address,to_address,amount,direction,token_contract_address):    
    if direction == "eth_to_bsc":
        approve_transfer(web3_eth,erc20_token_contract,'approve',ERC20_LOCK_ADDRESS, amount, from_address, ETH_CONTRACT_USER_PRIVATE_KEY)
        mint_fee = bep20_contract.functions.mintFee().call()  # Get the mint fee
        receipt = pay_mint_fee(to_address, mint_fee)
        transfer_tokens(from_address, to_address, amount, direction,receipt, token_contract_address_of_token_to_transfer_from_or_to_on_eth_chain=token_contract_address)
    elif direction=="bsc_to_eth":
         # Step 1: Approve Tokens
        approve_transfer(web3_bsc,bep20_contract,'approve',BURN_ESCROW_ADDRESS, amount, from_address, BSC_CONTRACT_USER_PRIVATE_KEY)
        # Step 2: Pay Release Fee Collect the receipt
        release_fee = erc20_lock_contract.functions.releaseFee().call() # Get the release fee
        receipt = pay_release_fee(to_address, release_fee)
        transfer_tokens(from_address, to_address, amount, direction,receipt,token_contract_address_of_token_to_transfer_from_or_to_on_eth_chain=token_contract_address)
    else:
        print('Invalid direction')
        
if __name__ == "__main__":
    from_address = Web3.toChecksumAddress(ETH_CONTRACT_USER_ADDRESS)
    to_address = Web3.toChecksumAddress(BSC_CONTRACT_USER_ADDRESS)
    amount = int(0.01)
    direction = "eth_to_bsc"
    token_contract_address = Web3.toChecksumAddress(ERC20_TOKEN_TO_TRANSFER_ADDRESS)
    transfer(from_address,to_address,amount,direction,token_contract_address)
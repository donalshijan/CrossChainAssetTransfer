from web3 import Web3
import json
import os
import time
import threading
from dotenv import load_dotenv
from service import stop_flag

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
ETH_CONTRACT_OWNER_PRIVATE_KEY = os.getenv('ETH_CONTRACT_OWNER_PRIVATE_KEY')
BSC_CONTRACT_OWNER_PRIVATE_KEY = os.getenv('BSC_CONTRACT_OWNER_PRIVATE_KEY')

ETH_CONTRACT_OWNER_ADDRESS = os.getenv('ETH_CONTRACT_OWNER_ADDRESS')
BSC_CONTRACT_OWNER_ADDRESS = os.getenv('BSC_CONTRACT_OWNER_ADDRESS')

# Contract addresses and ABI (replace with actual values)
ERC20_LOCK_ABI = load_abi('../artifacts/contracts/ERC20Lock.sol/ERC20Lock.json')  # Replace with your ERC20Lock contract ABI
ERC20_LOCK_ADDRESS = os.getenv('ERC20_LOCK_ADDRESS')

BEP20_ABI = load_abi('../artifacts/contracts/BEP20Mintable.sol/BEP20Mintable.json') # Replace with your BEP20Mintable contract ABI
BEP20_ADDRESS = os.getenv('BEP20_MINTABLE_ADDRESS')

BURN_AND_RELEASE_COORDINATOR_ABI = load_abi('../artifacts/contracts/BurnAndReleaseCoordinator.sol/BurnAndReleaseCoordinator.json')  # Replace with your coordinator contract ABI
BURN_AND_RELEASE_COORDINATOR_ADDRESS = os.getenv('BURN_AND_RELEASE_COORDINATOR_ADDRESS')

# Initialize Web3 instances
web3_eth = Web3(Web3.HTTPProvider(ETHEREUM_NODE_URL))
web3_bsc = Web3(Web3.HTTPProvider(BSC_NODE_URL))

# Contract instances
erc20_lock_contract = web3_eth.eth.contract(address=ERC20_LOCK_ADDRESS, abi=ERC20_LOCK_ABI)
bep20_contract = web3_bsc.eth.contract(address=BEP20_ADDRESS, abi=BEP20_ABI)
burn_and_release_contract = web3_eth.eth.contract(address=BURN_AND_RELEASE_COORDINATOR_ADDRESS, abi=BURN_AND_RELEASE_COORDINATOR_ABI)



def update_gas_fee(contract,web3_instance, function_name, address,privatekey, fee):
    
        tx = contract.functions[function_name](fee).buildTransaction({
            'from': address,
            'nonce': web3_instance.eth.getTransactionCount(address),
            'gas': 2000000,
            'gasPrice': web3_eth.toWei('20', 'gwei')
        })
        signed_tx = web3_instance.eth.account.sign_transaction(tx, private_key=privatekey)
        tx_hash = web3_instance.eth.sendRawTransaction(signed_tx.rawTransaction)
        print(f"[FeeEstimator] Updated {function_name} fee. TxHash: {web3_instance.toHex(tx_hash)}")

def calculate_and_update_gas_fee_for_coordinator():
    gas_estimate = burn_and_release_contract.functions.initateBurnAndRelease().estimateGas({
        'from': BSC_CONTRACT_OWNER_ADDRESS
    })
    gas_estimate += burn_and_release_contract.functions.releaseCompleted().estimateGas({
        'from': BSC_CONTRACT_OWNER_ADDRESS
    })
    gas_estimate += burn_and_release_contract.functions.releaseFailed().estimateGas({
        'from': BSC_CONTRACT_OWNER_ADDRESS
    })

    gas_price = web3_bsc.eth.gas_price
    current_fee = bep20_contract.functions.coordinatorFee().call()
    total_gas_fee = gas_estimate * gas_price
    total_gas_fee_in_ether = web3_bsc.fromWei(total_gas_fee, 'ether')

    print(f"[FeeEstimator] Estimated Max Gas Usage for Coordinator: {gas_estimate}")
    print(f"[FeeEstimator] Gas Price: {web3_bsc.fromWei(gas_price, 'gwei')} gwei")
    print(f"[FeeEstimator] Total Gas Fee: {total_gas_fee_in_ether} ETH")

    if total_gas_fee < current_fee:
        update_gas_fee(bep20_contract,web3_bsc,'setCoordinatorFee', BSC_CONTRACT_OWNER_ADDRESS, BSC_CONTRACT_OWNER_PRIVATE_KEY,total_gas_fee)

def calculate_and_update_gas_fee_for_release_tokens():
    gas_estimate = erc20_lock_contract.functions.releaseTokens().estimateGas({
        'from': ETH_CONTRACT_OWNER_ADDRESS
    })
    
    gas_price = web3_eth.eth.gas_price
    current_fee = erc20_lock_contract.functions.releaseFee().call()
    total_gas_fee = gas_estimate * gas_price
    total_gas_fee_in_ether = web3_eth.fromWei(total_gas_fee, 'ether')

    print(f"[FeeEstimator] Estimated Max Gas Usage for Release Tokens: {gas_estimate}")
    print(f"[FeeEstimator] Gas Price: {web3_eth.fromWei(gas_price, 'gwei')} gwei")
    print(f"[FeeEstimator] Total Gas Fee: {total_gas_fee_in_ether} ETH")

    if total_gas_fee < current_fee:
        update_gas_fee(erc20_lock_contract,web3_eth,'setReleaseFee', ETH_CONTRACT_OWNER_ADDRESS, ETH_CONTRACT_OWNER_PRIVATE_KEY,total_gas_fee)

def calculate_and_update_gas_fee_for_mint():
    gas_estimate = bep20_contract.functions.mint().estimateGas({
        'from': BSC_CONTRACT_OWNER_ADDRESS
    })

    gas_price = web3_bsc.eth.gas_price
    current_fee = bep20_contract.functions.mintFee().call()
    total_gas_fee = gas_estimate * gas_price
    total_gas_fee_in_ether = web3_bsc.fromWei(total_gas_fee, 'ether')

    print(f"[FeeEstimator] Estimated Max Gas Usage for Mint: {gas_estimate}")
    print(f"[FeeEstimator] Gas Price: {web3_bsc.fromWei(gas_price, 'gwei')} gwei")
    print(f"[FeeEstimator] Total Gas Fee: {total_gas_fee_in_ether} ETH")

    if total_gas_fee < current_fee:
        update_gas_fee(bep20_contract,web3_bsc,'setMintFee', BSC_CONTRACT_OWNER_ADDRESS, BSC_CONTRACT_OWNER_PRIVATE_KEY,total_gas_fee)

# Function to run the fee update tasks in parallel
def run_fee_update_tasks():
    tasks = [
        threading.Thread(target=calculate_and_update_gas_fee_for_coordinator,daemon=True),
        threading.Thread(target=calculate_and_update_gas_fee_for_release_tokens,daemon=True),
        threading.Thread(target=calculate_and_update_gas_fee_for_mint,daemon=True)
    ]

    for task in tasks:
        task.start()

    for task in tasks:
        task.join()

# Polling the fee update tasks at regular intervals
def poll_fee_updates(interval=600):
    while not stop_flag.is_set():
        run_fee_update_tasks()
        stop_flag.wait(interval)

if __name__ == "__main__":
    # Start the polling process
    poll_fee_updates(interval=600)  # Poll every 10 minutes (600 seconds)

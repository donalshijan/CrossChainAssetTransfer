import threading
import asyncio
from web3 import Web3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connect to Ethereum and BSC nodes
BSC_NODE_URL = os.getenv('BSC_NODE_URL')
ETH_NODE_URL = os.getenv('ETHEREUM_NODE_URL')

# Contract details
BEP20_ABI = [...]  # Replace with the ABI of your BEP20Mintable contract
ETH20_LOCK_ABI = [...]  # Replace with the ABI of your ERC20Lock contract

BEP20_ADDRESS = os.getenv('BEP20_MINTABLE_ADDRESS')
ERC20_LOCK_ADDRESS = os.getenv('ERC20_LOCK_ADDRESS')

# Initialize Web3 instances for BSC and Ethereum
web3_bsc = Web3(Web3.HTTPProvider(BSC_NODE_URL))
web3_eth = Web3(Web3.HTTPProvider(ETH_NODE_URL))

# Initialize contracts
bep20_contract = web3_bsc.eth.contract(address=BEP20_ADDRESS, abi=BEP20_ABI)
erc20_lock_contract = web3_eth.eth.contract(address=ERC20_LOCK_ADDRESS, abi=ETH20_LOCK_ABI)

# Private keys for signing (Make sure to keep this secure!)
BSC_CONTRACT_OWNER_PRIVATE_KEY = os.getenv('BSC_CONTRACT_OWNER_PRIVATE_KEY')
ETH_CONTRACT_OWNER_PRIVATE_KEY = os.getenv('ETH_CONTRACT_OWNER_PRIVATE_KEY')

# Data structure to store signed receipts
signed_receipts = {}

# Event handler (as defined above)
def handle_event(event, event_name):
    sender = event['args']['payer']
    value = event['args'].get('mintFeeAmount') or event['args'].get('releaseFeeAmount')
    nonce = event['args']['nonce']
    contractAddress = event['args']['contractAddress']
    timestamp = event['args']['userTimestamp']
    receipt_message = event['args']['receiptMessage']

    # Select the private key based on the event name
    if event_name == "MintFeePaid":
        private_key = BSC_CONTRACT_OWNER_PRIVATE_KEY
    elif event_name == "ReleaseFeePaid":
        private_key = ETH_CONTRACT_OWNER_PRIVATE_KEY
    else:
        raise ValueError(f"Unknown event name: {event_name}")

    # Sign the receipt message using the selected private key
    signed_message = web3_bsc.eth.account.sign_message(receipt_message, private_key)
    receipt_id = f"{sender}-{timestamp}"
    signed_receipts[receipt_id] = {
        'feeAmount': value,
        'nonce': nonce,
        'contractAddress': contractAddress,
        'receipt': signed_message.signature.hex(),
    }

    print(f"Signed receipt stored for {sender} for {event_name} event: {signed_receipts[receipt_id]}")

# Event listener function
def log_loop(event_filter, poll_interval, event_name):
    while True:
        for event in event_filter.get_new_entries():
            handle_event(event, event_name)
        web3_bsc.middleware_stack.sleep(poll_interval)

# Create a filter for the MintFeePaid event on BSC
mint_fee_filter = bep20_contract.events.MintFeePaid.createFilter(fromBlock='latest')
# Create a filter for the ReleaseFeePaid event on Ethereum
release_fee_filter = erc20_lock_contract.events.ReleaseFeePaid.createFilter(fromBlock='latest')

async def collect_receipt(receipt_id):
    # Retrieve the receipt by its unique receipt ID asynchronously
    await asyncio.sleep(0)  # Yield control to the event loop
    receipt = signed_receipts.get(receipt_id, None)

    if receipt:
        return receipt
    else:
        return "Receipt not found."

# Function to run the event listeners in parallel using threading
def start_event_listeners():
    threading.Thread(target=log_loop, args=(mint_fee_filter, 2, 'MintFeePaid')).start()
    threading.Thread(target=log_loop, args=(release_fee_filter, 2, 'ReleaseFeePaid')).start()

async def main():
    print("Event listeners started...")
    start_event_listeners()

    # Example usage: collecting receipts asynchronously
    while True:
        # Simulate some async receipt collection
        receipt_id = "some-receipt-id"
        receipt = await collect_receipt(receipt_id)
        print(f"Collected receipt: {receipt}")
        await asyncio.sleep(10)  # Wait before collecting again

# Run the asyncio event loop
asyncio.run(main())

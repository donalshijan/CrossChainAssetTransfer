# Cross Chain Asset Transfer Project

This project let's a user to transfer any ERC 20 token from Ethereum chain to a Specific BEP 20 token on Binance Smart Chain and the other way around.

It uses Lock & mint and Burn & Release mechanism to achieve that, where when a user makes a request to transfer an ERC20, that specific amount of ERC20 gets locked and held by a contract and same amount of BEP20 gets minted and credited to the user's address which the user must have specified as 'transfer to address'.

When the user wants to transfer that specific BEP20 back to the original ERC20 token which was locked to mint and get that BEP20 , the BEP20 gets burned and the locked amount of ERC20 gets released back to the user's address, again which must have been specified as 'transfer to address'.


## Project Architecture

    The project mainly involves one core service and two helper services all of which combined together build our conceptual Transfer Service Oracle. The services are:

    - Relayer (core)
    - Receipt Generator
    - Fee Estimator

### Relayer
The relayer Service will constantly monitor for events emitted by the contracts which lets users initiate transfer request by calling appropriate methods.
The events emitted are captured and necessary actions are taken by relayer for each event and there by fascilitating propogation of transfer request through different stages from initiation to completion.

### Receipt Generator
This service is used by users who interact with the contract , before making the call to transfer on the contract, users need to pay the fee for the cost of transfering which involves relayer making calls of it's own to contracts on behalf of the user's transfer request to fascilitate the transfer.
Normally the caller of the method for transfer (user) is the one who pays for the transaction, but since here two different chains are involved, it is not a straight forward task.
Receipt Generator will generate a receipt saying that the user has paid fee for either minting on BSC or releasing on Ethereum chain.
The user then makes the transfer call along with this receipt which will then be verified on the other chain, this is a crucial step only after which is the appropriate event regarding transfer initiation is emitted, the relayer will pick up this event and make the necessary calls on behalf of the user to move transfer request through to the next stages, these calls cost gas, and with this receipt, relayer is guaranteed that the user has paid for the fees ahead of time, so the relayer doesn't mind making calls on the user's behalf spending ETH or BNB from relayer's wallet.

### Fee Estimator
This service keeps monitoring the estimated gas cost for calls for which fee needs to be collected from user, since gas cost keeps changing based on network congestion and other factors, it will calculate the estimate for those calls and if it exceeds the current set fee amount value on contracts, it will update the fee at regular intervals.

# How to Run 

## Install all Dependencies

```
python3 -m venv venv
source venv/bin/activate
venv\Scripts\activate
pip install -r requirements.txt
deactivate

npm install
```

## Compile the contracts by running

    npx hardhat compile


## Set up environment variables

Create a .env file at the root of the project folder and add following environment variables

    ETHERSCAN_API_KEY = <create an account on etherscan and get this api key>
    BSCSCAN_API_KEY = <create an account on bscscan and get this api key>
    ETHEREUM_NODE_URL = <use any node url for any of the ethereum rpc client>
    BSC_NODE_URL = <use any node url for any of the BSC rpc client>
    ETH_CONTRACT_OWNER_PRIVATE_KEY = < You will be deploying ethereum smart contract with this account>
    BSC_CONTRACT_OWNER_PRIVATE_KEY = < You will be deploying your BSC smart contracts with this account>
    ETH_CONTRACT_OWNER_ADDRESS = <wallet address of the account you used to deploy the ethereum smart contract>
    BSC_CONTRACT_OWNER_ADDRESS = <wallet address of the account you used to deploy your BSC smart contracts>
    ERC20_LOCK_ADDRESS = <address of the ERC20_Lock contract after deploying>
    BEP20_MINTABLE_ADDRESS = <address of the BEP20_Mintable contract after deploying>
    BURN_AND_RELEASE_COORDINATOR_ADDRESS = <address of the BurnAndReleaseCoordinator contract after deploying>

    // All environment variables mentioned above are essential for contracts to be deployed and the transfer service to run, all environment variables after this is for running test specific scripts and script for interacting with the service in general.

    ERC20_TOKEN_TO_TRANSFER_ADDRESS = <contract address of the ERC20 token that you wish to transfer from Ethereum chain to BSC>
    ETH_CONTRACT_USER_PRIVATE_KEY= <private key of the user's eth account using the transfer service to transfer from Eth chain to BSC by interacting with ETH contract, used for running the test, but also used for interacting and doing transfers in general>
    BSC_CONTRACT_USER_PRIVATE_KEY= <private key of the user's BSC account using the transfer service to transfer from BSC  to Eth Chain by interacting with BSC contracts, used for running the test, but also used for interacting and doing transfers in general>
    ETH_CONTRACT_USER_ADDRESS= <wallet address of user using the transfer service and calling the eth contract for transfer from eth to bsc>
    BSC_CONTRACT_USER_ADDRESS= <wallet address of user using the transfer service and calling the BSC contract for transfer from BSC to ETH>


## Commands to deploy contracts to testnet 


```
npx hardhat run deploy.js --network ethereum_sepolia
npx hardhat run deploy.js --network bsc_testnet
```


## Start services and run test

At this point you need to make sure you have funded the accounts which were used to deploy contracts with test ether and bnb from faucets, also fund the accounts which will involve in the testing with test ether and bnb from faucets to run the test.

Set up the .env file with appropriate variables and values, and also set up the value for contract abi for the ERC20 token contract in the transfer.js/transfer.py script,this is the token you intend to transfer.

The line
`const ERC20_TOKEN_TO_TRANSFER_ABI = [...];` of the transfer.js file need to be provided with correct abi of erc20 token user wishes to transfer.

After that run

```
chmod +x start_services_and_run_test.sh 
bash start_services_and_run_test.sh
```
This will start all the services and run a test which will make a bunch of transfer calls and monitor logs and evaluate the performance and cost of making transfers and output the results in a file called PerformanceAndCostEvaluationResults.txt.
    
The test will take a while which is why it has a progress bar to indicate how far into the transfers are we currently in, and indicates us when the transfers have finished and the PerformanceAndCostEvaluationResults.txt is ready with final results.

## Start services

To simply start all the services, you need to 

    cd TransferServiceOracle

and then run

    python3 service.py

To interact and make transfers

You can use either the transfer.js or transfer.py script, which is a demo script to interact with the service to make transfer calls, a user can write their own script to interact with the contracts, obviously, but this is an example of how a typical interaction script should look like as it involves all the necessary actions to be taken on user's part.
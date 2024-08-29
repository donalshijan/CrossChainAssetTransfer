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

Compile the contracts by running

`npx hardhat compile
`


## Commands to deploy contracts to testnet 


```
npx hardhat run deploy.js --network ethereum_sepolia
npx hardhat run deploy.js --network bsc_testnet
```
## Start services and run test

```
chmod +x start_services_and_run_test.sh 
bash start_services_and_run_test.sh
```
    This will start all the services and run a test which will make a bunch of transfer calls and monitor logs and evaluate the performance and cost of making transfers and output the results in a file called PerformanceAndCostEvaluationResults.txt.
    
    The test will take a while which is why it has a progress bar to indicate how far into the transfers are we currently in, and indicates us when the transfers have finished and the PerformanceAndCostEvaluationResults.txt is ready with final results.

## Start services

To simply start all the services you need to 

`cd TransferServiceOracle`

and then run

`python3 service.py`

To interact and make transfers

    You can use either the transfer.js or transfer.py script, which is a demo script to interact with the service to make transfer calls, a user can write their own script to interact with the contracts, obviously, but this is an example of how a typical interaction script should look like as it involves all the necessary actions to be taken on user's part.
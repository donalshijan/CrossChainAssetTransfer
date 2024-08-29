const { ethers } = require("ethers");
const { transfer } = require("./transfer"); // Replace with the actual path to your transfer script
const { monitorTransferLogs, waitForAllTransfersToComplete } = require('./monitorTransfer.js');
const { initializeProgressBar, completeProgressBar } = require('./progressTracker.js');
require("dotenv").config();

// Number of times to perform the transfer
const NUM_INITIAL_TRANSFERS = 5;
const NUM_TRANSFERS = 10;


// Addresses and amounts for testing
const ETH_CONTRACT_USER_ADDRESS = ethers.utils.getAddress(process.env.ETH_CONTRACT_USER_ADDRESS);
const BSC_CONTRACT_USER_ADDRESS = ethers.utils.getAddress(process.env.BSC_CONTRACT_USER_ADDRESS);
const ERC20_TOKEN_TO_TRANSFER_ADDRESS = ethers.utils.getAddress(process.env.ERC20_TOKEN_TO_TRANSFER_ADDRESS);

// Addresses and amounts for testing
const ETH_CONTRACT_OWNER_ADDRESS = ethers.utils.getAddress(process.env.ETH_CONTRACT_OWNER_ADDRESS);
const BSC_CONTRACT_OWNER_ADDRESS = ethers.utils.getAddress(process.env.BSC_CONTRACT_OWNER_ADDRESS);

const AMOUNT = ethers.utils.parseUnits("0.01", 18); // The amount to transfer (replace with your desired amount)

// Log file paths
const logFilePath = './transfers.log';
const resultsFilePath = './PerformanceAndCostEvaluationResults.txt';

async function makeTestTransfers(numTransfers) {
    for (let i = 0; i < numTransfers; i++) {
        try {
            console.log(`Starting ETH to BSC transfer ${i + 1}/${numTransfers}...`);
            
            // Ethereum to BSC transfer
            await transfer(
                ETH_CONTRACT_USER_ADDRESS,
                BSC_CONTRACT_USER_ADDRESS,
                AMOUNT,
                "eth_to_bsc",
                ERC20_TOKEN_TO_TRANSFER_ADDRESS
            );

            console.log(` ${i + 1} - ETH to BSC Transfer Call made.`);

            // Wait for the first transfer to be confirmed before initiating the next one
            // await waitForAllTransfersToComplete();

            console.log(`Starting BSC to ETH transfer ${i + 1}/${numTransfers}...`);

            // BSC to Ethereum transfer
            await transfer(
                BSC_CONTRACT_USER_ADDRESS,
                ETH_CONTRACT_USER_ADDRESS,
                AMOUNT,
                "bsc_to_eth",
                ERC20_TOKEN_TO_TRANSFER_ADDRESS
            );

            console.log(` ${i + 1} - BSC to ETH Transfer Call made.`);
        } catch (error) {
            console.error(`Error during transfer ${i + 1}:`, error);
        }
    }

    console.log("All transfers calls made.");
}

// Function to transfer ETH to BSC to populate the BSC address with minted tokens
async function transferToPopulateBscAddressWithMintedTokens(numTransfers) {
    for (let i = 0; i < numTransfers; i++) {
        try {
            console.log(`Starting ETH to BSC transfer ${i + 1}/${numTransfers}...`);

            // Ethereum to BSC transfer
            await transfer(
                ETH_CONTRACT_USER_ADDRESS,
                BSC_CONTRACT_USER_ADDRESS,
                AMOUNT,
                "eth_to_bsc",
                ERC20_TOKEN_TO_TRANSFER_ADDRESS
            );

            console.log(` ${i + 1} - ETH to BSC Transfer Call made.`);
        } catch (error) {
            console.error(`Error during ETH to BSC transfer ${i + 1}:`, error);
        }
    }

    console.log("All ETH to BSC transfer calls made.");
}

// Run the transfer to populate BSC address with some minted tokens and then make the test transfers and log info and use it to evaluate performance and cost
(async (num_of_transfers) => {
    let stopMonitoringInitialTransfers;
    let stopMonitoringTestTransfers;
    try {
        initializeProgressBar(num_of_transfers);
        // Start monitoring logs
        stopMonitoringInitialTransfers = monitorTransferLogs('./transfers.log',num_of_transfers);
        await transferToPopulateBscAddressWithMintedTokens(num_of_transfers);
        // Wait until the transfer is confirmed
        await waitForAllTransfersToComplete();
        // Stop monitoring logs
        stopMonitoringInitialTransfers();

        // 1. Clear the transfers.log file
        fs.writeFileSync(logFilePath, '');

        // 2. Fetch and log balances before transfers
        const ethProvider = new ethers.providers.JsonRpcProvider(process.env.ETH_RPC_URL);
        const bscProvider = new ethers.providers.JsonRpcProvider(process.env.BSC_RPC_URL);

        const ethBalance = await ethProvider.getBalance(ETH_CONTRACT_OWNER_ADDRESS);
        const bscBalance = await bscProvider.getBalance(BSC_CONTRACT_OWNER_ADDRESS);

        const ethBalanceFormatted = ethers.utils.formatEther(ethBalance);
        const bscBalanceFormatted = ethers.utils.formatEther(bscBalance);

        const balancesLog = `
        Initial ETH Balance of Owner of Ethereum Chain Contracts: ${ethBalanceFormatted} ETH
        Initial BNB Balance of Owner of Binance Chain Contracts: ${bscBalanceFormatted} BNB
        `;

        fs.writeFileSync(resultsFilePath, balancesLog);

        // 3. Make the transfers
        stopMonitoringTestTransfers = monitorTransferLogs('./transfers.log',2*num_of_transfers);
        await makeTestTransfers(num_of_transfers);
        await waitForAllTransfersToComplete();
        stopMonitoringTestTransfers();
        // 4. Parse the transfers.log file to extract transfer request IDs and timestamps
        const logData = fs.readFileSync(logFilePath, 'utf8');
        const lines = logData.split('\n');

        const transferTimes = {};

        lines.forEach(line => {
            const completedMatch = line.match(/Transfer of \d+ tokens.*completed at \[(.*?)\] for the transfer request Id: (.*)/);
            const initiatedMatch = line.match(/Transfer initiated at \[(.*?)\] for the transfer request Id: (.*)/);

            if (initiatedMatch) {
                const [_, initiatedAt, requestId] = initiatedMatch;
                if (!transferTimes[requestId]) {
                    transferTimes[requestId] = { initiatedAt: new Date(initiatedAt).getTime() };
                }
            } else if (completedMatch) {
                const [_, completedAt, requestId] = completedMatch;
                if (transferTimes[requestId]) {
                    transferTimes[requestId].completedAt = new Date(completedAt).getTime();
                }
            }
        });

        // 5. Calculate and log the transfer times
        let totalTransferTime = 0;
        let transferCount = 0;
        const transferResults = [];

        for (const requestId in transferTimes) {
            const { initiatedAt, completedAt } = transferTimes[requestId];
            if (initiatedAt && completedAt) {
                const transferTime = completedAt - initiatedAt;
                totalTransferTime += transferTime;
                transferCount++;
                transferResults.push(`RequestId: ${requestId}, Transfer Time: ${transferTime / 1000} seconds`);
            }
        }

        fs.appendFileSync(resultsFilePath, '\nTransfer Times:\n' + transferResults.join('\n') + '\n');

        // 6. Calculate and log the average transfer time
        if (transferCount > 0) {
            const averageTransferTime = totalTransferTime / transferCount;
            fs.appendFileSync(resultsFilePath, `\nAverage Transfer Time: ${averageTransferTime / 1000} seconds\n`);
        }

        // 7. Fetch and log balances after transfers
        ethBalance = await ethProvider.getBalance(ETH_CONTRACT_OWNER_ADDRESS);
        bscBalance = await bscProvider.getBalance(BSC_CONTRACT_OWNER_ADDRESS);

        ethBalanceFormatted = ethers.utils.formatEther(ethBalance);
        bscBalanceFormatted = ethers.utils.formatEther(bscBalance);

        balancesLog = `
        Final ETH Balance of Owner of Ethereum Chain Contracts: ${ethBalanceFormatted} ETH
        Final BNB Balance of Owner of Binance Chain Contracts: ${bscBalanceFormatted} BNB
        `;
        fs.appendFileSync(resultsFilePath, balancesLog);
        // Once all transfers are done and result logs made, ensure the progress bar is completed
        completeProgressBar();
        process.exit(0); // Exit the process successfully
    } catch (error) {
        console.error("Error running ETH to BSC transfers:", error);
        // Stop monitoring logs in case of an error
        if (stopMonitoringInitialTransfers) stopMonitoringInitialTransfers();
        if (stopMonitoringTestTransfers) stopMonitoringTestTransfers();
        process.exit(1); // Exit the process with an error
    }
})(parseInt(process.argv[2], 10));

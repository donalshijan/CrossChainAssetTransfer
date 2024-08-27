const { ethers } = require("ethers");
const { transfer } = require("./transfer"); // Replace with the actual path to your transfer script
const { monitorInitialTransferLogs, waitForAllTransfersToComplete } = require('./monitorInitialTransfer.js');
require("dotenv").config();

// Number of times to perform the transfer
const NUM_TRANSFERS = 5;

// Addresses and amounts for testing
const ETH_CONTRACT_USER_ADDRESS = ethers.utils.getAddress(process.env.ETH_CONTRACT_USER_ADDRESS);
const BSC_CONTRACT_USER_ADDRESS = ethers.utils.getAddress(process.env.BSC_CONTRACT_USER_ADDRESS);
const ERC20_TOKEN_TO_TRANSFER_ADDRESS = ethers.utils.getAddress(process.env.ERC20_TOKEN_TO_TRANSFER_ADDRESS);

const AMOUNT = ethers.utils.parseUnits("0.01", 18); // The amount to transfer (replace with your desired amount)

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

            console.log(`Transfer ${i + 1} - ETH to BSC completed successfully.`);
        } catch (error) {
            console.error(`Error during ETH to BSC transfer ${i + 1}:`, error);
        }
    }

    console.log("All ETH to BSC transfers completed.");
}

// Run the transfer to populate BSC address with minted tokens
(async () => {
    let stopMonitoringInitialTransfers;
    try {
        // Start monitoring logs
        stopMonitoringInitialTransfers = monitorInitialTransferLogs('./path_to_your_log_file.log');
        await transferToPopulateBscAddressWithMintedTokens(NUM_TRANSFERS);
        // Wait until the transfer is confirmed
        await waitForAllTransfersToComplete();
        // Stop monitoring logs
        stopMonitoringInitialTransfers();
        process.exit(0); // Exit the process successfully
    } catch (error) {
        console.error("Error running ETH to BSC transfers:", error);
        // Stop monitoring logs in case of an error
        if (stopMonitoringInitialTransfers) stopMonitoringInitialTransfers();
        process.exit(1); // Exit the process with an error
    }
})();

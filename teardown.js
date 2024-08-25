const { ethers } = require("hardhat");
const minimist = require("minimist");

async function destroyContract(contractName, contractAddress) {
    const [deployer] = await ethers.getSigners();
    console.log(`Destroying ${contractName} contract at address:`, contractAddress);

    const ContractFactory = await ethers.getContractFactory(contractName);
    const contract = await ContractFactory.attach(contractAddress);

    // Call the destroyContract method
    let tx = await contract.destroyContract();
    await tx.wait();

    console.log(`${contractName} at ${contractAddress} has been destroyed.`);
}

async function teardownContractsForBSC() {
    // Destroy BEP20Mintable contract
    await destroyContract("BEP20Mintable", process.env.BEP20_CONTRACT_ADDRESS);

    // Destroy BurnTokensEscrow contract
    await destroyContract("BurnTokensEscrow", process.env.BURN_TOKENS_ESCROW_CONTRACT_ADDRESS);

    // Destroy BurnAndReleaseCoordinator contract
    await destroyContract("BurnAndReleaseCoordinator", process.env.BURN_AND_RELEASE_COORDINATOR_CONTRACT_ADDRESS);
}

async function teardownContractsForEthereum() {
    // Destroy ERC20Lock contract
    await destroyContract("ERC20Lock", process.env.ERC20_LOCK_CONTRACT_ADDRESS);
}

async function main() {
    const argv = minimist(process.argv.slice(2));
    const network = argv.network;

    if (network === "ethereum_sepolia") {
        await teardownContractsForEthereum();
    } else if (network === "bsc_testnet") {
        await teardownContractsForBSC();
    } else {
        console.log("Invalid network specified. Please choose 'ethereum_sepolia' or 'bsc_testnet'.");
        process.exit(1);
    }
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});

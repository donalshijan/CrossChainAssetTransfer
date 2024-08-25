const { ethers } = require("hardhat");
const minimist = require("minimist");

let burnTokenEscrowContractAddress; // Global variable for burnTokenEscrowContractAddress
let bep20ContractAddress; // Global variable for bep20ContractAddress

async function deployContract(contractName, constructorArgs, callback = null) {
    const [deployer] = await ethers.getSigners();
    console.log(`Deploying ${contractName} contract with account:`, deployer.address);

    const ContractFactory = await ethers.getContractFactory(contractName);
    const contract = await ContractFactory.deploy(...constructorArgs);
    await contract.deployed();

    console.log(`${contractName} deployed to:`, contract.address);
    // Verify the contract
    await verifyContract(contract.address, constructorArgs);
    // Run the callback function if provided
    if (callback) {
        await callback(contract);
    }

    return contract;
}

async function deployContractsForBSC() {
    bep20ContractAddress = (await deployContract("BEP20Mintable", [
        "Token Name",
        "TOKEN",
        ethers.utils.parseEther("0.01"),
        process.env.ETH_CONTRACT_OWNER_ADDRESS,
    ])).address;

    burnTokenEscrowContractAddress = (await deployContract("BurnTokensEscrow", [], async (burnTokensEscrowContract) => {
        // Get the BEP20Mintable contract
        const BEP20 = await ethers.getContractFactory("BEP20Mintable");
        const bep20Contract = await BEP20.attach(bep20ContractAddress);

        // Set the burn escrow token contract address in BEP20Mintable
        let tx = await bep20Contract.setBurnEscrowTokenContractAddress(burnTokensEscrowContract.address);
        await tx.wait();
        console.log("Burn escrow token contract address updated in BEP20 contract:", burnTokensEscrowContract.address);

        // Set the BEP20Mintable contract address in BurnTokensEscrow
        tx = await burnTokensEscrowContract.setBEP20TokenContractAddress(bep20ContractAddress);
        await tx.wait();
        console.log("BEP20Mintable contract address updated in BurnTokensEscrow contract:", bep20ContractAddress);

    })).address;

    await deployContract("BurnAndReleaseCoordinator", [burnTokenEscrowContractAddress]);
}

async function deployContractsForEthereum() {
    await deployContract("ERC20Lock", [
        ["0xTokenAddress1", "0xTokenAddress2"],
        ethers.utils.parseEther("0.01"),
        process.env.BSC_CONTRACT_OWNER_ADDRESS,
    ]);
}

async function verifyContract(contractAddress, constructorArguments) {
    console.log("Verifying contract at address:", contractAddress);
    console.log("Constructor arguments:", constructorArguments);

    const network = hre.network.name; // Get the current network name
    let apiKey;
    if (network === "ethereum_sepolia") {
        apiKey = process.env.ETHERSCAN_API_KEY;
    } else if (network === "bsc_testnet") {
        apiKey = process.env.BSCSCAN_API_KEY;
    }

    console.log(`Using API Key for ${network}:`, apiKey);
    try {
      await run("verify:verify", {
        address: contractAddress,
        constructorArguments: constructorArguments,
      });
      console.log("Contract verified!");
    } catch (error) {
      console.error("Verification failed:", error);
    }
  }

async function main() {
    const argv = minimist(process.argv.slice(2));
    const network = argv.network;

    if (network === "ethereum_sepolia") {
        await deployContractsForEthereum();
    } else if (network === "bsc_testnet") {
        await deployContractsForBSC();
    } else {
        console.log("Invalid network specified. Please choose 'ethereum_sepolia' or 'bsc_testnet'.");
        process.exit(1);
    }
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});

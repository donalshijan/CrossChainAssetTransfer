const { ethers } = require("hardhat");
const minimist = require("minimist");

async function deployERC20Lock() {
    const [deployer] = await ethers.getSigners();
    console.log("Deploying ERC20Lock contract with account:", deployer.address);

    const ERC20Lock = await ethers.getContractFactory("ERC20Lock");
    const tokenAddresses = ["0xTokenAddress1", "0xTokenAddress2"];
    const releaseFee = ethers.utils.parseEther("0.01"); 
    const bscContractOwner = process.env.BSC_CONTRACT_OWNER_ADDRESS;
    const erc20Lock = await ERC20Lock.deploy(tokenAddresses,releaseFee,bscContractOwner);
    await erc20Lock.deployed();
    console.log("ERC20Lock deployed to:", erc20Lock.address);

    await verifyContract(erc20Lock.address, [tokenAddresses, releaseFee, bscContractOwner]);
}
let bep20ContractAddress;
async function deployBEP20Mintable() {
    const [deployer] = await ethers.getSigners();
    console.log("Deploying BEP20Mintable contract with account:", deployer.address);

    const BEP20Mintable = await ethers.getContractFactory("BEP20Mintable");
    const mintFee = ethers.utils.parseEther("0.01"); 
    const bep20Mintable = await BEP20Mintable.deploy("Token Name", "TOKEN",mintFee,process.env.ETH_CONTRACT_OWNER_ADDRESS);
    await bep20Mintable.deployed();
    console.log("BEP20Mintable deployed to:", bep20Mintable.address);
    bep20ContractAddress=bep20Mintable.address;
    await verifyContract(bep20Mintable.address, ["Token Name", "TOKEN",mintFee,process.env.ETH_CONTRACT_OWNER_ADDRESS]);
}

let burnTokenEscrowContractAddress;
async function deployBurnTokensEscrow() {
    const [deployer] = await ethers.getSigners();
    console.log("Deploying BurnTokensEscrow contract with account:", deployer.address);

    const BURNTOKENSESCROW = await ethers.getContractFactory("BurnTokensEscrow");
    const BurnTokensEscrow = await BURNTOKENSESCROW.deploy();
    await BurnTokensEscrow.deployed();
    console.log("BurnTokensEscrow deployed to:", BurnTokensEscrow.address);
    burnTokenEscrowContractAddress=BurnTokensEscrow.address;
    await verifyContract(BurnTokensEscrow.address, []);

    // Get the BEP20 contract
    const BEP20 = await ethers.getContractFactory("BEP20Mintable"); // Replace with your BEP20 contract name
    const bep20Contract = await BEP20.attach(bep20ContractAddress); // Replace with the deployed BEP20 contract address

    // Call setBurnEscrowTokenContractAddress on the BEP20 contract to update the burn escrow address
    const tx = await bep20Contract.setBurnEscrowTokenContractAddress(burnTokenEscrowContractAddress);
    await tx.wait();

    console.log("Burn escrow token contract address updated in BEP20 contract:", burnTokenEscrowContractAddress);
    
    // Get the BurnTokensEscrow contract
    const burnTokensEscrowContract = await BURNTOKENSESCROW.attach(BurnTokensEscrow.address); // Replace with the deployed BEP20 contract address

    // Call setBEP20TokenContractAddress on the BurnTokensEscrow contract to update the burn escrow address
    tx = await burnTokensEscrowContract.setBEP20TokenContractAddress(bep20ContractAddress);
    await tx.wait();

    console.log("BEP20Mintable contract address updated in BurnTokensEscrow contract:", bep20ContractAddress);
}

async function deployBurnAndReleaseCoordinator() {
    const [deployer] = await ethers.getSigners();
    console.log("Deploying BurnAndReleaseCoordinator contract with account:", deployer.address);

    const BURNANDRELEASECOORDINATOR = await ethers.getContractFactory("BurnAndReleaseCoordinator");
    const BurnAndReleaseCoordinator = await BURNANDRELEASECOORDINATOR.deploy();
    await BurnAndReleaseCoordinator.deployed(burnTokenEscrowContractAddress);
    console.log("BurnTokensEscrow deployed to:", BurnAndReleaseCoordinator.address);
    await verifyContract(BurnAndReleaseCoordinator.address, [burnTokenEscrowContractAddress]);
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
        await deployERC20Lock();
    } else if (network === "bsc_testnet") {
        await deployBEP20Mintable();
        await deployBurnTokensEscrow();
        await deployBurnAndReleaseCoordinator();
    } else {
        console.log("Invalid network specified. Please choose 'ethereum_sepolia', or 'bscTestnet'.");
        process.exit(1);
    }
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});

const { ethers } = require("hardhat");

async function deployERC20Lock() {
    const [deployer] = await ethers.getSigners();
    console.log("Deploying ERC20Lock contract with account:", deployer.address);

    const ERC20Lock = await ethers.getContractFactory("ERC20Lock");
    const tokenAddresses = ["0xTokenAddress1", "0xTokenAddress2"];
    const erc20Lock = await ERC20Lock.deploy(tokenAddresses);
    await erc20Lock.deployed();
    console.log("ERC20Lock deployed to:", erc20Lock.address);
}

async function deployBEP20Mintable() {
    const [deployer] = await ethers.getSigners();
    console.log("Deploying BEP20Mintable contract with account:", deployer.address);

    const BEP20Mintable = await ethers.getContractFactory("BEP20Mintable");
    const bep20Mintable = await BEP20Mintable.deploy("Token Name", "TOKEN");
    await bep20Mintable.deployed();
    console.log("BEP20Mintable deployed to:", bep20Mintable.address);
}

async function main() {
    const network = process.env.NETWORK; 

    if (network === "ethereum_sepolia") {
        await deployERC20Lock();
    } else if (network === "bsc_testnet") {
        await deployBEP20Mintable();
    } else {
        console.log("Invalid network specified. Please choose 'ropsten', 'rinkeby', or 'bscTestnet'.");
        process.exit(1);
    }
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});

import { HardhatUserConfig } from "hardhat/config";
import "@nomicfoundation/hardhat-toolbox";

require('@nomiclabs/hardhat-ethers');
require('@nomiclabs/hardhat-etherscan'); // Import Etherscan plugin

if (!process.env.ETHERSCAN_API_KEY) {
  throw new Error("Missing ETHERSCAN_API_KEY in environment variables");
}

if (!process.env.BSCSCAN_API_KEY) {
  throw new Error("Missing BSCSCAN_API_KEY in environment variables");
}

const config: HardhatUserConfig = {
  solidity: "0.8.0",
  networks: {
    hardhat: {},
    ethereum_sepolia: {
      url: process.env.ETHEREUM_NODE_URL,
      accounts: [`0x${process.env.ETH_CONTRACT_OWNER_PRIVATE_KEY}`],
    },
    bsc_testnet: {
      url: process.env.BSC_NODE_URL,
      accounts: [`0x${process.env.BSC_CONTRACT_OWNER_PRIVATE_KEY}`],
    },
  },
  etherscan: {
    apiKey: {
      ethereum_sepolia: process.env.ETHERSCAN_API_KEY, // For Ethereum Sepolia testnet
      bsc_testnet: process.env.BSCSCAN_API_KEY, // For BSC testnet
    },
  }
};

export default config;

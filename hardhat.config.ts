import { HardhatUserConfig } from "hardhat/config";
import "@nomicfoundation/hardhat-toolbox";

const config: HardhatUserConfig = {
  solidity: "0.8.0",
  networks: {
    // hardhat: {
    //   chainId: 1337 // Default Hardhat local network chain ID
    // },
    // localhost: {
    //   url: "http://127.0.0.1:8545",
    //   chainId: 1337
    // },
    ethereum_sepolia: {
      url: process.env.ETHEREUM_NODE_URL,
      accounts: [`0x${process.env.ETH_CONTRACT_OWNER_PRIVATE_KEY}`],
    },
    bsc_testnet: {
      url: process.env.BSC_NODE_URL,
      accounts: [`0x${process.env.BSC_CONTRACT_OWNER_PRIVATE_KEY}`],
    },
  },
};

export default config;

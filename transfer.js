require("dotenv").config();
const { ethers } = require("ethers");

async function transfer(fromChain, from, to, amount, privateKey,tokenAddress) {
  let network;
  if (fromChain === "ethereum") {
    network = "sepolia";  // Specify Ethereum testnet, e.g., Goerli
  } else if (fromChain === "bsc") {
    network = "bscTestnet";  // Specify BSC testnet
  }

  const provider = ethers.getDefaultProvider(network);
  const wallet = new ethers.Wallet(privateKey, provider);

  if (fromChain === "ethereum") {
    const erc20Lock = new ethers.Contract(process.env.ERC20_LOCK_ADDRESS, abi, wallet);
    const tx = await erc20Lock.lockTokens(tokenAddress,amount, to);
    console.log(`Locked ${amount} tokens on Ethereum from ${from} to ${to}. TxHash: ${tx.hash}`);
  } else if (fromChain === "bsc") {
    const bep20Mintable = new ethers.Contract(process.env.BEP20_MINTABLE_ADDRESS, abi, wallet);
    const tx = await bep20Mintable.burn(from, amount, to);
    console.log(`Burned ${amount} tokens on BSC from ${from} to ${to}. TxHash: ${tx.hash}`);
  } else {
    console.log("Unsupported chain");
  }
}

const abi = [
  // ABI definitions for ERC20Lock and BEP20Mintable contracts
];

transfer("ethereum", "<fromAddress>", "<toAddress>", 1000, 'privatekey')
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });

const { ethers } = require("ethers");
const { v4: uuidv4 } = require('uuid');
const winston = require('winston');
const fs = require('fs');
const path = require('path');
require("dotenv").config();
const axios = require("axios");
const { acquireLock, releaseLock } = require('./filelock');

// Infura/Node URLs for Ethereum and Binance Smart Chain
const ETHEREUM_NODE_URL = process.env.ETHEREUM_NODE_URL;
const BSC_NODE_URL = process.env.BSC_NODE_URL;

// Private key and address of the account that will sign transactions
const ETH_CONTRACT_USER_PRIVATE_KEY = process.env.ETH_CONTRACT_USER_PRIVATE_KEY;
const BSC_CONTRACT_USER_PRIVATE_KEY = process.env.BSC_CONTRACT_USER_PRIVATE_KEY;

const ETH_CONTRACT_USER_ADDRESS = process.env.ETH_CONTRACT_USER_ADDRESS;
const BSC_CONTRACT_USER_ADDRESS = process.env.BSC_CONTRACT_USER_ADDRESS;

// Initialize providers and wallets
const ethProvider = new ethers.providers.JsonRpcProvider(ETHEREUM_NODE_URL);
const bscProvider = new ethers.providers.JsonRpcProvider(BSC_NODE_URL);

const ethWallet = new ethers.Wallet(ETH_CONTRACT_USER_PRIVATE_KEY, ethProvider);
const bscWallet = new ethers.Wallet(BSC_CONTRACT_USER_PRIVATE_KEY, bscProvider);

// ABI and contract addresses (Replace with actual ABI and contract addresses)
const ERC20_LOCK_ABI = loadABI('./artifacts/contracts/ERC20Lock.sol/ERC20Lock.json');  // Replace with the ABI of your ERC20Lock contract
const ERC20_LOCK_ADDRESS = process.env.ERC20_LOCK_ADDRESS;
const BEP20_ABI = loadABI('./artifacts/contracts/BEP20Mintable.sol/BEP20Mintable.json');  // Replace with the ABI of your BEP20Mintable contract
const BEP20_ADDRESS = process.env.BEP20_MINTABLE_ADDRESS;
const BURN_ESCROW_ADDRESS = process.env.BURN_ESCROW_ADDRESS;

const ERC20_TOKEN_TO_TRANSFER_ABI = [...];
const ERC20_TOKEN_TO_TRANSFER_ADDRESS = ethers.utils.getAddress(process.env.ERC20_TOKEN_TO_TRANSFER_ADDRESS);

const erc20TokenContract = new ethers.Contract(ERC20_TOKEN_TO_TRANSFER_ADDRESS, ERC20_TOKEN_TO_TRANSFER_ABI, ethWallet);
const erc20LockContract = new ethers.Contract(ERC20_LOCK_ADDRESS, ERC20_LOCK_ABI, ethWallet);
const bep20Contract = new ethers.Contract(BEP20_ADDRESS, BEP20_ABI, bscWallet);

// Setup logger with a lockfile
const logFilePath = './transfers.log';

// Helper function to load ABI from a JSON file
function loadABI(filePath) {
  const jsonContent = fs.readFileSync(path.resolve(__dirname, filePath), 'utf8');
  const contractJson = JSON.parse(jsonContent);
  return contractJson.abi;
}

// Ensure the log file exists
if (!fs.existsSync(logFilePath)) {
    fs.writeFileSync(logFilePath, '');
}

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
      winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
      winston.format.printf(info => `${info.timestamp} - ${info.level.toUpperCase()}: ${info.message}`)
  ),
  transports: [
      new winston.transports.File({ filename: logFilePath })
  ]
});

function logMessage(message) {
  acquireLock((err, acquired) => {
    if (err) {
      console.error('Failed to acquire lock:', err);
      return;
    }

    if (acquired) {
      // Log the message once the lock is acquired
      logger.info(message);

      // Release the lock after logging
      releaseLock((err) => {
        if (err) {
          console.error('Failed to release lock:', err);
        }
      });
    } else {
      console.log('Lock is held by another process. Retrying...');
      setTimeout(() => logMessage(message), 1000); // Retry after 1 second
    }
  });
}
async function approveTransfer(contract, method, spender, amount) {
    const tx = await contract[method](spender, amount);
    const receipt = await tx.wait();
    console.log(`Tokens Approved. TxHash: ${receipt.transactionHash}`);
    return receipt;
}

async function payMintFee(toAddress, mintFee) {
    const timestamp = Math.floor(Date.now() / 1000);
    const receiptId = `${toAddress}-${timestamp}`;

    // Make the transaction to pay the mint fee
    const tx = await bep20Contract.payMintFee(timestamp, {
        from: toAddress,
        value: ethers.utils.parseEther(mintFee.toString()),  // Replace with the actual mint fee in ether
        gasLimit: 2000000,
        gasPrice: ethers.utils.parseUnits('20', 'gwei'),
    });

    console.log(`Mint fee transaction sent. Hash: ${tx.hash}`);
    await tx.wait();

    // Poll for the receipt using the receipt_id via HTTP request
    const url = `http://localhost:8000/collect/`;
    const payload = { receipt_id: receiptId };

    while (true) {
        try {
            const response = await axios.post(url, payload);
            if (response.status === 200) {
                console.log(`Receipt found: ${JSON.stringify(response.data)}`);
                return response.data;
            } else {
                console.log("Receipt not found, polling again in 5 seconds...");
            }
        } catch (error) {
            console.log(`Error during the HTTP request: ${error.message}`);
        }
        await new Promise(resolve => setTimeout(resolve, 5000));
    }
}

async function payReleaseFee(toAddress, releaseFee) {
    const timestamp = Math.floor(Date.now() / 1000);
    const receiptId = `${toAddress}-${timestamp}`;

    const tx = await erc20LockContract.payReleaseFee(timestamp, {
        from: toAddress,
        value: ethers.utils.parseEther(releaseFee.toString()),
        gasLimit: 2000000,
        gasPrice: ethers.utils.parseUnits('20', 'gwei'),
    });

    console.log(`Release Fee Paid. TxHash: ${tx.hash}`);
    await tx.wait();

    // Poll for the receipt using the receipt_id via HTTP request
    const url = `http://localhost:8000/collect/`;
    const payload = { receipt_id: receiptId };

    while (true) {
        try {
            const response = await axios.post(url, payload);
            if (response.status === 200) {
                console.log(`Receipt found: ${JSON.stringify(response.data)}`);
                return response.data;
            } else {
                console.log("Receipt not found, polling again in 5 seconds...");
            }
        } catch (error) {
            console.log(`Error during the HTTP request: ${error.message}`);
        }
        await new Promise(resolve => setTimeout(resolve, 5000));
    }
}

async function transferTokens(fromChainUserAddress, toChainUserAddress, amount, direction, receipt, tokenContractAddress) {
  const transferRequestId = uuidv4(); // Generate a UUID
    if (direction === "eth_to_bsc") {
        const { feeAmount, nonce, contractAddress, receipt: receiptSignature } = receipt;

        const tx = await erc20LockContract.lockTokens(tokenContractAddress, amount, toChainUserAddress, feeAmount, nonce, contractAddress, receiptSignature, transferRequestId,{
            from: fromChainUserAddress,
            gasLimit: 2000000,
            gasPrice: ethers.utils.parseUnits('20', 'gwei'),
        });

        const timestamp = new Date().toISOString();
        console.log(`Tokens Lock called on Ethereum. TxHash: ${tx.hash}`);
        console.log(`Token Transfer for ${amount} tokens of ${tokenContractAddress} from Ethereum  address ${fromChainUserAddress} to Binance  address ${toChainUserAddress} initiated at [${timestamp}] with Transfer request id [${transferRequestId}]`)
        logMessage(`Token Transfer for ${amount} tokens of ${tokenContractAddress} from Ethereum  address ${fromChainUserAddress} to Binance  address ${toChainUserAddress} initiated at [${timestamp}] with Transfer request id [${transferRequestId}]`);
        await tx.wait();

    } else if (direction === "bsc_to_eth") {
        const { feeAmount, nonce, contractAddress, receipt: receiptSignature } = receipt;

        const coordinatorFee = await bep20Contract.coordinatorFee();

        const tx = await bep20Contract.burn(fromChainUserAddress, amount, toChainUserAddress, tokenContractAddress, feeAmount, nonce, contractAddress, receiptSignature, transferRequestId,{
            from: fromChainUserAddress,
            value: coordinatorFee,
            gasLimit: 2000000,
            gasPrice: ethers.utils.parseUnits('5', 'gwei'),
        });

        const timestamp = new Date().toISOString();
        console.log(`Tokens Burn called on BSC. TxHash: ${tx.hash} at [${timestamp}]`);
        console.log(`Token Transfer for ${amount} tokens from Binance  address ${fromChainUserAddress} to Ethereum  address ${toChainUserAddress} into   ${tokenContractAddress} tokens initiated at [${timestamp}] with Transfer request id [${transferRequestId}]`)
        logMessage(`Token Transfer for ${amount} tokens from Binance  address ${fromChainUserAddress} to Ethereum  address ${toChainUserAddress} into   ${tokenContractAddress} tokens initiated at [${timestamp}] with Transfer request id [${transferRequestId}]`)
        await tx.wait();
    }
}

async function transfer(fromAddress, toAddress, amount, direction, tokenContractAddress) {
    if (direction === "eth_to_bsc") {
        await approveTransfer(erc20TokenContract, 'approve', ERC20_LOCK_ADDRESS, amount);
        const mintFee = await bep20Contract.mintFee();  // Get the mint fee
        const receipt = await payMintFee(toAddress, mintFee);
        await transferTokens(fromAddress, toAddress, amount, direction, receipt, tokenContractAddress);
    } else if(direction=="bsc_to_eth"){
        await approveTransfer(bep20Contract, 'approve', BURN_ESCROW_ADDRESS, amount);
        const releaseFee = await erc20LockContract.releaseFee();  // Get the release fee
        const receipt = await payReleaseFee(toAddress, releaseFee);
        await transferTokens(fromAddress, toAddress, amount, direction, receipt, tokenContractAddress);
    }
    else{
        console.log('Invalid direction')
    }
}

(async () => {
  try {
      const fromAddress = ethers.utils.getAddress(ETH_CONTRACT_USER_ADDRESS);
      const toAddress = ethers.utils.getAddress(BSC_CONTRACT_USER_ADDRESS);
      const amount = ethers.utils.parseUnits("0.01", 18);
      const direction = "eth_to_bsc";
      const tokenContractAddress = ethers.utils.getAddress(ERC20_TOKEN_TO_TRANSFER_ADDRESS);

      await transfer(fromAddress, toAddress, amount, direction, tokenContractAddress);
      process.exit(0); // Exit the process successfully
  } catch (error) {
      console.error(error);
      process.exit(1); // Exit the process with an error
  }
})();

module.exports = {
  transfer,
};

const { EventEmitter } = require('events');
const fs = require('fs');
const path = require('path');
const { updateProgressBar } = require('./progressTracker'); // Import the progress tracker
// Event emitter for monitoring logs
const logMonitor = new EventEmitter();

// Map to track the completion status of each transfer request
const transferStatusMap = new Map();




// Function to monitor log files for transfer events
function monitorTransferLogs(logFilePath,num_of_transfers) {
    transferStatusMap.clear();
    
    let logStream;

    function startReadingLog() {
        logStream = fs.createReadStream(logFilePath, { encoding: 'utf8', flags: 'r' });

        logStream.on('data', (chunk) => {
            const lines = chunk.split('\n');
            for (const line of lines) {
                const initiatedMatch = line.match(/Token Transfer .* initiated .* Transfer request id \[(\w+)\]/);
                if (initiatedMatch) {
                    const transferRequestId = initiatedMatch[1];
                    transferStatusMap.set(transferRequestId, false);
                    console.log(`Transfer initiated: ${transferRequestId}`);
                    continue;
                }

                const completedMatch = line.match(/Transfer .* completed .* Transfer request id: (\w+)/);
                if (completedMatch) {
                    const transferRequestId = completedMatch[1];
                    if (transferStatusMap.has(transferRequestId)) {
                        transferStatusMap.set(transferRequestId, true);
                        updateProgressBar(); // Update the progress bar
                        console.log(`Transfer completed: ${transferRequestId}`);
                        checkIfAllCompleted(num_of_transfers);
                    }
                    continue;
                }
            }
        });

        logStream.on('end', () => {
            console.log('End of log file reached. Waiting for new data...');
            setTimeout(startReadingLog, 1000); // Reopen the stream after a short delay
        });
    }
    startReadingLog();
    return () => {
        logStream.close();  // Stop reading the log file
    };
}

// Function to check if all transfers are completed
function checkIfAllCompleted(num_of_transfers) {
    if (transferStatusMap.size !== num_of_transfers) {
        return; // If the number of transfers doesn't match, exit the function
    }
    const allCompleted = Array.from(transferStatusMap.values()).every(status => status === true);
    if (allCompleted) {
        console.log("All transfers completed.");
        logMonitor.emit('allTransfersCompleted');
    }
}

// Function to wait until all transfers are completed
function waitForAllTransfersToComplete() {
    return new Promise((resolve) => {
        logMonitor.once('allTransfersCompleted', resolve);
    });
}

module.exports = {
    monitorTransferLogs,
    waitForAllTransfersToComplete,
};

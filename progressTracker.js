const cliProgress = require('cli-progress');

let progressBar;
let completedTransfers = 0;
let totalTransfers = 0;

// Initialize the progress bar with the total number of transfers
function initializeProgressBar(num_of_transfers) {
    totalTransfers = num_of_transfers * 3+1; // 3 times the number of transfers
    progressBar = new cliProgress.SingleBar({}, cliProgress.Presets.shades_classic);
    progressBar.start(totalTransfers, 0);
}

// Update the progress bar when a transfer is completed
function updateProgressBar() {
    completedTransfers++;
    if (progressBar) {
        progressBar.update(completedTransfers);
    }
}

// Stop the progress bar when all transfers are complete
function completeProgressBar() {
    if (progressBar) {
        progressBar.update(totalTransfers); // Ensure progress bar is complete
        progressBar.stop();
    }
}

// Export the functions and variables
module.exports = {
    initializeProgressBar,
    updateProgressBar,
    completeProgressBar,
};

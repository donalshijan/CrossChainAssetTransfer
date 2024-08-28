#!/bin/bash

# Function to handle script termination (Ctrl+C)
cleanup() {
    echo "Stopping service.py..."
    kill %1  # Stops the service.py process
    exit 0
}

# Trap SIGINT (Ctrl+C) and call cleanup function
trap cleanup SIGINT

# Step 1: Navigate to the TransferServiceOracle directory and start the service
cd TransferServiceOracle || { echo "Directory TransferServiceOracle not found."; exit 1; }
echo "Starting the Transfer Service..."
python3 service.py &

# Step 2: Navigate back to the root directory (assuming the script is run from there)
cd ..

# Step 3: Check and create the necessary log files if they do not exist
LOG_FILE="./transfers.log"
LOCK_FILE="./transfers.log.lock"
RESULTS_FILE="./testPerformanceAndCostEvaluationResults.txt"

if [ ! -f "$LOG_FILE" ]; then
    touch "$LOG_FILE"
    echo "Created $LOG_FILE"
else
    echo "$LOG_FILE already exists."
fi

if [ ! -f "$LOCK_FILE" ]; then
    touch "$LOCK_FILE"
    echo "Created $LOCK_FILE"
else
    echo "$LOCK_FILE already exists."
fi

if [ ! -f "$RESULTS_FILE" ]; then
    touch "$RESULTS_FILE"
    echo "Created $RESULTS_FILE"
else
    echo "$RESULTS_FILE already exists."
fi

# Step 4: Start the testTransfer.js script in a new process
echo "Starting the testTransfer.js script..."
node testTransfer.js &

# Wait for testTransfer.js to finish (we don't wait for service.py)
wait %2  # Wait for the second background job (testTransfer.js)

echo "testTransfer.js has completed."

# At this point, the script will keep running, allowing the user to press Ctrl+C to stop service.py
echo "service.py is still running. Press Ctrl+C to stop it when you're ready."

# Keep the script running so the user can manually stop service.py with Ctrl+C
while true; do
    sleep 1  # Infinite loop to keep the script running
done


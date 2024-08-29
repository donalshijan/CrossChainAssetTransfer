#!/bin/bash

num_of_transfers=10

# Function to handle script termination (Ctrl+C)
cleanup() {
    echo "Stopping service.py..."
    kill $SERVICE_PID  # Stops the service.py process
    exit 0
}

# Trap SIGINT (Ctrl+C), SIGHUP, and SIGTERM signals to call cleanup functio
trap cleanup SIGINT SIGHUP SIGTERM

# Step 1: Navigate to the TransferServiceOracle directory and start the service
cd TransferServiceOracle || { echo "Directory TransferServiceOracle not found."; exit 1; }
echo "Starting the Transfer Service..."
python3 service.py &
SERVICE_PID=$!
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
node testTransfer.js $num_of_transfers &
TEST_PID=$!
# Wait for testTransfer.js to finish (we don't wait for service.py)
wait $TEST_PID  

echo "testTransfer.js has completed."

# Inform the user that service.py is still running
echo "service.py is still running. Press Ctrl+C to stop it when you're ready."

# Keep the script running so the user can manually stop service.py with Ctrl+C
# Infinite loop to keep the script running until the user manually stops service.py
while kill -0 $SERVICE_PID 2>/dev/null; do
    sleep 1
done


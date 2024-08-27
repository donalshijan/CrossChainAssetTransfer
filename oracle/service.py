import threading
import signal
import sys
import logging
import os
from feeEstimator import poll_fee_updates
from receiptGenerator import start_event_listeners
from relayer import listen_and_relay

# Global variables to hold the threads
fee_thread = None
receipt_thread = None
relayer_thread = None
stop_flag = threading.Event()

def setup_logger(log_file=None):
    logger = logging.getLogger('Relayer')
    logger.setLevel(logging.INFO)
    
    # Create a formatter and set it for both handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    
    # If a log file is specified, add a file handler
    if log_file:
        # Get the current working directory
        current_dir = os.getcwd()
        
        # Construct the full path to the log file
        log_file_path = os.path.join(current_dir, log_file)
        
        # Ensure the log file exists
        if not os.path.isfile(log_file_path):
            with open(log_file_path, 'w'):  # Create the file
                pass
        
        # Add the file handler
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    else:
        return None
    return logger

# Function to stop all services
def stop_services():
    print("\nStopping services...")
    # Signal the threads to stop
    stop_flag.set()
    # Implement any necessary cleanup or stop logic for each service here
    if fee_thread:
        fee_thread.do_run = False  # Assuming the threads are designed to check this flag
    if receipt_thread:
        receipt_thread.do_run = False
    if relayer_thread:
        relayer_thread.do_run = False
    
    # Optionally wait for threads to finish
    if fee_thread:
        fee_thread.join()
    if receipt_thread:
        receipt_thread.join()
    
    print("All services stopped.")

# Function to handle the Ctrl+C signal (SIGINT)
def signal_handler(sig, frame):
    stop_services()
    sys.exit(0)

def start_services():
    global fee_thread, receipt_thread, relayer_thread
    
    # Starting the feeEstimator Service in a new thread
    fee_thread = threading.Thread(target=poll_fee_updates, args=(600,), daemon=True)
    fee_thread.start()

    # Starting receiptGenerator Service in a new thread
    receipt_thread = threading.Thread(target=start_event_listeners, daemon=True)
    receipt_thread.start()

    logger = setup_logger(log_file='relayer.log')
    # Starting relayer Service in a new thread
    relayer_thread = threading.Thread(target=lambda: listen_and_relay(logger), daemon=True)
    relayer_thread.start()

if __name__ == "__main__":
    # Set up the signal handler to catch Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    start_services()
    
    # Keeping the main thread running to listen for user input or Ctrl+C
    print("Services are running. Press Ctrl+C to stop.")
    
    # Optionally keep the script running with a loop
    try:
        while True:
            # Keep the main thread alive, could be waiting for user input or other actions
            input()
    except KeyboardInterrupt:
        stop_services()

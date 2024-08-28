import os
import time

log_file_path = './transfers.log'
lock_file_path = log_file_path + '.lock'
lock_timeout = 30  # Timeout in seconds

def acquire_lock():
    current_pid = os.getpid()
    
    if os.path.isfile(lock_file_path):
        with open(lock_file_path, 'r') as f:
            lock_timestamp, pid = f.read().splitlines()
            lock_age = time.time() - float(lock_timestamp)
            
            # Check if the PID is the same as the current process's PID
            if int(pid) == current_pid:
                #print("Current process already holds the lock.")
                return True  # The current process already holds the lock
            
            if lock_age < lock_timeout:
                #print("Lock file exists and is still valid.")
                return False  # Another process holds the lock and it's still valid

    # Acquire the lock by writing the current timestamp and PID
    with open(lock_file_path, 'w') as f:
        f.write(f"{time.time()}\n{current_pid}")
    return True

def release_lock():
    if os.path.isfile(lock_file_path):
        os.remove(lock_file_path)



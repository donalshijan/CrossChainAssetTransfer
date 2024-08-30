import os
import time
import errno

log_file_path = './transfers.log'
lock_file_path = log_file_path + '.lock'
lock_timeout = 5  # Timeout in seconds

def acquire_lock():
    current_pid = os.getpid()
    
    try:
        # Use O_CREAT and O_EXCL to ensure atomic creation of the lock file
        fd = os.open(lock_file_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, 'w') as f:
            f.write(f"{time.time()}\n{current_pid}")
        return True
    except OSError as e:
        if e.errno == errno.EEXIST:
            # The lock file already exists; check if it's still valid
            with open(lock_file_path, 'r') as f:
                lock_timestamp, pid = f.read().splitlines()
                lock_age = time.time() - float(lock_timestamp)

                if int(pid) == current_pid:
                    return True  # The current process already holds the lock

                if lock_age < lock_timeout:
                    return False  # Another process holds the lock and it's still valid

                # Acquire the lock by writing the current timestamp and PID
                with open(lock_file_path, 'w') as f:
                    f.write(f"{time.time()}\n{current_pid}")
                return True

def release_lock():
    if os.path.isfile(lock_file_path):
        os.remove(lock_file_path)



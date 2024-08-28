const fs = require('fs');

const logFilePath = './transfers.log';
const lockFilePath = logFilePath + '.lock';
const lockTimeout = 30000; // Timeout in milliseconds


  function acquireLock(callback) {
    const currentPid = process.pid;
  
    fs.readFile(lockFilePath, 'utf8', (err, data) => {
        if (err && err.code !== 'ENOENT') {
          // Return error if there's an issue reading the file, except if the file doesn't exist (ENOENT)
          callback(err, false);
          return;
        }
    
        if (!err) {
          const [timestamp, pid] = data.split('\n');
          const lockAge = Date.now() - parseFloat(timestamp);
    
          if (parseInt(pid) === currentPid) {
            callback(null, true); // Current process already holds the lock
            return;
          } else if (lockAge < lockTimeout) {
            callback(null, false); // Another process holds the lock and it's still valid
            return;
          }
        }
    
        // Acquire the lock by writing the current timestamp and PID
        fs.writeFile(lockFilePath, `${Date.now()}\n${currentPid}`, (err) => {
          callback(err, err === null);
        });
      });
    }

    function releaseLock(callback) {
        fs.unlink(lockFilePath, (err) => {
          if (err) {
            if (err.code === 'ENOENT') {
              // The lock file doesn't exist, so no need to delete it
              callback(null);
            } else {
              callback(err); // Handle other possible errors
            }
          } else {
            callback(null); // Successfully released the lock
          }
        });
      }
      

module.exports = {
  acquireLock,
  releaseLock,
};
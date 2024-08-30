const fs = require('fs');

const logFilePath = './transfers.log';
const lockFilePath = logFilePath + '.lock';
const lockTimeout = 5000; // Timeout in milliseconds


function acquireLock(callback) {
  const currentPid = process.pid;

  // Try to atomically create the lock file
  fs.open(lockFilePath, 'wx', (err, fd) => {
      if (err) {
          if (err.code === 'EEXIST') {
              // Lock file already exists, read its contents
              fs.readFile(lockFilePath, 'utf8', (err, data) => {
                  if (err) {
                      callback(err, false);
                      return;
                  }

                  const [timestamp, pid] = data.split('\n');
                  const lockAge = Date.now() - parseFloat(timestamp);

                  if (parseInt(pid) === currentPid) {
                      callback(null, true); // Current process already holds the lock
                  } else if (lockAge < lockTimeout) {
                      callback(null, false); // Another process holds the lock and it's still valid
                  } else {
                      // Lock is stale, overwrite the file with the current PID and timestamp
                      fs.writeFile(lockFilePath, `${Date.now()}\n${currentPid}`, (err) => {
                          callback(err, err === null);
                      });
                  }
              });
          } else {
              console.log('Unexpected Error')
              callback(err, false); // An unexpected error occurred
          }
      } else {
          // Successfully created the lock file
          fs.write(fd, `${Date.now()}\n${currentPid}`, (err) => {
              if (err) {
                  callback(err, false);
              } else {
                  callback(null, true);
              }
              fs.close(fd, () => {}); // Close the file descriptor
          });
      }
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
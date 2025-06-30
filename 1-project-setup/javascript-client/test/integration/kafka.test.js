const { expect } = require('chai');
const net = require('net');
const { execSync } = require('child_process');

describe('Kafka Service Integration Tests', () => {
  const KAFKA_HOST = 'kafka';
  const KAFKA_PORT = 9092;
  const TOPIC = process.env.KAFKA_TOPIC || 'test';
  const GROUP_ID = process.env.GROUP_ID || 'javascriptconsumer';
  const BOOTSTRAP_SERVERS = process.env.BOOTSTRAP_SERVERS;
  const WAIT_MESSAGE_TIMEOUT = 15000;

  const waitForService = async (host, port, timeout = 5000) => {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();
      const tryConnect = () => {
        const socket = new net.Socket();
        socket.on('error', () => {
          socket.destroy();
          if (Date.now() - startTime > timeout) {
            reject(new Error(`Service ${host}:${port} not available`));
          } else {
            setTimeout(tryConnect, 1000);
          }
        });
        socket.on('connect', () => {
          socket.destroy();
          resolve();
        });
        socket.connect(port, host);
      };
      tryConnect();
    });
  };

  const getContainerLogs = async (container) => {
    try {
      // Use container names instead of service names
      const containerName = {
        'consumer': 'kafka-consumer',
        'producer': 'kafka-producer'
      }[container] || container;
      
      const logs = execSync(`docker logs ${containerName} 2>&1`).toString();
      return logs;
    } catch (error) {
      console.error(`Error getting logs from ${container}:`, error.message);
      return '';
    }
  };

  const waitForPattern = async (container, pattern, maxRetries = 30, interval = 1000) => {
    let retries = 0;
    while (retries < maxRetries) {
      try {
        const logs = await getContainerLogs(container);
        if (logs.includes(pattern)) {
          return true;
        }
      } catch (error) {
        console.log(`Retry ${retries + 1}/${maxRetries}: Waiting for pattern "${pattern}" in ${container}`);
      }
      
      await new Promise(resolve => setTimeout(resolve, interval));
      retries++;
    }
    throw new Error(`Pattern "${pattern}" not found in ${container} logs after ${maxRetries} retries`);
  };

  it('should verify producer connection', async function() {
    this.timeout(90000);
    // First check for JSON-formatted log
    await waitForPattern('producer', 'message: \'Producer connected\'');
    // Then check for plain text confirmation
    await waitForPattern('producer', 'Connected successfully');
    console.log('✅ Producer is connected');
  });

  it('should verify message flow', async function() {
    this.timeout(90000);
    await waitForPattern('producer', 'Sent message');
    console.log('✅ Producer sent message');
    
    await waitForPattern('consumer', 'Received message:');
    console.log('✅ Consumer received message');
  });
});

import os
import socket
import time
import docker
import subprocess
from typing import Optional
import asyncio
import pytest

KAFKA_HOST = 'kafka'
KAFKA_PORT = 9092
TOPIC = os.getenv('KAFKA_TOPIC', 'test')
GROUP_ID = os.getenv('GROUP_ID', 'pythonconsumer')
BOOTSTRAP_SERVERS = os.getenv('BOOTSTRAP_SERVERS')
WAIT_MESSAGE_TIMEOUT = 15000

def wait_for_service(host: str, port: int, timeout: int = 5000) -> None:
    """Wait for a service to become available."""
    start_time = time.time()
    while True:
        try:
            with socket.create_connection((host, port), timeout=1.0):
                return
        except (socket.timeout, ConnectionRefusedError):
            if (time.time() - start_time) * 1000 > timeout:
                raise TimeoutError(f"Service {host}:{port} not available")
            time.sleep(1)

def get_container_logs(container: str) -> str:
    """Get logs from a Docker container."""
    try:
        container_name = {
            'consumer': 'kafka-consumer',
            'producer': 'kafka-producer'
        }.get(container, container)
        
        client = docker.from_env()
        container = client.containers.get(container_name)
        return container.logs().decode('utf-8')
    except docker.errors.NotFound as e:
        print(f"Container {container_name} not found: {e}")
        return ''
    except Exception as e:
        print(f"Error getting logs from {container}: {e}")
        return ''

async def wait_for_pattern(container: str, pattern: str, max_retries: int = 30, interval: float = 1.0) -> bool:
    """Wait for a pattern to appear in container logs."""
    for retry in range(max_retries):
        try:
            logs = get_container_logs(container)
            logs_oneline = ' '.join(logs.splitlines())
            if pattern in logs_oneline:
                return True
        except Exception as e:
            print(f"Retry {retry + 1}/{max_retries}: Waiting for pattern '{pattern}' in {container}")
        
        await asyncio.sleep(interval)
    
    raise TimeoutError(f"Pattern '{pattern}' not found in {container} logs after {max_retries} retries")

@pytest.mark.timeout(90)

@pytest.mark.asyncio
async def test_message_flow():
    """Verify message flow between producer and consumer."""
    
    await wait_for_pattern('producer', 'Produced event to topic \'test\'')
    print('✅ Producer sent message')
    
    await wait_for_pattern('consumer', 'Received message')
    print('✅ Consumer received message')

@pytest.fixture(autouse=True)
async def setup_kafka():
    """Setup Kafka connection before tests."""
    try:
        wait_for_service(KAFKA_HOST, KAFKA_PORT)
        print('✅ Kafka broker is accessible')
        yield
    except Exception as e:
        pytest.fail(f"Failed to connect to Kafka: {e}")

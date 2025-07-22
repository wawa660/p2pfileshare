
import os
import hashlib
import requests
import socket
from flask import Flask, request, send_from_directory

# Configuration
TRACKER_URL = "http://127.0.0.1:5000"
CHUNK_SIZE = 1024 * 1024  # 1MB
DOWNLOAD_DIR = "downloads"

app = Flask(__name__)

def get_my_ip():
    """Get the local IP address of the machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

MY_ADDRESS = f"http://{get_my_ip()}:5001"

@app.route('/download/<file_hash>/<int:chunk_index>')
def download_chunk(file_hash, chunk_index):
    """Serves a specific chunk of a file."""
    file_path = os.path.join(DOWNLOAD_DIR, file_hash)
    if not os.path.exists(file_path):
        return "File not found", 404

    return send_from_directory(DOWNLOAD_DIR, f"{file_hash}_{chunk_index}")

def register_file(file_path):
    """Registers a file with the tracker."""
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return

    file_hash = hashlib.sha1(open(file_path, 'rb').read()).hexdigest()
    
    # Create chunks
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    with open(file_path, 'rb') as f:
        chunk_index = 0
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            with open(os.path.join(DOWNLOAD_DIR, f"{file_hash}_{chunk_index}"), 'wb') as chunk_file:
                chunk_file.write(chunk)
            chunk_index += 1

    data = {
        "file_hash": file_hash,
        "peer_address": MY_ADDRESS
    }
    try:
        response = requests.post(f"{TRACKER_URL}/register", json=data)
        response.raise_for_status()
        print(f"Successfully registered file {file_hash} with the tracker.")
    except requests.exceptions.RequestException as e:
        print(f"Error registering file with tracker: {e}")

def download_file(file_hash):
    """Downloads a file from peers."""
    try:
        response = requests.get(f"{TRACKER_URL}/query/{file_hash}")
        response.raise_for_status()
        data = response.json()
        peers = data.get("peers", [])
    except requests.exceptions.RequestException as e:
        print(f"Error querying tracker: {e}")
        return

    if not peers:
        print("No peers found for this file.")
        return

    print(f"Found {len(peers)} peers: {peers}")

    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    # For simplicity, we'll try to download from the first peer
    # A more robust client would try multiple peers
    peer_address = peers[0]
    
    # We need to know how many chunks to download.
    # This information should ideally be part of the tracker's response.
    # For now, we'll assume a fixed number of chunks for simplicity.
    # A better approach would be to get the file size from the tracker or a peer.
    num_chunks = 10 # Placeholder

    with open(os.path.join(DOWNLOAD_DIR, file_hash), 'wb') as f:
        for i in range(num_chunks):
            try:
                chunk_url = f"{peer_address}/download/{file_hash}/{i}"
                print(f"Downloading chunk {i} from {chunk_url}")
                response = requests.get(chunk_url, stream=True)
                response.raise_for_status()
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            except requests.exceptions.RequestException as e:
                print(f"Error downloading chunk {i}: {e}")
                # Try another peer if available
                break
    print("File download complete.")

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python client.py [register|download] [file_path|file_hash]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "register":
        if len(sys.argv) < 3:
            print("Usage: python client.py register [file_path]")
            sys.exit(1)
        file_to_register = sys.argv[2]
        register_file(file_to_register)
        # Start the Flask app to serve chunks
        app.run(host='0.0.0.0', port=5001)

    elif command == "download":
        if len(sys.argv) < 3:
            print("Usage: python client.py download [file_hash]")
            sys.exit(1)
        hash_to_download = sys.argv[2]
        download_file(hash_to_download)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


import os
import hashlib
import requests
import socket
from flask import Flask, request, send_from_directory

# Config
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
    # Construct the chunk file name as stored during registration
    chunk_file_name = f"{file_hash}_{chunk_index}"
    chunk_path = os.path.join(DOWNLOAD_DIR, chunk_file_name)

    if not os.path.exists(chunk_path):
        return "Chunk not found", 404

    return send_from_directory(DOWNLOAD_DIR, chunk_file_name)

def register_file(file_path):
    """Registers a file with the tracker."""
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return

    file_size = os.path.getsize(file_path)
    file_hash = hashlib.sha1(open(file_path, 'rb').read()).hexdigest()
    num_chunks = (file_size + CHUNK_SIZE - 1) // CHUNK_SIZE

    # Create and save chunks
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    with open(file_path, 'rb') as f:
        for i in range(num_chunks):
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            chunk_filename = f"{file_hash}_{i}"
            with open(os.path.join(DOWNLOAD_DIR, chunk_filename), 'wb') as chunk_file:
                chunk_file.write(chunk)

    data = {
        "file_hash": file_hash,
        "peer_address": MY_ADDRESS,
        "file_size": file_size,
        "num_chunks": num_chunks
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
        num_chunks = data.get("num_chunks")

    except requests.exceptions.RequestException as e:
        print(f"Error querying tracker: {e}")
        return

    if not peers or num_chunks is None:
        print("No peers found for this file or file info is incomplete.")
        return

    print(f"Found {len(peers)} peers: {peers}")

    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    # For simplicity, we'll try to download from the first peer
    peer_address = peers[0]

    # Assemble the file from chunks
    final_file_path = os.path.join(DOWNLOAD_DIR, file_hash)
    with open(final_file_path, 'wb') as f:
        for i in range(num_chunks):
            try:
                chunk_url = f"{peer_address}/download/{file_hash}/{i}"
                print(f"Downloading chunk {i+1}/{num_chunks} from {chunk_url}")
                response = requests.get(chunk_url, stream=True)
                response.raise_for_status()
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            except requests.exceptions.RequestException as e:
                print(f"Error downloading chunk {i}: {e}")
                # In a real client, you would try another peer here.
                print("Download failed.")
                # Clean up partially downloaded file
                if os.path.exists(final_file_path):
                    os.remove(final_file_path)
                return

    print(f"File download complete. Saved as {final_file_path}")

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
        # Run the Flask app in a separate thread to serve chunks
        import threading
        flask_thread = threading.Thread(target=app.run, kwargs={'host':'0.0.0.0', 'port':5001})
        flask_thread.daemon = True
        flask_thread.start()
        
        register_file(file_to_register)
        
        # Keep the main thread alive to allow the Flask server to run
        try:
            while True:
                pass
        except KeyboardInterrupt:
            print("Client shutting down.")

    elif command == "download":
        if len(sys.argv) < 3:
            print("Usage: python client.py download [file_hash]")
            sys.exit(1)
        hash_to_download = sys.argv[2]
        download_file(hash_to_download)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

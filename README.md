
# Peer-to-Peer (P2P) File Sharing App

This project is a simplified implementation of a peer-to-peer file sharing system. It consists of a central tracker server and a peer client that can both download and upload files.

## How it Works

### 1. Tracker

The tracker is a central server that keeps track of which peers have which files. It does not store any files itself, but rather the mapping between a file's hash and the IP addresses of the peers that have it.

- **Registration:** When a peer wants to share a file, it first calculates the SHA1 hash of the file. It then sends a request to the tracker to register itself as a peer for that file hash.
- **Querying:** When a peer wants to download a file, it queries the tracker with the file's hash. The tracker responds with a list of IP addresses of peers who have the file.

### 2. Peer Client

The peer client is the application that runs on each user's machine. It has two main functionalities:

- **Sharing (Uploading):** A user can choose a file to share. The client will then:
    1. Calculate the file's SHA1 hash.
    2. Register the file with the tracker, associating the file hash with its own IP address.
    3. Break the file into smaller, 1MB chunks.
    4. Run a local web server to serve these chunks to other peers.

- **Downloading:** A user can download a file by providing its SHA1 hash. The client will then:
    1. Query the tracker to get a list of peers who have the file.
    2. Connect to one of the peers from the list.
    3. Download the file chunks one by one from the peer.
    4. Reassemble the chunks into the original file.

## How to Deploy

### Prerequisites

- Python 3.x
- Flask (`pip install Flask`)
- Requests (`pip install requests`)

### 1. Start the Tracker

On a server with a public IP address, run the following command:

```bash
python tracker.py
```

The tracker will start listening on port 5000.

### 2. Share a File

On your local machine, open a terminal and run the following command to share a file:

```bash
python client.py register /path/to/your/file
```

This will register the file with the tracker and start a local server on port 5001 to serve the file chunks.

### 3. Download a File

On another machine, open a terminal and run the following command to download the file:

```bash
python client.py download <file_hash>
```

Replace `<file_hash>` with the SHA1 hash of the file you want to download. You can get this hash from the output of the `register` command.

## Limitations and Future Improvements

This is a simplified implementation and has several limitations:

- **Centralized Tracker:** The tracker is a single point of failure. A more robust system would use a decentralized tracker (e.g., a DHT).
- **Peer Selection:** The client currently downloads from the first peer in the list returned by the tracker. A better client would download from multiple peers simultaneously to increase download speed.
- **Chunk Discovery:** The client currently assumes a fixed number of chunks. The number of chunks should be retrieved from the tracker or from a peer.
- **Security:** There is no verification of file chunks. A malicious peer could send a corrupted chunk.
- **Firewall/NAT Traversal:** The current implementation assumes that peers are directly reachable. In a real-world scenario, NAT traversal techniques (e.g., STUN/TURN) would be needed.

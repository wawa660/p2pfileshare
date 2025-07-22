
from flask import Flask, request, jsonify
import json

app = Flask(__name__)

# In-memory database to store file and peer information
db = {}

@app.route('/register', methods=['POST'])
def register_peer():
    """
    Registers a peer with a file.
    """
    data = request.get_json()
    file_hash = data.get('file_hash')
    peer_address = data.get('peer_address')

    if not file_hash or not peer_address:
        return jsonify({"error": "Missing file_hash or peer_address"}), 400

    if file_hash not in db:
        db[file_hash] = []

    if peer_address not in db[file_hash]:
        db[file_hash].append(peer_address)

    return jsonify({"message": "Peer registered successfully."})

@app.route('/query/<file_hash>', methods=['GET'])
def query_peers(file_hash):
    """
    Returns a list of peers who have the specified file.
    """
    if file_hash in db:
        return jsonify({"peers": db[file_hash]})
    else:
        return jsonify({"error": "File not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


from flask import Flask, request, jsonify
import sqlite3
import json

app = Flask(__name__)

# --- Database Setup ---
DB_NAME = 'tracker.db'

def get_db():
    conn = sqlite3.connect(DB_NAME)
    return conn

def create_tables():
    conn = get_db()
    cursor = conn.cursor()
    # Create files table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            file_hash TEXT PRIMARY KEY,
            file_size INTEGER NOT NULL,
            num_chunks INTEGER NOT NULL
        )
    ''')
    # Create peers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS peers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_hash TEXT NOT NULL,
            peer_address TEXT NOT NULL,
            FOREIGN KEY (file_hash) REFERENCES files (file_hash),
            UNIQUE (file_hash, peer_address)
        )
    ''')
    conn.commit()
    conn.close()

# --- Routes ---

@app.route('/register', methods=['POST'])
def register_peer():
    """
    Registers a peer with a file.
    """
    data = request.get_json()
    file_hash = data.get('file_hash')
    peer_address = data.get('peer_address')
    file_size = data.get('file_size')
    num_chunks = data.get('num_chunks')

    if not all([file_hash, peer_address, file_size is not None, num_chunks is not None]):
        return jsonify({"error": "Missing required data"}), 400

    conn = get_db()
    cursor = conn.cursor()
    try:
        # Use INSERT OR IGNORE to avoid errors if the file already exists.
        cursor.execute("INSERT OR IGNORE INTO files (file_hash, file_size, num_chunks) VALUES (?, ?, ?)",
                       (file_hash, file_size, num_chunks))

        # Use INSERT OR IGNORE to avoid errors if the peer is already registered for the file.
        cursor.execute("INSERT OR IGNORE INTO peers (file_hash, peer_address) VALUES (?, ?)",
                       (file_hash, peer_address))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
        return jsonify({"error": "Database error"}), 500
    finally:
        conn.close()

    return jsonify({"message": "Peer registered successfully."})

@app.route('/query/<file_hash>', methods=['GET'])
def query_peers(file_hash):
    """
    Returns a list of peers who have the specified file, and file metadata.
    """
    conn = get_db()
    cursor = conn.cursor()

    # Get file info
    cursor.execute("SELECT file_size, num_chunks FROM files WHERE file_hash = ?", (file_hash,))
    file_info_row = cursor.fetchone()

    if not file_info_row:
        conn.close()
        return jsonify({"error": "File not found"}), 404

    file_size, num_chunks = file_info_row

    # Get peers
    cursor.execute("SELECT peer_address FROM peers WHERE file_hash = ?", (file_hash,))
    peers = [row[0] for row in cursor.fetchall()]
    conn.close()

    if peers:
        return jsonify({
            "peers": peers,
            "file_size": file_size,
            "num_chunks": num_chunks
        })
    else:
        # This case should ideally not happen if file_info was found, but as a safeguard:
        return jsonify({"error": "File not found or no peers available"}), 404

if __name__ == '__main__':
    create_tables()
    app.run(host='0.0.0.0', port=5000)

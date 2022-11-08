import string
import random
import hashlib
import os
import errno
import json

# Function to generate a random string
def generate_random_string(length):
    st = (''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length)))
    return st

# Function to read the sha1 hash to a string
def generate_sha1(st):
    hash = hashlib.sha1(st.encode("utf-8")).hexdigest()
    return hash

# Function to crate a directory
def create_dir(dir_name):
    try:
        os.mkdir(dir_name)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

# Function to verify if a directory-file exists
def verify_file(path):
    try:
        file = open(path)
        print(file) 
        file.close()
        return True
    except FileNotFoundError:
        return False

# Function to read the contents of a directory-file
def read_file(dir):
    f = open(dir, "r")
    t = f.read()
    t = json.loads(t) 
    f.close()
    return t

# Function to write the information of the node in a JSON file
def write_data_server(dir, mac):
    f = open (dir, 'w')
    node_id = mac + generate_random_string(30)
    hash = generate_sha1(node_id)
    hash_int = int(hash, 16)
    data_server = {
        "id": hash_int,
        "id_mac": node_id,
        "hash": hash,
        "joined": False
    }
    f.write(json.dumps(data_server))
    f.close()

# Function to write info in a file
def write_info(info, dir):
    f = open (dir, 'w')
    f.write(json.dumps(info))
    f.close()    
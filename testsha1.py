import hashlib
import os

def generate_file_sha1(filename, blocksize=2**20):
    m = hashlib.sha1()
    with open( os.path.join(filename) , "rb" ) as f:
        while True:
            buf = f.read(blocksize)
            if not buf:
                break
            m.update( buf )
    return m.hexdigest()

print(generate_file_sha1("client/Server_filehalf.bin"))

import uuid
import string
import random
import hashlib
import os
import errno
  
mac =  (':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) 
for ele in range(0,8*6,8)][::-1]))

def generate_random_string(length):
    st = (''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length)))
    return st

#Function to read the sha1 hash to a string
def generate_sha1(st):
    hash = hashlib.sha1(st.encode("utf-8")).hexdigest()
    return hash

NODE_ID = mac + generate_random_string(30)

print(NODE_ID)


try:
    os.mkdir('dir1')
except OSError as e:
    if e.errno != errno.EEXIST:
        raise
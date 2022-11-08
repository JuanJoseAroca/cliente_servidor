import zmq
import os
import hashlib
import sys
import math
import json

context = zmq.Context()

IP_NODE, PORT_NODE = sys.argv[1], sys.argv[2]

#Request types -> file, file_validation, id_assignment

#  Socket to talk to the kown node
print("Connecting to server...")

pool = {}
socket = context.socket(zmq.REQ)
con = "tcp://" + IP_NODE + ":" + PORT_NODE
socket.connect(con)

pool.update({IP_NODE + ":" + PORT_NODE: socket})

# Socket to talk to server
socket2 = context.socket(zmq.REQ)

#Function to calculate the size of the chunks
def calculate_chunk_size(file_size):

    #Less than 1 megabyte, 100 kilobytes chunks
    if file_size < 1048576:
        chunk_size = 102400
    #Less than 50 megabytes, 1 megabyte chunks    
    elif file_size <  52428800:
        chunk_size = 1048576
    #Bigger than 50 megabytes, 10 megabytes chunks   
    else:
        chunk_size = 10485760

    return chunk_size 

#Function to read the sha1 hash
def generate_file_sha1(filename, blocksize=2**20):
    m = hashlib.sha1()
    with open( os.path.join(filename) , "rb" ) as f:
        while True:
            buf = f.read(blocksize)
            if not buf:
                break
            m.update( buf )
    return m.hexdigest()

# Create a file if doesn't exist
def create_file(file_name, type):
    try:
        f = open (file_name, 'r')
        f.close()
    except:
        if type == "list":
            f = open (file_name, 'wb')
        elif type == "dic":
            f = open (file_name, 'wb')
            f.write(json.dumps({}).encode('utf-8'))

        f.close()

# reads the content of a file and turns it into a json
def read_lines(dir):
    f = open(dir, "r")
    lines = f.readlines()
    t = []
    for line in lines:
        t.append(json.loads(line)) 
    f.close()
    
    return t

def read_file(dir):
    f = open(dir, "r")
    t = f.read()
    t = json.loads(t) 
    f.close()
    return t

# Function to write info in a file
def write_info(info, dir):
    f = open (dir, 'w')
    f.write(json.dumps(info))
    f.close()  

# Function to load a file to the servers
def load_file(user_name, file_name, data_files, data_nodes):

    
    connect = IP_NODE + ":" + PORT_NODE
    file_size = os.path.getsize(file_name)

    chunk_size = calculate_chunk_size(file_size)
    n_files = math.ceil(file_size/chunk_size)

    print("Calculando sha1, por favor espere...")
    readable_hash = generate_file_sha1(file_name)

    files = []
    file_number = 0
    with open(file_name, 'rb') as f:
        chunk = f.read(chunk_size)
        while chunk:
            percent = (file_number/n_files)*100
            print("Porcentaje subido:", percent, "%")
            file = str(file_number) + file_name
            files.append(file)

            with open(file, 'wb') as chunk_file:
                chunk_file.write(chunk)
                fi = open (file, 'rb')
                bytes = fi.read() # read file as bytes
                readable_hash_segment = hashlib.sha1(bytes).hexdigest()
                fi.close()
                extension = os.path.splitext(file)[1]
                file_name_server = readable_hash_segment + extension
                int_readable_hash_segment = int(readable_hash_segment, 16)
                int_readable_hash_segment = str(int_readable_hash_segment)

                # Send request to any node    
                pool[connect].send_multipart(["chunk".encode('utf-8'), int_readable_hash_segment.encode('utf-8')])
                
                info = pool[connect].recv_json()

                print(info["answer"]["answer"])

                while info["answer"]["answer"] == "ask my succesor":
                    connect = info["answer"]["connection"]
                    print(connect)
                    if not(connect in pool):
                        s = context.socket(zmq.REQ)
                        s.connect("tcp://" +  connect)

                        pool.update({connect: s})

                    pool[connect].send_multipart(["chunk".encode('utf-8'), 
                                            int_readable_hash_segment.encode('utf-8')])
                    data_nodes.update(
                        {connect: info["range"]}
                    )

                    write_info(data_nodes, "nodes.json")                                                
                    info = pool[connect].recv_json()   

                if info["answer"]["answer"] == "you can save in":
                    print("saved")
  
                    pool[connect].send_multipart(["save-chunk".encode('utf-8'), 
                                            int_readable_hash_segment.encode('utf-8'), 
                                            file_name_server.encode('utf-8'),
                                            bytes,
                                            user_name.encode('utf-8')])

                    data_nodes.update(
                        {connect: info["range"]}
                    )

                    write_info(data_nodes, "nodes.json")


                    info = pool[connect].recv_json()
                    
                    print(info)
                   
                    seg_info = {"file_name": file_name,
                        "hash_file": readable_hash,
                        "chunk_name": file_name_server,
                        "server_con": connect,
                        "order": file_number,
                        "int_hash": int(int_readable_hash_segment)}
                    
                    data_files.append(seg_info)

                    fi = open ("files.json", 'ab')
                    fi.write((json.dumps(seg_info) + "\n").encode("utf-8"))
                    fi.close()

                    
                        
            files.remove(file)
            os.remove(file)   
            file_number += 1
            chunk = f.read(chunk_size)


    for file in files:
        os.remove(file)

# Function to download a file from servers
def download_file(user_name, file_name, data_files, data_nodes):
    joined_files = []
    for file in data_files:
        counter_files = 0
        if file["file_name"] == file_name:
            counter_files += 1
            found = False
            for connection in data_nodes:
                range = data_nodes[connection]
                if ((file["int_hash"] > range[0]) and (file["int_hash"] <= range[1])) or (file["int_hash"] <= range[2]):
                    if not(connection in pool):
                        s = context.socket(zmq.REQ)
                        s.connect("tcp://" +  connection)
                        pool.update({connection: s})
                    
                    pool[connection].send_multipart(["get-chunk".encode('utf-8'), 
                                            file["chunk_name"].encode('utf-8')])
                    
                    answer = pool[connection].recv_multipart()

                    while(answer[0].decode() == "not-found"):
                        connection = answer[1].decode()
                        if not(connection in pool):
                            s = context.socket(zmq.REQ)
                            s.connect("tcp://" +  connection)
                            pool.update({connection: s})
                        
                        pool[connection].send_multipart(["get-chunk".encode('utf-8'), 
                                            file["chunk_name"].encode('utf-8')])
                        
                        answer = pool[connection].recv_multipart()    


                    if answer[0].decode() == "found":
                        found = True
                        if not(file["chunk_name"] in joined_files):
                            with open("Server_" + file_name, "ab") as client_file:
                                    client_file.write(answer[1])
                                    joined_files.append(file["chunk_name"])
                  

            # In case we have any node to connect that actually have the correct range
            if not(found):
                connection = IP_NODE + ":" + PORT_NODE
                pool[connection].send_multipart(["get-chunk".encode('utf-8'), 
                                            file["chunk_name"].encode('utf-8')])
                    
                answer = pool[connection].recv_multipart()

                while(answer[0].decode() == "not-found"):
                    connection = answer[1].decode()
                    if not(connection in pool):
                        s = context.socket(zmq.REQ)
                        s.connect("tcp://" +  connection)
                        pool.update({connection: s})
                    
                    pool[connection].send_multipart(["get-chunk".encode('utf-8'), 
                                        file["chunk_name"].encode('utf-8')])
                    
                    answer = pool[connection].recv_multipart()    


                if answer[0].decode() == "found":
                        found = True
                        if not(file["chunk_name"] in joined_files):
                            with open("Server_" + file_name, "ab") as client_file:
                                    client_file.write(answer[1])
                                    joined_files.append(file["chunk_name"])


#Driver
if __name__ == "__main__":
    create_file("files.json", "list")
    create_file("nodes.json", "dic")

    files = read_lines("files.json")
    nodes = read_file("nodes.json")


    user_name = input("Escriba su nombre de usuario: ")

    print('''
        ------ Menú ------
        1). Subir archivo
        2). Descargar archivo
        3). Salir
    ''')

    option = input("Escoja una opción: ")

    while option != "1" and option != "2" and option != "3":
        option = input("Por favor seleccione una alternativa 1 o alternativa 2: ")

    file_name = input("Por favor escriba el nombre del archivo: ")


    if option == "1":
        load_file(user_name, file_name, files, nodes)
    elif option == "2":
        download_file(user_name, file_name, files, nodes)
    elif option == "3":
        exit()             


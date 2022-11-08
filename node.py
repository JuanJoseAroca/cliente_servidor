import zmq
import argparse
import socket as sk
import uuid
import time
from utilities import *
from shutil import rmtree
import copy
import os

# Construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-p", "--port", required=True, help="port of this server")
ap.add_argument("-f", "--folder", required=True, help="name of the folder")
ap.add_argument("-c", "--connect", help="connection")
ap.add_argument("-fs", "--firstserver", help="first server")
args = vars(ap.parse_args())

# Arguments -> port where is going to listen, path
PORT, NAME = args["port"], args["folder"]

# Sockets
context = zmq.Context()

# Socket where is to do a reuest to another node
socket1 = context.socket(zmq.REQ)

# Socket where is going to listen another node
socket2 = context.socket(zmq.REP)
socket2.bind("tcp://*:" +  PORT)

# IP address
s = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
IP = s.getsockname()[0]

# MAC address
MAC =  (':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) 
for ele in range(0,8*6,8)][::-1]))

# Path --> Windows (\\) Linux (//)
SLASH = "\\"
PATH = NAME + SLASH
CON = IP + ":" + PORT


# Function to join the server to a ring
def join_server(connection, data_server):
    print("Connecting to server...")
    socket1.connect("tcp://" + connection)

    data = json.dumps(data_server)
    socket1.send_multipart(["New-server".encode("utf8"), CON.encode("utf8"), data.encode("utf-8")])

    info = socket1.recv_json()

    if info["answer"] == "Server joined":
        data_server.update({
            "succesor_id": info["succesor"],
            "succesor_connection": info["connection"],
            "joined": True,
            "range1": info["range1"],
            "range2": info["range2"],
            "range3": info["range3"],
            "firstserver": False,
            "alone": False,
            "files": []
        })
    
        write_info(data_server, PATH + "data_server.json")

    elif info["answer"] == "Comunicate succesor":
        join_server(info["connection"], data_server)


# Function to establish the ring and put the server
def establish(data_server):
    data_server.update({"range1": data_server["id"], 
                        "range2": (2 ** 160) - 1, 
                        "range3": data_server["id"],
                        "succesor_id": data_server["id"], 
                        "succesor_connection": CON, 
                        "joined": True,
                        "firstserver": True,
                        "alone": True,
                        "files": []})
    write_info(data_server, PATH + "data_server.json")
        

# Driver
if __name__ == "__main__":
    create_dir(NAME)

    if not(verify_file(PATH + "data_server.json")):
        write_data_server(PATH + "data_server.json", MAC)
        data_server = read_file(PATH + "data_server.json")
        
    else:
        try:
            data_server = read_file(PATH + "data_server.json")
        except:
            write_data_server(PATH + "data_server.json", MAC)
            data_server = read_file(PATH + "data_server.json")
        

    if not(data_server["joined"]) and ((args["firstserver"] == None or args["firstserver"] == "n") and (args["connect"] == None)):
        print("Por favor debe ingresar los parametros para unirse a un anillo o para establecerlo")
        print("Saliendo...")
        rmtree(NAME)
        time.sleep(3)
        exit()

    elif (data_server["joined"]) and ((args["firstserver"] == None or args["firstserver"] == "n") and (args["connect"] == None)):    
        pass
    
    elif args["firstserver"] != None and args["firstserver"] != "n":
        print("Estableciendo servidor...")
        establish(data_server)

    else:
        print("Conectando con:", args["connect"])
        join_server(args["connect"], data_server)      

    while True:

        info = socket2.recv_multipart()
        
        # Add new server
        if info[0].decode() == "New-server":
            data_entry_node = info[2].decode()
            data_entry_node = json.loads(data_entry_node)

            # Is succesor
            if ((data_entry_node["id"] > data_server["id"]) and (data_entry_node["id"] <= data_server["range2"])) or ((data_entry_node["id"] > 0) and (data_entry_node["id"] <= data_server["range3"])):

                if ((data_entry_node["id"] > data_server["id"]) and (data_entry_node["id"] <= data_server["range2"])):
                    print("uniendo sucesor...")
                    socket2.send_json({
                        "answer": "Server joined",
                        "succesor": data_server["succesor_id"],
                        "connection": data_server["succesor_connection"],
                        "range1": data_entry_node["id"],
                        "range2": data_server["range2"],
                        "range3": data_server["range3"]                 
                        })

                    socket1 = context.socket(zmq.REQ)
                    socket1.connect("tcp://" + info[1].decode())
                    for file in data_server["files"]:
                        for ele in file:
                            n_hash = file[ele]

                            if (n_hash > data_entry_node["id"] and n_hash <= data_server["range2"]):
                                if verify_file(PATH + ele):
                                    fi = open (PATH + ele, 'rb')
                                    bytes = fi.read()
                                    fi.close()

                                    
                                    socket1.send_multipart(["save-chunk".encode('utf-8'),
                                                            str(file[ele]).encode('utf-8'), 
                                                            ele.encode('utf-8'),
                                                            bytes])

                                    socket1.recv_json()                        

                                    os.remove(PATH + ele)                        


                    data_server.update({
                        "succesor_id": data_entry_node["id"],
                        "succesor_connection": info[1].decode(),
                        "range1": data_server["id"],
                        "range2": data_entry_node["id"],
                        "range3": 0

                    })

                    

                elif (data_entry_node["id"] > 0) and (data_entry_node["id"] <= data_server["range3"]):
                    print("uniendo sucesor desde el otro lado...")
                    socket2.send_json({
                    "answer": "Server joined",
                    "succesor": data_server["id"],
                    "connection": data_server["succesor_connection"],
                    "range1": data_entry_node["id"],
                    "range2": data_server["succesor_id"],
                    "range3": 0                   
                    })

                    socket1 = context.socket(zmq.REQ)
                    socket1.connect("tcp://" + info[1].decode())
                    for file in data_server["files"]:
                        for ele in file:
                            n_hash = file[ele]

                            if (n_hash > data_entry_node["id"] and n_hash <= data_server["range2"]):
                                if verify_file(PATH + ele):
                                    fi = open (PATH + ele, 'rb')
                                    bytes = fi.read()
                                    fi.close()
                                    
                                    socket1.send_multipart(["save-chunk".encode('utf-8'),
                                                            str(file[ele]).encode('utf-8'), 
                                                            ele.encode('utf-8'),
                                                            bytes])
                                    socket1.recv_json()

                                    os.remove(PATH + ele)



                    data_server.update({
                        "range1": data_server["id"],
                        "succesor_id": data_entry_node["id"],
                        "succesor_connection": info[1].decode(),
                        "range3": data_entry_node["id"]
                        })

                
                if data_server["firstserver"] and data_server["alone"]:
                    data_server.update({"alone": False})

                write_info(data_server, PATH + "data_server.json")
   
            else:
                print("pasando sucesor")
                socket2.send_json({
                    "answer": "Comunicate succesor",
                    "connection": data_server["succesor_connection"]
                    })

        # Verifies if a chunk could be saved by this node 
        elif info[0].decode() == "chunk":
            file_name = info[1].decode()
            print("recibido", file_name)
            hash = int(info[1].decode())

            if ((hash > data_server["range1"]) and (hash <= data_server["range2"])) or (hash <= data_server["range3"]):

                answer = {"answer": "you can save in"}
            else:
                answer =  {"answer": "ask my succesor", "connection": data_server["succesor_connection"]}    
            #Send reply back to client
            socket2.send_json({"answer": answer, 
                               "range": [data_server["range1"], data_server["range2"], data_server["range3"]
                               ]
                               })

        # Save a chunk
        elif info[0].decode() == "save-chunk":
            filename = info[2].decode()
            print(filename)
            f = open (PATH + filename, 'wb')
            f.write(info[3])
            f.close()
            hash = int(info[1].decode())
            fi = data_server["files"]
            fi.append({filename: hash})

            data_server.update({
                "files": fi
            })

            print(data_server)
            write_info(data_server, PATH + "data_server.json")
            socket2.send_json({"answer": "saved"})

        elif info[0].decode() == "get-chunk":
            filename = info[1].decode()

            if verify_file(PATH + filename):
                fi = open (PATH + filename, 'rb')
                bytes = fi.read()
                socket2.send_multipart(["found".encode("utf-8"), bytes])
                print("solicitud de segmento", filename)
            else:
                suc = str(copy.copy(data_server["succesor_connection"]))
                socket2.send_multipart(["not-found".encode("utf-8"), suc.encode("utf-8")])
                   

        # For an invalid request by clients or nodes
        else:
            socket2.send_json({"Not-found": "invalid request"})
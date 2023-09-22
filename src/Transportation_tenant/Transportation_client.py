''' This code is based on the example provided at https://hackernoon.com/creating-command-line-based-chat-room-using-python-oxu3u33 '''

import socket
import threading
import logging
from pathlib import Path


from config_transportation_client import config as client_config

# Set up the logger
logfile_path = client_config["logging"]["baseConfig"]["filename"]
if not Path(logfile_path).is_file():
    Path(logfile_path).parent.resolve().mkdir(parents=True, exist_ok=True)

logging.basicConfig(**client_config["logging"]["baseConfig"])
transport_client_logger = logging.getLogger(name="transport_client_logger")

# Connect the client to the server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((client_config["chat_server"]["host"], client_config["chat_server"]["port"]))
transport_client_logger.info(msg=f"{client_config['name']}:\n Sent connection request to host {client_config['chat_server']['host']} and port {client_config['chat_server']['port']}.")

def receive():
    """This function continuously checks for received messages and acts on some of them automatically.
    """
    try:
        while True:
            msg = client.recv(1024).decode(client_config["chat_server"]["encoding"])
            # If asked for a password, send the password from the config.
            if msg == "_Password":
                client.send(client_config["chat_server"]["password"].encode(client_config["chat_server"]["encoding"]))
                transport_client_logger.info(msg=f"{client_config['name']}:\n Sent password.")
                continue
            # If asked for a name, send the name from the config
            elif msg == "_Name":
                client.send(client_config["name"].encode(client_config["chat_server"]["encoding"]))
                transport_client_logger.info(msg=f"{client_config['name']}:\n Sent name.")
                continue
            # Show other messages to the user
            print(msg)
    # If the connection to the server is lost (ConnectionResetError) or the client is
    # already shut down (OSError), terminate the process.
    except (ConnectionResetError, OSError) as e:
        terminate_client(error=e)
        return

def write():
    """This function continuously checks for new inputs from the user and sends them
    to the server.
    """
    try:
        while True:
            msg = input("")
            client.send(msg.encode(client_config["chat_server"]["encoding"]))
            transport_client_logger.info(msg=f"{client_config['name']}:\n Sent message:\n {msg}.")
    # If the connection to the server is lost (ConnectionResetError) or the client is
    # already shut down (OSError), terminate the process.
    except (ConnectionResetError, OSError) as e:
        terminate_client(error=e)
        return

def terminate_client(error):
    """This function terminates the client upon an error. It disables the sending and
    receiving functionality and closes the socket. A specific handling of the error is
    currently only supported for ConnectionResetError.

    :param error: The error, which caused the termination
    :type error: Any
    """
    if isinstance(error, ConnectionResetError):
        client.shutdown(socket.SHUT_RDWR)
        client.close()
        transport_client_logger.info(msg=f"Client terminated due to {error}.")

# Start the receiving thread
receive_thread = threading.Thread(target=receive)
receive_thread.start()
transport_client_logger.info(msg=f"{client_config['name']}:\n Started receiving thread.")

# Start the writing thread
write_thread = threading.Thread(target=write)
write_thread.start()
transport_client_logger.info(msg=f"{client_config['name']}:\n Started writing thread.")
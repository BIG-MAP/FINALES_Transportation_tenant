''' The chat functionality is based on an example provided here: https://hackernoon.com/creating-command-line-based-chat-room-using-python-oxu3u33 '''

from FINALES2.tenants.referenceTenant import Tenant
from FINALES2.schemas import GeneralMetaData, Quantity, ServerConfig, Method
from FINALES2.user_management.classes_user_manager import User
from FINALES2.engine.main import RequestStatus, ResultStatus
from config_transportation_tenant import config as tenant_config


from datetime import datetime
import time
import requests
from typing import Any, Union
import logging
from pathlib import Path

import socket
import threading
from passlib.context import CryptContext

crypto_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Set up the logger
logfile_path = tenant_config["logging"]["baseConfig"]["filename"]
if not Path(logfile_path).is_file():
    Path(logfile_path).parent.resolve().mkdir(parents=True, exist_ok=True)

logging.basicConfig(**tenant_config["logging"]["baseConfig"])
transport_tenant_logger = logging.getLogger(name="transport_tenant_logger")

# Set the allowed origins and destinations, which are used to define the limitations
origins_list = [
            {
                "address": "KIT HIU Ulm",
                "detail_1": "ASAB",
                "detail_2": f"vial_{i}"
            } for i in range(1, 9)
            ] + [
            {
                "address": "KIT HIU Ulm",
                "detail_1": "AutoBASS",
                "detail_2": f"Tray: {j}"
            } for j in range(1, 65)
            ]

destinations_list = [
            {
                "address": "KIT HIU Ulm",
                "detail_1": "AutoBASS",
                "detail_2": f"Tray: {k}"
            } for k in range(1, 65)
            ] + [
                {
                    "address": "KIT HIU Ulm",
                    "detail_1": "Cycler",
                    "detail_2": f"Channel: {k}"
                } for k in range(1, 25)
            ] 


# Prepare all the elements required to instantiate the tenant
transport_method = Method(
    name = "transport_service",
    quantity = "transport",
    parameters = ["origin", "destination"],
    limitations = {
        "origin": origins_list,
        "destination": destinations_list
    }
)

transport_quantities = {
    "transport": Quantity(
        name = "transport",
        methods = {"transport_service": transport_method},
        is_active = True
    )
}

def tranport_run(request_info: dict[str, Any]) -> str:
    """This function sends a message to the chat about a pending request

    :param request_info: The request containing the information about the origin and 
                         the destination of the transport
    :type request_info: dict[str, Any]
    :return message: A string representing the message, which is supposed to be shared
    :rtype: str
    """
    message = f"\n\n Pending request with ID {request_info['uuid']} is waiting for transport.\n Pick it up at {request_info['request']['parameters']['transport_service']['origin']} \n and bring it to {request_info['request']['parameters']['transport_service']['destination']}\n\n"
    transport_tenant_logger.info(msg=message)
    return message


def transport_prepare_results(request:dict, data:str) -> dict:
    """This function prepares the result to be posted to the FINALES server

    :param request: The request containing all the info about the requested transport
    :type request: dict
    :param data: The message sent to the chat by the user
    :type data: str
    :return formatted_result: A dictionary containing the result formatted for posting
    :rtype: dict
    """
    # Split the message to access the information relevant for the post
    execution_details = data["message"].split(";")
    # Try to get the information about the actual new location, if it is there
    try:
        actual_location_list = execution_details[2].lstrip("{").rstrip("}").split("\"")
        actual_location = {
        "address": actual_location_list[3],
        "detail_1": actual_location_list[7],
        "detail_2": actual_location_list[11]
      }
    # If no actual new location is provided in the message, assume, that the requested
    # destination was used
    except IndexError:
        actual_location = request['request']['parameters']['transport_service']['destination']
    # Assemble the result
    result_data = {
      "success": "%DONE" in data["message"],
      "actual_new_location": actual_location,
      "executant": data["executant"]
    }

    # Wrap it into the FINALES result structure
    formatted_result = {
        "data": result_data,
        "quantity": "transport",
        "method": [
            "transport_service"
        ],
        "parameters": request["request"]['parameters'],
        "tenant_uuid": "",
        "request_uuid": request["uuid"]
    }
    transport_tenant_logger.info(msg=f"formatted result: \n {formatted_result}")
    return formatted_result


class Tenant_custom(Tenant):
    """This class is a customized version of the FINALES Tenant class

    :param Tenant: The Tenant class as implemented in FINALES
    :type Tenant: Tenant
    :return: No returns
    :rtype: None
    """
    informed_queue:dict = {}    # The queue containing all the requests, for which a message was already sent to the chat
    clients:dict = {}   # A dictionary containing all the clients connected to the chat server (names are keys, sockets are values)
    chat_host:str = tenant_config["chat_server"]["host"]    # The host of the chat server
    chat_port:int = tenant_config["chat_server"]["port"]    # The port of the chat server
    chat_server:Union[Any, None] = None # The chat server instance (socket.socket as a type is not accepted by pydantic)

    def send_message_to_all(self, message:str):
        """This function sends a message to all the clients connected to the server.

        :param message: A string representing the message to be shared
        :type message: str
        """
        # Get the list of clients
        clients_list = list(self.clients.keys())
        # Try to send the message to each of the clients
        for client_name in clients_list:
            try:
                self.clients[client_name].send(f"\n{datetime.now().strftime(tenant_config['chat_server']['timestamp_layout'])} - {message}\n".encode(tenant_config["chat_server"]["encoding"]))
                transport_tenant_logger.info(msg=f"\nTo {client_name}: \n{datetime.now().strftime(tenant_config['chat_server']['timestamp_layout'])} - {message}\n")
            # If sending the message fails due to a lost connection (ConnectionResetError),
            # remove the respective client, for which the error appeared from the client
            # list. If it is already removed (KeyError), pass.
            except (ConnectionResetError,KeyError) as e:
                self.remove_client(client_name=client_name, error=e)


    def forward_message(self, name:str):
        """This funciton forwards a message received from a client either to the
        other clients or to internal processing routines.

        :param name: The name of the client, from where the messages are received
        :type name: str
        """
        while True:
            clients_list = list(self.clients.keys())
            # Try to receive a message from each client and share it with the other
            # clients
            for client_name in clients_list:
                try:
                    msg = self.clients[name].recv(1024).decode(tenant_config["chat_server"]["encoding"])
                    self.send_message_to_all(message=f"{name}: {msg}")
                    # % marks messages, which are related to the processing of the request.
                    # It will be attempted to process these messages and post a request.
                    if "%" in msg:
                        request_ID = msg.split(";")[1]
                        request = self.informed_queue[request_ID]
                        self._post_result(request=request, data={"executant": client_name, "message": msg})
                        transport_tenant_logger.info(msg=f"Posted result for request with ID {request_ID}.")
                        self.send_message_to_all(message=f"Posted result for request {request_ID}.")
                    # # marks messages, which are targeted towards the chat server.
                    # "#exit" is one example, which will deregister a client from the
                    # chat server.
                    if "#exit" in msg:
                        self.remove_client(client_name=name, error=None)
                # If sending the message fails due to a lost connection (ConnectionResetError),
                # remove the respective client, for which the error appeared from the client
                # list. If it is already removed (KeyError), pass.
                except (ConnectionResetError,KeyError) as e:
                    self.remove_client(client_name=client_name, error=e)

    def remove_client(self, client_name:str, error):
        """This funciton removes a client from the chat server, if the connection is
        lost (ConnectionResetError), or if the client is already removed (KeyError), pass.

        :param client_name: The name of the client causing the error
        :type client_name: str
        :param error: The error caused by the client to enable handling of the error
        :type error: Any error type
        """
        if isinstance(error, ConnectionResetError) or error is None:
            # Remove the client from the list of clients
            self.clients[client_name].shutdown(socket.SHUT_RDWR)
            self.clients[client_name].close()
            del self.clients[client_name]
            # Inform everyone
            self.send_message_to_all(message=f"{client_name} left.")
        elif isinstance(error, KeyError):
            pass


    def accept_connections(self, chat_server):
        """This function accepts connections to the chat server

        :param chat_server: A socket representing the chat server
        :type chat_server: socket.socket
        """
        while True:
            # Accept the conntection
            client, address = chat_server.accept()
            # Check, that the connecting client knows the password and hence legitimates
            # for joining the chat
            client.send("_Password".encode(tenant_config["chat_server"]["encoding"]))
            received_password = client.recv(1024)
            # Do not add the tenant to the client list, if it provides a wrong password
            if not crypto_context.verify(received_password, tenant_config["chat_server"]["password"]):
                client.send(f"{datetime.now().strftime(tenant_config['chat_server']['timestamp_layout'])} - You are not authorized to join the chat.".encode(tenant_config["chat_server"]["encoding"]))
                transport_tenant_logger.info(msg=f"Failed to authenticate client at address {address}.")
                continue
            # If the received password is correct, ask for a name to be used in the
            # chat and the results
            client.send("_Name".encode(tenant_config["chat_server"]["encoding"]))
            name = client.recv(1024).decode(tenant_config["chat_server"]["encoding"])
            # If the name provided by the tenant is already in use, ask the user to enter
            # a different one
            while name in self.clients.keys():
                transport_tenant_logger.info(msg=f"Received a client name, which is already in use.")
                client.send(
                    f"{datetime.now().strftime(tenant_config['chat_server']['timestamp_layout'])} - "
                    "This name is already in use. Please try again with a different one."
                    "".encode(tenant_config["chat_server"]["encoding"])
                    )
                name = client.recv(1024).decode(tenant_config["chat_server"]["encoding"])
            # Add the client to self.clients
            self.clients[name] = client
            print(f"{datetime.now().strftime(tenant_config['chat_server']['timestamp_layout'])} - "
                  f"Successful connection to {address} established.")
            transport_tenant_logger.info(msg=f"Established a connection with client {name} at address {address}.")
            # Welcome the new client with some instructions
            client.send(
                f"{datetime.now().strftime(tenant_config['chat_server']['timestamp_layout'])} - "
                f"Welcome {name}!".encode(tenant_config["chat_server"]["encoding"])
                )
            client.send(
                f"{datetime.now().strftime(tenant_config['chat_server']['timestamp_layout'])} - "
                "Syntax for finishing a task: \n '%DONE;<request_uuid>;<actual_new_position>' \n "
                f"The actual new position is optional.\n\n"
                f"If you want to leave the chat, enter a message containing '#exit'.\n"
                "".encode(tenant_config["chat_server"]["encoding"])
                )
            # Inform all the clients about the new client
            self.send_message_to_all(f"New memeber in the chat: {name}")
            # Start the thread for the new client
            thread = threading.Thread(target=self.forward_message, args=(name,))
            thread.start()
            transport_tenant_logger.info(msg=f"Welcomed new client {name} and started new thread for communication.")

    def start_chat_server(self) -> socket.socket:
        """This funciton starts a chat server.

        :return: The server providing the chat functionality of the tenant.
        :rtype: socket.socket
        """
        # Instantiate the socket, bind it to the configured address and start
        # to listen
        chat_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        chat_server.bind((self.chat_host, self.chat_port))
        chat_server.listen()
        transport_tenant_logger.info(msg=f"Started chat server at host {self.chat_host} and port {self.chat_port}.")

        # Start a thread to accept new connections
        accepting_thread = threading.Thread(target=self.accept_connections, args=(chat_server,))
        accepting_thread.start()
        print(f"Chat server started on host {self.chat_host} and port {self.chat_port}.")
        transport_tenant_logger.info(msg=f"Started chat server started on host {self.chat_host} and port {self.chat_port}.")
        return chat_server


    def run_custom(self):
        """A copy of the reference tenant run() method,
        but omitting the preparation and postin of results.
        """  
        # If there is not yet a chat server start one
        if self.chat_server is None:
            self.chat_server = self.start_chat_server()

        # Run until the end_run_time is exceeded
        # this is intended for maintenance like refilling consumables,
        # for which a time can roughly be estimated
        while datetime.now() < self.end_run_time:
            # Wait in between two requests to FINALES
            time.sleep(self.sleep_time_s)
            # Get the currently pending requests from FINALES
            self._update_queue()
            transport_tenant_logger.info(msg="Updated queue.")
            if len(self.queue) > 0:
                for request in self.queue:
                    try:
                        # Inform or remind of requests, which do not yet have a result
                        message = self._run_method(request_info = request)
                        if request["uuid"] in self.informed_queue.keys():
                            if request["status"] == RequestStatus.PENDING:
                                level = "STILL PENDING"
                                transport_tenant_logger.info(msg=f"Need to send a reminder.")
                            else:
                                del self.informed_queue[request["uuid"]]
                        else:
                            level = "NEW"
                            transport_tenant_logger.info(msg=f"Need to send the initial notification.")
                            self.informed_queue[request["uuid"]] = request
                        self.send_message_to_all(message=f"{level}: {message}")
                    # If an error occurs during processing of a request, put its status
                    # back to pending to be able to pick it up again later.
                    except (Exception, KeyboardInterrupt) as e:
                        self._change_status(
                            req_res_dict=request,
                            new_status=RequestStatus.PENDING,
                            status_change_message=(
                                f"Processing of request {request['uuid']} failed."
                            ),
                        )
                        transport_tenant_logger.exception(msg=f"An error occured while processing request {request['uuid']}:\n {e}")
                        raise


# Instantiate the transportation tenant
Transportation_tenant = Tenant_custom(
    general_meta = GeneralMetaData(**tenant_config["general_meta"]),
    sleep_time_s = 60.,
    quantities = transport_quantities,
    tenant_config = f"{tenant_config}",
    run_method = tranport_run,
    prepare_results = transport_prepare_results,
    FINALES_server_config = ServerConfig(**tenant_config["ServerConfig"]),
    end_run_time = tenant_config["end_run_time"],
    operators = [User(**operator) for operator in tenant_config["operators"]],
    tenant_user = tenant_config["tenant_user"],
    tenant_uuid = "71e8e983f58c4ab1937f929fa641e2d8"
)

# If the json for registering the tenant is requried, execute the following line and
# comment the line containing the Transportation_tenant.run_custom() command.
# Transportation_tenant.tenant_object_to_json()

# Run the transportation tenant
Transportation_tenant.run_custom()
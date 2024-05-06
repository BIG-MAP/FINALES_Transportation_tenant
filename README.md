# FINALES_Transportation_tenant
The transportation tenant created for the use with FINALES.

# Related Documents and Links to FINALES

Documents related to the FINALES project and its broader context can be found on the
respective Wiki page of the project:
[https://github.com/BIG-MAP/FINALES2/wiki/Links](https://github.com/BIG-MAP/FINALES2/wiki/Links)

Links to FINALES:

1. FINALES latest version Github
[https://github.com/BIG-MAP/FINALES2](https://github.com/BIG-MAP/FINALES2)

1. FINALES v1.1.0 Zenodo
[10.5281/zenodo.10987727](10.5281/zenodo.10987727)

1. Schemas of FINALES v1.1.0
[https://github.com/BIG-MAP/FINALES2_schemas](https://github.com/BIG-MAP/FINALES2_schemas)


# Description

The Transportation tenant enables the necessary manual transport of the electrolyte to the cell assembly and the transport of the cells to the cycler.
Mulitple users are able to use the tenant and post the result including the new location by writing a certain message to the tenant.

# Installation

To install the tenant, please follow the steps listed below:

1. Clone this repository
1. Install the packages reported in the requirements.txt
1. _(chat server administrators only)_ Clone the repository of FINALES version 1.1.0 [https://github.com/BIG-MAP/FINALES2](https://github.com/BIG-MAP/FINALES2)
1. _(chat server administrators only)_ Install the FINALES package by switching to the respective directory and
running `pip install . `
1. Adjust the configuration files to match your setup and replace all the placeholders
enclosed in `<>`.
The files to manually alter are:
    - `config_transportation_client.py` (by each client. The information about the
    server password etc. must be provided by the chat server administrator.)
    - `config_transportation_tenant.py` (by the chat server administrator. The information
    regarding the FINALES server must be provided by the FINALES administrator.)
1. _(chat server administrators only)_ Ensure to adjust the acceptable origins and
    destinations in the `Transportation_tenant.py`, which are used in the limitations
    of the tenant.
1. _(chat server administrators only)_ Alter the bottom lines of the script
    `Transportation_tenant.py` to read
    ```
    # If the json for registering the tenant is requried, execute the following line and
    # comment the line containing the Transportation_tenant.run_custom() command.
    Transportation_tenant.tenant_object_to_json()

    # Run the transportation tenant
    # Transportation_tenant.run_custom()
    ```
    and run the script. This will update or create the `Transportation_tenant_tenant.json` file, which you can then send to your FINALES server administrator.
1. _(chat server administrators only)_ Once the server administrator provides you with a tenant UUID, provide it in the
respective key in the instantiation of the Transportation tenant in the `Transportation_tenant.py`
file and alter the bottom lines to read
    ```
    # If the json for registering the tenant is requried, execute the following line and
    # comment the line containing the Transportation_tenant.run_custom() command.
    # Transportation_tenant.tenant_object_to_json()

    # Run the transportation tenant
    Transportation_tenant.run_custom()
    ```

You are now all set to run the chat server and use the tenant once the FINALES instance and all the hardware, for which it is configured, is running.

# Usage

## Chat server

To start the chat server and the tenant run the script `Transportation_tenant.py`.

## Chat client

Once the chat server is running and the client-side steps in the installation section
are done, the chat client may be started executing the script `Transportation_client.py`.
**The chat server and each client must be connected to the same network!**

The chat server messages the clients once a new transport request is available on FINALES
allows the clients to reply to transport requests in the following two ways:

1. _The transport was performed as requested_  
    In this case, the client may respond by a message according to the syntax
    `%DONE;<request_uuid>`. The `request_uuid` and the other details regarding the requested transport
    can be found in the chat message sent by the tenant.
1. _The actual destination deviates from the requested one_  
    In this case, the client can provide the actual new location of the transported
    good in the chat message using the syntax `%DONE;<request_uuid>;<actual_new_position>`.
    The `<actual_new_position>` needs to be supplied in the format as specified in the
    [Schemas used with FINALES v1.1.0](https://github.com/BIG-MAP/FINALES2_schemas).

In both cases, the `%DONE` marker informs the tenant, that the transport was performed successfully. `%` in a message marks it relevant for processing by the tenant. Sending a message containing `#exit` allows a client to disconnect from the chat. All other messages are forwarded to the other clients as usual in chats. All messages are logged and the name chosen for a client in the chat will be used to identify the person/instance/..., who/which executed the transport.
    

# Acknowledgements

This project received funding from the European Union’s [Horizon 2020 research and innovation programme](https://ec.europa.eu/programmes/horizon2020/en) under grant agreement [No 957189](https://cordis.europa.eu/project/id/957189) (BIG-MAP).
The authors acknowledge BATTERY2030PLUS, funded by the European Union’s Horizon 2020 research and innovation program under grant agreement no. 957213.
This work contributes to the research performed at CELEST (Center for Electrochemical Energy Storage Ulm-Karlsruhe) and was co-funded by the German Research Foundation (DFG) under Project ID 390874152 (POLiS Cluster of Excellence).

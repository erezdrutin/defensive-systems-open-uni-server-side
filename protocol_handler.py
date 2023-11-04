import logging
import os
import uuid
import struct
from datetime import datetime
from const import SERVER_VERSION, RequestCodes, ResponseCodes, \
    CLIENTS_NAME_SIZE, CLIENTS_AES_KEY_SIZE, FILES_STORAGE_FOLDER
from custom_exceptions import ClientDisconnectedError
from db_handler import DatabaseHandler
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Random import get_random_bytes
from crypto import readfile as readfile_crc32, decrypt_aes_cbc
from file_handler import FileHandler
from models import Client, File, Request, Response
from base_protocol import BaseProtocol


class ProtocolHandler(BaseProtocol):
    def __init__(self, db_handler: DatabaseHandler, logger: logging.Logger):
        super().__init__(logger=logger)
        self.SERVER_VERSION = SERVER_VERSION
        self.db_handler = db_handler

    def handle_request(self, client_socket):
        # The format string for struct.unpack:
        # - 16s: client_id is a 16-byte string
        # - B: version is a 1-byte unsigned char
        # - H: code is a 2-byte unsigned short
        # - I: payload_size is a 4-byte unsigned int
        # Assuming the total size of the struct is
        # (16 + 1 + 2 + 4 = 23 bytes) without the payload.
        format_string = "16sBHI"
        size_without_payload = struct.calcsize(format_string)
        data = client_socket.recv(size_without_payload)

        # The client has disconnected, raise an error
        if data == b'':
            raise ClientDisconnectedError("Client has disconnected.")

        # Unpack the data
        client_id_bytes, version_byte, code, payload_size = struct.unpack(
            format_string, data)
        # Save client_id as bytes and remove trailing null bytes
        client_id = client_id_bytes.replace(b'\x00', b'')
        version = chr(version_byte)  # Converts ascii byte value to string
        code = RequestCodes(code)

        # Read the payload based on the payload_size
        payload = client_socket.recv(payload_size)

        request = Request(client_id, version, code,
                          payload_size, payload)

        # Trigger handler based on request code + wrap with logger:
        handler = self.request_handlers.get(request.code,
                                            self._send_general_error)
        handler = self.log_decorator(handler)
        handler(client_socket, request)

    @BaseProtocol.register_request(RequestCodes.REGISTRATION)
    def _handle_registration(self, client_socket, request: Request):
        # Extracting request details
        client_name = request.payload.decode('utf-8').strip('\x00').strip()

        client = self.db_handler.get_client(client_name=client_name)
        if client:
            # Username already exists
            response = Response(self.SERVER_VERSION,
                                ResponseCodes.REGISTRATION_FAILED, b"")
            client_socket.sendall(response.to_bytes())
            return

        # Generating a 16 bit UUID for the client:
        client_id = uuid.uuid4().bytes
        client = Client(id=client_id, name=client_name, public_key=b'',
                        last_seen=datetime.now(), aes_key=b'')

        # Add the client to the DB (with partial info):
        self.db_handler.add_client(client=client)

        # Craft the response payload with the UUID
        response = Response(self.SERVER_VERSION,
                            ResponseCodes.REGISTRATION_SUCCESS, client_id)
        bytes_res = response.to_bytes()
        client_socket.sendall(bytes_res)

    @BaseProtocol.register_request(RequestCodes.RECONNECT)
    def _handle_reconnect(self, client_socket, request: Request):
        # Extracting request details
        client_name = request.payload.decode('utf-8').strip('\x00').strip()

        client = self.db_handler.get_client(client_name=client_name)
        if not client or not client.public_key:
            # Username already exists
            response = Response(self.SERVER_VERSION,
                                ResponseCodes.RECONNECT_REJECTED,
                                b"Restart as new client")
            client_socket.sendall(response.to_bytes())
            return

        # Encrypt the AES key using the client's public key
        public_key = RSA.import_key(client.public_key)
        cipher_rsa = PKCS1_OAEP.new(public_key)
        encrypted_aes_key = cipher_rsa.encrypt(client.aes_key)
        combined_payload = client.id + encrypted_aes_key

        # Construct the response
        response = Response(self.SERVER_VERSION,
                            ResponseCodes.APPROVE_RECONNECT_SEND_AES,
                            combined_payload)
        client_socket.sendall(response.to_bytes())

    @BaseProtocol.register_request(RequestCodes.SEND_PUBLIC_KEY)
    def _handle_public_key(self, client_socket, request: Request):
        # Assuming the payload is structured as username|public_key
        # Extracting the username and public key
        client_name = request.payload[:CLIENTS_NAME_SIZE].decode().strip(
            '\x00')
        public_key_pem = request.payload[CLIENTS_NAME_SIZE:]

        # Generate an AES key for the client
        aes_key = get_random_bytes(CLIENTS_AES_KEY_SIZE)  # AES-128 key

        # Update public key and AES key in the database
        self.db_handler.update_public_key_and_aes_key(
            client_id=request.client_id, aes_key=aes_key,
            public_key=public_key_pem)

        # Encrypt the AES key using the client's public key
        public_key = RSA.import_key(public_key_pem)
        cipher_rsa = PKCS1_OAEP.new(public_key)
        encrypted_aes_key = cipher_rsa.encrypt(aes_key)
        combined_payload = request.client_id + encrypted_aes_key

        # Construct the response
        response = Response(self.SERVER_VERSION,
                            ResponseCodes.RECEIVED_PUBLIC_KEY_SEND_AES,
                            combined_payload)
        client_socket.sendall(response.to_bytes())

    @BaseProtocol.register_request(RequestCodes.SEND_FILE)
    def _handle_file_transfer(self, client_socket, request_details: Request):
        # Retrieve the AES key for this client from the database
        aes_key = self.db_handler.get_aes_key_for_client(
            request_details.client_id)

        content_size = int.from_bytes(request_details.payload[0:4],
                                      byteorder='big')

        # Extract file name (trimming any null bytes)
        file_name = request_details.payload[4:259].decode('utf-8').rstrip('\0')

        # Extract the Base64 encoded encrypted content
        encrypted_content_hex = request_details.payload[
                                259:259 + content_size]

        # Decrypt using our AES CBC decryption method
        decrypted_file = decrypt_aes_cbc(encrypted_content_hex, aes_key)

        # Create the file (both locally "in storage") & in the DB:
        file = File(id=request_details.client_id, file_name=file_name,
                    path_name=os.path.join(FILES_STORAGE_FOLDER, file_name),
                    verified=False)
        FileHandler(filepath=file.path_name).write_value(decrypted_file)
        # This will append the file to DB if user-file doesn't exist yet:
        self.db_handler.add_file(file=file)

        # Calculate the CRC checksum for the decrypted file
        crc_checksum = readfile_crc32(file.path_name)

        # ClientID - 16 bytes
        response_payload = request_details.client_id
        # Content Size - 4 bytes
        response_payload += content_size.to_bytes(4, byteorder='big')
        # File Name - 255 bytes
        response_payload += file_name.encode('utf-8').ljust(255, b'\0')
        # CRC Checksum - 4 bytes
        response_payload += crc_checksum
        response = Response(self.SERVER_VERSION,
                            ResponseCodes.FILE_RECEIVED_CRC_OK,
                            response_payload)
        client_socket.sendall(response.to_bytes())

    @BaseProtocol.register_request(RequestCodes.CRC_CORRECT)
    def _handle_message_received_approval(self, client_socket,
                                          request: Request):
        # Update verified field to True:
        file_name = request.payload[:255].decode('utf-8').rstrip('\0')
        self.db_handler.update_file_verified(client_id=request.client_id,
                                             file_name=file_name,
                                             verified=True)
        response = Response(self.SERVER_VERSION,
                            ResponseCodes.CONFIRM_MSG,
                            payload=request.client_id)
        client_socket.sendall(response.to_bytes())

    @BaseProtocol.register_request(RequestCodes.CRC_INCORRECT_RESEND)
    def _handle_crc_invalid_resend(self, client_socket, request: Request):
        print(f"Received MSG with code - {request.code}")
        pass

    @BaseProtocol.register_request(RequestCodes.CRC_INCORRECT_DONE)
    def _send_general_error(self, client_socket, request: Request):
        response = Response(self.SERVER_VERSION, ResponseCodes.GENERAL_ERROR,
                            b"General server exception or invalid "
                            b"request code.")
        client_socket.sendall(response.to_bytes())

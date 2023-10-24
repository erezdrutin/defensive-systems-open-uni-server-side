import uuid
import zlib
from dataclasses import dataclass

from Crypto.Util.Padding import unpad

from const import SERVER_VERSION
from src.db_handler import DatabaseHandler
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Random import get_random_bytes


@dataclass
class RequestDetails:
    client_id: str
    version: int
    code: int
    payload_size: int
    payload: bytes


@dataclass
class ResponseDetails:
    version: int
    code: int
    payload: bytes

    @property
    def payload_size(self):
        return len(self.payload)

    def to_bytes(self):
        """Convert the response details to a byte sequence
        based on the specified structure."""
        version_bytes = self.version.to_bytes(1, byteorder='big')
        code_bytes = self.code.to_bytes(2, byteorder='big')
        payload_size_bytes = self.payload_size.to_bytes(4, byteorder='big')
        return version_bytes + code_bytes + payload_size_bytes + self.payload


class ProtocolHandler:
    def __init__(self, db_handler: DatabaseHandler):
        self.SERVER_VERSION = SERVER_VERSION
        self.db_handler = db_handler
        # Mapping request codes to their respective handler methods
        self.request_handlers = {
            1025: self._handle_registration,
            1026: self._handle_public_key,
            1027: self._handle_reconnection,
            1028: self._handle_file_transfer,
            1029: self._handle_crc_correct,
            1030: self._handle_crc_invalid_resend,
            1031: self._handle_crc_invalid_final,
        }

    def extract_request_details(self, raw_request):
        client_id = raw_request[:16].decode()
        version = int.from_bytes(raw_request[16:17], byteorder='big')
        code = int.from_bytes(raw_request[17:19], byteorder='big')
        payload_size = int.from_bytes(raw_request[19:23], byteorder='big')
        payload = raw_request[23:23 + payload_size]

        # Validate the request code
        if code not in self.request_handlers:
            raise ValueError(f"Invalid request code: {code}")

        return RequestDetails(client_id, version, code, payload_size, payload)

    def handle_request(self, client_socket):
        # Read the first 2 bytes to determine the request type
        request_code = int.from_bytes(client_socket.recv(2), byteorder='big')

        # Dispatch to the appropriate handler or send a general error response
        handler = self.request_handlers.get(request_code,
                                            self._send_general_error)
        handler(client_socket)

    def _handle_registration(self, client_socket):
        # Extracting request details
        raw_request = client_socket.recv(1024)
        request_details = self.extract_request_details(raw_request)
        username = request_details.payload.decode().strip()

        user_uuid = self.db_handler.get_user_uuid(username)

        if user_uuid:
            # Username already exists
            response = ResponseDetails(self.SERVER_VERSION, 2101, b"")
            client_socket.sendall(response.to_bytes())
            return

        # Register the new user
        user_uuid = str(uuid.uuid4())
        self.db_handler.register_user(username, user_uuid)

        # Craft the response payload with the UUID
        response = ResponseDetails(self.SERVER_VERSION, 2100,
                                   user_uuid.encode())
        client_socket.sendall(response.to_bytes())

    def _handle_public_key(self, client_socket, request_details):
        # Assuming the payload is structured as username|public_key
        # Extracting the username and public key
        username, public_key_pem = request_details.payload.decode().split("|")

        # Generate an AES key for the client
        aes_key = get_random_bytes(32)  # AES-256 key

        # Update public key and AES key in the database
        self.db_handler.update_public_key_and_aes_key(username, public_key_pem,
                                                      aes_key)

        # Encrypt the AES key using the client's public key
        public_key = RSA.import_key(public_key_pem.encode())
        cipher_rsa = PKCS1_OAEP.new(public_key)
        encrypted_aes_key = cipher_rsa.encrypt(aes_key)

        # Construct the response
        response = ResponseDetails(self.SERVER_VERSION, 2102,
                                   encrypted_aes_key)
        client_socket.sendall(response.to_bytes())

    def _handle_reconnection(self, client_socket, request_details):
        # Extracting the client's UUID from the payload
        client_uuid = request_details.payload.decode().strip()

        # Check if the client UUID exists in our database
        if self.db_handler.get_user_uuid(client_uuid):
            # Client UUID exists

            # Verify the client's version against the server's version
            if request_details.version == self.SERVER_VERSION:
                # Versions match, send a success response
                response = ResponseDetails(
                    self.SERVER_VERSION, 2105, b"Reconnection successful")
            else:
                # Versions don't match, send a version mismatch error response
                response = ResponseDetails(
                    self.SERVER_VERSION, 2106,
                    b"Version mismatch. Please update your client.")
        else:
            # Client UUID does not exist, send an error response
            response = ResponseDetails(self.SERVER_VERSION, 2106,
                                       b"Invalid client UUID")

        client_socket.sendall(response.to_bytes())

    def _handle_file_transfer(self, client_socket, request_details):
        # Retrieve the AES key for this client from the database
        aes_key = self.db_handler.get_aes_key_for_client(
            request_details.client_id)

        # Decrypt the received file using the AES key
        cipher_aes = AES.new(aes_key, AES.MODE_CBC,
                             iv=request_details.payload[:16])
        decrypted_file = unpad(
            cipher_aes.decrypt(request_details.payload[16:]), AES.block_size)

        # Calculate the CRC checksum for the decrypted file
        crc_checksum = zlib.crc32(decrypted_file)

        # Construct the response with the CRC checksum
        response = ResponseDetails(self.SERVER_VERSION, 2108,
                                   crc_checksum.to_bytes(4, byteorder='big'))
        client_socket.sendall(response.to_bytes())

    def _handle_crc_correct(self, client_socket):
        pass

    def _handle_crc_invalid_resend(self, client_socket):
        pass

    def _handle_crc_invalid_final(self, client_socket):
        pass

    def _send_general_error(self, client_socket):
        """Send a general error response."""
        response = ResponseDetails(self.SERVER_VERSION, 2107, b"")
        client_socket.sendall(response.to_bytes())

"""
Author: Erez Drutin
Date: 04.11.2023
Purpose: A file with custom exceptions for easy parsing throughout the code.
"""


class ClientDisconnectedError(Exception):
    """ Raised when a client has disconnected from the server. """
    pass

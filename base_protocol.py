"""
Author: Erez Drutin
Date: 02.11.2023
Purpose: The idea here is to simplify the work when registering new "route"
handlers for new request codes, such that whenever we add a new one, we can
simply wrap the method with its respective code, and we will automatically
get the logging and the handling "associated" with that code.
Note: This feels a bit like an overkill compared to the scope of the project,
thus I stopped here. Otherwise, I would have happily added another abstraction
layer to further distance the implementation level of the protocol handler
from the actual required methods using an "abstract" class as an interface.
"""
import logging
from typing import Callable, Dict

from const import RequestCodes
from models import Request, Response


class BaseProtocol:
    # A dictionary that will hold a mapping between request codes and
    # matching methods to trigger.
    request_handlers: Dict[RequestCodes, Callable] = {}

    def __init__(self, logger=None):
        self.logger = logger if logger else logging.getLogger(
            self.__class__.__name__)

    @classmethod
    def register_request(cls, code: RequestCodes) -> Callable:
        """
        A class method to allow registration of request handler methods with
        specific request codes.
        @param code: A code to associate with the received method.
        @return: The received method.
        """

        def decorator(func):
            cls.request_handlers[code] = func
            return func

        return decorator

    def log_decorator(self, func: Callable):
        """
        A method to decorate by logging the request codes that we're handling.
        This is by design not a "requirement" as we may not always want our
        BaseProtocol implementers to log messages.
        @param func: A method to wrap.
        @return: The wrapped method.
        """

        def wrapper(client_socket, request: Request, *args, **kwargs):
            info_msg = f"{request.code} from client ID: {request.client_id}"

            # Logging the request before receiving it and after handling it:
            self.logger.info(f"Received request code: {info_msg}")
            result: Response = func(self, client_socket, request, *args,
                                    **kwargs)

            self.logger.info(f"Finished handling request code: {info_msg}")

            return result

        return wrapper

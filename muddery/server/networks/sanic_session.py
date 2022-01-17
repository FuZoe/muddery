
import json, traceback
from muddery.server.server import Server
from muddery.server.utils.logger import logger


class SanicSession(object):
    """
    Websocket path.
    """
    def __init__(self, *args, **kwargs):
        """
        Init the channel.

        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)

        self.connection = None
        self.address = None
        self.account = None
        self.authed = False

    def __str__(self):
        """
        Output self as a string
        """
        output = self.address
        if self.account:
            output += "-" + str(self.account)
        return output

    def connect(self, request, connection):
        """
        Called on a client connecting in.
        """
        # To send message back to the client, accept first.
        self.connection = connection
        self.address = "%s:%s" % (request.ip, request.port)

    async def disconnect(self, close_code):
        """
        Called on a client disconnected.
        """
        if self.account:
            await self.logout()

    async def receive(self, text_data=None, bytes_data=None):
        """
        Received a message from the client.

        :param text_data:
        :param bytes_data:
        :return:
        """
        # Pass messages to the muddery server.
        await Server.inst().handler_message(self, text_data)

    async def login(self, account):
        """
        Login an account.
        """
        self.authed = True

        if self.account:
            await self.logout()

        self.account = account

        # call hook
        await self.account.at_post_login(self)

    async def logout(self):
        """
        Logout an account
        """
        if self.account:
            # call hook
            await self.account.at_pre_logout()

        self.account = None
        self.authed = False

    async def msg(self, text, context=None):
        """
        Send data to the client.

        :param data_out: data to send {type: data}
        :param close: close connect after sends message.
        """
        # create the output string
        out_text = json.dumps({"data": text, "context": context}, ensure_ascii=False)

        # send message
        try:
            await self.connection.send(out_text)
        except Exception as e:
            logger.log_err("Send message error: %s" % e)

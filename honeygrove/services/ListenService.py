from honeygrove import log
from honeygrove.config import Config
from honeygrove.services.ServiceBaseModel import ServiceBaseModel

from twisted.internet import reactor
from twisted.internet.error import CannotListenError
from twisted.internet.protocol import Factory, Protocol


class ListenService(ServiceBaseModel):
    def __init__(self):
        """
        This service can open a lot of ports and starts listening and loggin on them.
        """
        super(ListenService, self).__init__()

        self._fService = Factory()
        self.protocol = ListenProtocol
        self._fService.protocol = self.protocol

        self._name = Config.listen.name
        self._ports = Config.listen.ports
        self._transport = dict([])
        self._stop = True
        self._active = False

    def startService(self):
        """
        Start service on all ports defined in Config.py. 
        Ignores ports where it can't listen.
        :return:
        """
        try:
            self._stop = False
            for port in self._ports:
                try:
                    self._transport[port] = reactor.listenTCP(port, self._fService, interface=self._interface)
                except CannotListenError:
                    pass

            self._active = True

        except Exception as e:
            log.err(e)
            self._stop = True

    def startOnPort(self, port):
        """
        Start service on a specific port if it doesn't already run there.
        Ignores this call when it can't listen.
        :param port: the port on which the service shall start
        :return:
        """
        if self._stop:
            self._stop = False

        if port not in self._transport and self._active:
            try:
                self._transport[port] = reactor.listenTCP(port, self._fService)
            except CannotListenError:
                pass

    def stopOnPort(self, port):
        """
        Stop service on a specific port.
        :param port: the port where the service should stop listening
        """

        if port in self._transport and self._active:
            self._transport[port].stopListening()
            try:
                self._transport[port].connectionLost("Force close/cleanup due to next service scheduling")
            except AttributeError:
                log.err("ListenService connectionLost wirft AttributeError!", port)
            self._transport.pop(port, None)
            # Dict is Empty
            if not self._transport:
                self._stop = True

    def stopService(self):
        """
        Closes all open ports and stops the Service
        """
        if not self._stop:
            for key, _ in self._transport.items():
                self._transport[key].stopListening()
                try:
                    self._transport[key].connectionLost("Force close/cleanup due to next service scheduling")
                except AttributeError:
                    log.err("ListenService connectionLost wirft AttributeError!", key)

        self._stop = True
        self._active = False


class ListenProtocol(Protocol):
    def dataReceived(self, data):
        """
        Called when the attacker sends data.
        :param data: The received data
        """

        local = self.transport.getHost()
        remote = self.transport.getPeer()
        log.request(Config.listenServiceName, remote.host, remote.port, local.host, local.port, data.decode())

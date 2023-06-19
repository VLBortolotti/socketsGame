import socket
import json
import queue
import secrets
import random
from   Request       import *
from   Response      import *
from   pygame.locals import *

class ClientUDP:
    def __init__(self) -> None:
        self.udpAddressPort    = ('127.0.0.1', 20001)
        self.tcpAddressPort    = ('127.0.0.1', 20005)

        self.bufferSize        = 1024

        self.thisUDPAddress    = ('127.0.0.1', random.randint(2000, 65000))
        self.UDPClientSocket   = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.UDPClientSocket.bind(self.thisUDPAddress)

        self.TCPClientSocket   = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.TCPClientSocket.connect(self.tcpAddressPort)

        self.currentRoom       = None
        self.sharedQueue       = queue.Queue()

        self.addressToken      = secrets.token_hex(nbytes=16)

    def sendRequestWithTCP(self, request):
        bytesToSend = str.encode(json.dumps(request.getRequestAsArray()))
        self.TCPClientSocket.sendall(bytesToSend)
    
    def sendRequestWithUDP(self, request):
        request.getRequestData()['tcpAddress'] = self.TCPClientSocket.getsockname()
        bytesToSend = str.encode(json.dumps(request.getRequestAsArray()))
        self.UDPClientSocket.sendto(bytesToSend, self.udpAddressPort)
    
    def getTCPResponse(self):
        try:
            serverMessage = self.TCPClientSocket.recv(self.bufferSize)
            serverMessage = json.loads(serverMessage)
            response = Response()

            return response.createResponseFromArray(serverMessage)
        except:
            return False
    
    def getUDPReponse(self):
        try:
            # Waiting for response
            bytesAddressPair = self.UDPClientSocket.recvfrom(self.bufferSize)
            serverMessageArray = json.loads(bytesAddressPair[0])

            response = Response()

            return response.createResponseFromArray(serverMessageArray)
        except:
            return False
    
    def getResponses(self):
        while True:
            response = self.getUDPReponse()
            # Append response to the shared queue
            if response:                   
                self.sharedQueue.put(response)

    def getQueue(self):
        return self.sharedQueue
        
    def createRoom(self):
        # Sending message to create room
        request = Request(requestCode=100)
        self.sendRequestWithTCP(request)

        # Waiting for response
        return self.getTCPResponse()
    
    def listRooms(self):
        request = Request(requestCode=103, token=self.currentRoom)
        self.sendRequestWithTCP(request=request)

        # Waiting for response
        return self.getTCPResponse()

    def joinRoom(self, roomToken):
        self.currentRoom = roomToken

        # Sending message to join a room
        request = Request(requestCode=101, token=self.currentRoom, requestData=self.thisUDPAddress)
        self.sendRequestWithTCP(request=request)

        # Waiting for response
        return self.getTCPResponse()

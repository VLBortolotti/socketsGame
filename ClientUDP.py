import socket                   # biblioteca de sockets
import json                     # biblioteca para manipulacao de JSON
import queue                    # estrutura de dados Fila
import secrets                  # biblioteca para criacao de hashes
import random                   # biblioteca para criar numeros aleatorios
import threading                # biblioteca de threads
from   Request       import *   # classe request
from   Response      import *   # classe response
from   pygame.locals import *   # variaveis do Pygame

# Classe que trata de fazer requisicoes ao servidores TCP e UDP 
# e fazer as manipulacoes necessarias, como tratar as respostas, atualizar jogadores,
# etc.
class ClientUDP:
    def __init__(self) -> None:
        self.udpAddressPort    = ('127.0.0.1', 20001)#(endereço, porta) UDP do servidor
        self.tcpAddressPort    = ('127.0.0.1', 20005)#(endereço, porta) TCP do servidor

        self.bufferSize        = 1024  # tamanho maximo dos dados recebidos/enviados

        # numero aleatorio entre 2000 e 65000 sera atribuido como a porta 
        # para o endereco UDP do cliente
        self.thisUDPAddress    = ('127.0.0.1', random.randint(2000, 65000))

        # instancia de uma conexao UDP
        self.UDPClientSocket   = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.UDPClientSocket.bind(self.thisUDPAddress)

        # instancia de uma conexao TCP
        self.TCPClientSocket   = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.currentRoom       = None           # token da sala atual da partida
        self.sharedQueue       = queue.Queue()  # Fila de dados recebidos do servidor

        # Hash aleatoria que representa o endereço do cliente
        self.addressToken      = secrets.token_hex(nbytes=16)  

        self.colors = {
            'green': '\033[92m',
            'black': "\u001b[40m",
            'red': "\u001b[41m",
            'green': "\u001b[42m",
            'yellow': "\u001b[43m",
            'blue': "\u001b[44m",
            'magenta': "\u001b[45m",
            'cyan': "\u001b[46m",
            'white': "\u001b[47m",
            "ENDC": '\033[0m'
        }

    # faz uma requisicao TCP para o servidor
    def sendRequestWithTCP(self, request):
        # verifica se o cliente tem uma conexao ativa com o cliente 
        try:
            self.TCPClientSocket.getpeername()
        # caso contrario ele cria uma nova conexao TCP
        except:
            self.TCPClientSocket.connect(self.tcpAddressPort)
        
        # e a requisicao eh enviada para o servidor em forma de JSON, 
        # codificado para string
        bytesToSend = str.encode(json.dumps(request.getRequestAsArray()))
        self.TCPClientSocket.sendall(bytesToSend)
    
    # faz uma requisicao UDP para o servidor
    def sendRequestWithUDP(self, request):
        # adiciona (endereço, porta) ao dicionario de dados da requisicao
        request.getRequestData()['tcpAddress'] = self.TCPClientSocket.getsockname()

        # dado enviado para o servidor
        bytesToSend = str.encode(json.dumps(request.getRequestAsArray()))
        self.UDPClientSocket.sendto(bytesToSend, self.udpAddressPort)
    
    # Trata as respostas TCP do servidor
    def getTCPResponse(self):
        # recebe os dados do servidor em JSON, converte para dicionario, e
        # cria e retorna uma instancia da classe Response com os dados
        try:
            serverMessage = self.TCPClientSocket.recv(self.bufferSize)
            serverMessage = json.loads(serverMessage)
            response = Response()

            return response.createResponseFromArray(serverMessage)
        except:
            return False # em caso de erro, retorna False
    
    # Trata as respostas UDP do servidor
    def getUDPReponse(self):
        # recebe os dados do servidor em JSON, converte para dicionario, e
        # cria e retorna uma instancia da classe Response com os dados
        try:
            bytesAddressPair = self.UDPClientSocket.recvfrom(self.bufferSize)
            serverMessageArray = json.loads(bytesAddressPair[0])

            response = Response()

            return response.createResponseFromArray(serverMessageArray)
        except:
            return False # em caso de erro, retorna False
    
    # Fica ouvindo pelas respostas UDP do servidor
    def getResponses(self):
        while True:
            response = self.getUDPReponse()

            if response:                   
                self.sharedQueue.put(response)
    
    def handleTCPResponse(self, tcpResponse):
        print('CHEGOU AQUI')
        responseCode = tcpResponse.getResponseCode()
        responseData = tcpResponse.getReturnData()

        if responseCode == 299:
            print(f'response:\n{responseData}')
            #print(f"{responseData['name']}: {responseData['message']}")

    # Pega a primeira resposta da fila
    def getQueue(self):
        return self.sharedQueue
    
    # Faz uma requisicao com codigo 100, para criar uma sala
    def createRoom(self):
        request = Request(requestCode=100)
        self.sendRequestWithTCP(request)

        # Aguarda e retorna pela resposta TCP do servidor
        return self.getTCPResponse()
    
    # Faz uma requisicao do tipo 103, para listar as salas ja criadas,
    # enviando tambem o token da sala atual do cliente
    def listRooms(self):
        request = Request(requestCode=103, token=self.currentRoom)
        self.sendRequestWithTCP(request=request)

        # Aguarda e retorna a resposta TCP pelo servidor
        return self.getTCPResponse()

    # Faz uma requisicao 101, para entrar em uma sala,
    # passando o token da sala que deseja-se entrar e o nome escolhido pelo usuario
    def joinRoom(self, roomToken, name):
        requestData = {}
        requestData['name'] = name
        requestData['UDPAddress'] = self.thisUDPAddress
        
        self.currentRoom = roomToken # a nova sala atual do usuario eh atualizada

        # Realiza a requisicao para o servidor TCP
        request = Request(requestCode=101, token=self.currentRoom, requestData=requestData)
        self.sendRequestWithTCP(request=request)

        # Aguarda e retorna a resposta
        return self.getTCPResponse()
    
    def handleUserInput(self, userName):
        while True:
            userInput = input('')
            
            requestData = {}
            requestData['name'] = userName
            requestData['message'] = userInput

            request = Request(requestCode=199, token=self.currentRoom,requestData=requestData)
            self.sendRequestWithUDP(request=request)

    def getUserMessage(self, userName):
        print(f'\n{self.colors["blue"]}=x=x=x=x= Bem-vindo ao chat! =x=x=x=x={self.colors["ENDC"]}\n')
        print('Para você enviar uma mensagem aos outros jogadores basta digitar sua mensagem no terminal e apertar a tecla ENTER.\nBoa sorte!\n')
        
        inputThread = threading.Thread(target=self.handleUserInput, args=(userName,))
        inputThread.start()
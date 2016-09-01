import optparse
import socket
import sys

class Server:
    def __init__(self,port):
        self.host = ""
        self.port = port
        self.client = None
        self.cache = ''
        self.messages = {}
        self.size = 1024
        self.parse_options()
        self.open_socket()
        self.run()

    def parse_options(self):
        parser = optparse.OptionParser(usage = "%prog [options]",
                                       version = "%prog 0.1")

        parser.add_option("-p","--port",type="int",dest="port",
                          default=5000,
                          help="port to listen on")

        (options,args) = parser.parse_args()
        self.port = options.port

    def open_socket(self):
        """ Setup the socket for incoming clients """
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
            self.server.bind((self.host,self.port))
            self.server.listen(5)
        except socket.error, (value,message):
            if self.server:
                self.server.close()
            print "Could not open socket: " + message
            sys.exit(1)

    def run(self):
        while True:
            try:
                (client,address) = self.server.accept()
            except:
                break
            self.client = client
            self.handle_client()

    def handle_client(self):
        while True:
            data = self.client.recv(self.size)
            if not data:
                return
            self.cache += data
            message = self.read_message()
            if not message:
                continue
            self.handle_message(message)

    def read_message(self):
        index = self.cache.find("\n")
        if index == "-1" or index == -1:
            return None
        message = self.cache[0:index+1]
        self.cache = self.cache[index+1:]
        return message

    def handle_message(self,message):
        response = self.parse_message(message)
        self.send_response(response)

    def parse_message(self,message):
        fields = message.split()
        if not fields:
            return('error invalid message\n')
        if fields[0] == 'reset':
            self.messages = {}
            return "OK\n"
        if fields[0] == 'put':
            try:
                name = fields[1]
                subject = fields[2]
                length = int(fields[3])
            except:
                return('error invalid message\n')
            data = self.read_put(length)
            if data == None:
                return 'error could not read entire message\n'
            self.store_message(name,subject,data)
            return "OK\n"
        if fields[0] == 'list':
            try:
                name = fields[1]
            except:
                return('error invalid message\n')
            subjects,length = self.get_subjects(name)
            response = "list %d\n" % length
            response += subjects
            return response
        if fields[0] == 'get':
            try:
                name = fields[1]
                index = int(fields[2])
            except:
                return('error invalid message\n')
            subject,data = self.get_message(name,index)
            if not subject:
                return "error no such message for that user\n"
            response = "message %s %d\n" % (subject,len(data))
            response += data
            return response
        return('error invalid message\n')
    
    def store_message(self,name,subject,data):
        if name not in self.messages:
            self.messages[name] = []
        self.messages[name].append((subject,data))

    def get_subjects(self,name):
        if name not in self.messages:
            return "",0
        response = ["%d %s\n" % (index+1,message[0]) for index,message in enumerate(self.messages[name])]
        return "".join(response),len(response)

    def get_message(self,name,index):
        if index <= 0:
            return None,None
        try:
            return self.messages[name][index-1]
        except:
            return None,None

    def read_put(self,length):
        data = self.cache
        while len(data) < length:
            d = self.client.recv(self.size)
            if not d:
                return None
            data += d
        if len(data) > length:
            self.cache = data[length:]
            data = data[:length]
        else:
            self.cache = ''
        return data

    def send_response(self,response):
        self.client.sendall(response)

if __name__ == '__main__':
    s = Server(5000)

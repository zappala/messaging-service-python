import fileinput
import optparse
import socket
import sys

class Client:
    def __init__(self,host,port):
        self.host = host
        self.port = port
        self.server = None
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
                          help="port to connect to")

        parser.add_option("-s","--server",type="string",dest="host",
                          default='localhost',
                          help="server to connect to")

        (options,args) = parser.parse_args()
        self.host = options.host
        self.port = options.port


    def open_socket(self):
        """ Connect to the server """
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.connect((self.host,self.port))
        except socket.error, (value,message):
            if self.server:
                self.server.close()
            print "Could not connect to server: " + message
            sys.exit(1)

    def run(self):
        while True:
            # get input from users
            self.prompt()
            command = sys.stdin.readline()
            result = self.parse_command(command)
            if not result:
                print "I don't recognize that command."

    ### Interaction with user ###

    def prompt(self):
        sys.stdout.write("% ")

    def parse_command(self,command):
        fields = command.split()
        if not fields:
            return('error invalid message\n')
        if fields[0] == 'quit':
            sys.exit()
        if fields[0] == 'send':
            ### send message ###
            try:
                name = fields[1]
                subject = fields[2]
            except:
                return False
            data = self.get_user_message()
            self.send_put(name,subject,data)
            self.response_to_put()
            return True
        if fields[0] == 'list':
            ### list messages ###
            try:
                name = fields[1]
            except:
                return False
            self.send_list(name)
            self.response_to_list()
            return True
        if fields[0] == 'read':
            ### read message ###
            try:
                name = fields[1]
                index = int(fields[2])
            except:
                return False
            self.send_read(name,index)
            self.response_to_read()
            return True
        return False

    ### Generic message handling ###

    def get_response(self):
        # get a response from the server
        while True:
            data = self.server.recv(self.size)
            if not data:
                print "Connection to server closed."
                sys.exit()
            self.cache += data
            message = self.read_message()
            if not message:
                continue
            return message

    def read_message(self):
        # read until we have a newline and store excess in cache
        index = self.cache.find("\n")
        if index == "-1":
            return None
        message = self.cache[0:index+1]
        self.cache = self.cache[index+1:]
        return message

    def send_request(self,request):
        self.server.sendall(request)

    ### Handling send ###

    def send_put(self,name,subject,data):
        self.send_request("put %s %s %d\n%s" % (name, subject, len(data), data))

    def get_user_message(self):
        print "- Type your message. End with a blank line -"
        message = ""
        while True:
            # get input from user
            data = sys.stdin.readline()
            if data == "\n":
                return message
            message += data

    def response_to_put(self):
        message = self.get_response()
        if message != "OK\n":
            print "Server returned bad message:",message
            return

    ### Handling list ###

    def send_list(self,name):
        self.send_request("list %s\n" % name)

    def response_to_list(self):
        message = self.get_response()
        fields = message.split()
        try:
            if fields[0] != 'list':
                print "Server returned bad message:",message
                return
            num = int(fields[1])
        except:
            print "Server returned bad message:",message
            return
        self.read_list_response(num)


    def read_list_response(self,num):
        total = 0
        while (total < num):
            data = self.read_message()
            print data,
            total += 1

    ### Handling read ###

    def send_read(self,name,index):
        self.send_request("get %s %s\n" % (name, index))

    def response_to_read(self):
        message = self.get_response()
        fields = message.split()
        try:
            if fields[0] != 'message':
                print "Server returned bad message:",message
                return
            subject = fields[1]
            length = int(fields[2])
        except:
            print "Server returned bad message:",message
            return
        self.read_message_response(subject,length)

    def read_message_response(self,subject,length):
        data = self.cache
        while len(data) < length:
            d = self.server.recv(self.size)
            if not d:
                self.cache = ''
                print "Server did not send the whole message:",data
                return None
            data += d
        if data > length:
            self.cache = data[length:]
            data = data[:length]
        else:
            self.cache = ''
        print subject
        print data,
    

if __name__ == '__main__':
    s = Client('',5000)

import optparse
import socket
import sys

class Tester:
    def __init__(self,host,port):
        self.host = host
        self.port = port
        self.server = None
        self.cache = ''
        self.messages = {}
        self.size = 1024
        self.parse_options()
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
        """ Setup the socket for the server """
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
            self.server.connect((self.host,self.port))
        except socket.error, (value,message):
            print "Could not open socket: " + message
            sys.exit(1)

    def close_socket(self):
        self.server.close()

    def run(self):
        self.testProtocol()
        self.testUsers()
        self.testErrors()
        self.testLarge()
        self.testPartial()

    def testProtocol(self):
        print "*** Message Protocol ***"
        self.open_socket()
        self.send_reset()
        data = 'This is a test message.'
        self.send_put('user1','hello',data)
        self.send_list('user1',"list 1\n1 hello\n")
        self.send_get('user1',1,'hello',data)
        self.close_socket()

    def testUsers(self):
        print "*** Message Protocol (Multiple Users) ***"
        self.open_socket()
        data1 = 'This is a test message.'
        self.send_put('user1','testing',data1)
        data2 = 'Where are you?'
        self.send_put('user2','hello',data2)
        self.send_list('user1',"list 2\n1 hello\n2 testing\n")
        self.send_list('user2',"list 1\n1 hello\n")
        self.send_get('user1',2,'testing',data1)
        self.send_get('user2',1,'hello',data2)
        self.close_socket()

    def testErrors(self):
        print "*** Errors ***"
        self.open_socket()
        self.send_bad_msg("bad\n")
        self.send_bad_msg("put bad\n")
        self.send_bad_msg("put bad hello\n")
        self.send_bad_msg("list\n")
        self.send_bad_msg("get\n")
        self.send_bad_msg("get bad\n")
        self.send_bad_msg("get bad 10000\n")
        self.close_socket()

    def testLarge(self):
        print "*** Test Large Message ***"
        self.open_socket()
        data = "This is a " + "really "*1000 + "long message."
        self.send_put('user3','hello',data)
        self.send_list('user3',"list 1\n1 hello\n")
        self.send_get('user3',1,'hello',data)
        self.close_socket()

    def testPartial(self):
        print "*** Test Partial Messages ***"
        self.open_socket()
        data = "This is a " + "really "*1000 + "long message."
        self.send_put_slow('user4','hello',data)
        self.send_list('user4',"list 1\n1 hello\n")
        self.send_get('user4',1,'hello',data)
        self.close_socket()

    def get_response(self):
        while True:
            data = self.server.recv(self.size)
            if not data:
                response = self.cache
                self.cache = ''
                return response
            self.cache += data
            message = self.get_message()
            if not message:
                continue
            message = self.handle_message(message)
            return message

    def get_message(self):
        index = self.cache.find("\n")
        if index == -1:
            return None
        message = self.cache[0:index+1]
        self.cache = self.cache[index+1:]
        return message

    def handle_message(self,message):
        message = self.parse_message(message)
        return message

    def parse_message(self,message):
        fields = message.split()
        if not fields:
            return message
        if fields[0] == 'list':
            try:
                number = int(fields[1])
            except:
                return message
            data = self.read_list(number)
            return message + data
        if fields[0] == 'message':
            try:
                subject = fields[1]
                length = int(fields[2])
            except:
                return message
            data = self.read_message(length)
            return message + data
        return message

    def read_list(self,number):
        data = self.cache
        newlines = data.count('\n')
        while newlines < number:
            d = self.server.recv(self.size)
            if not d:
                return None
            data += d
            newlines = data.count('\n')
        fields = data.split('\n')
        data = "\n".join(fields[:number]) + '\n'
        self.cache = "\n".join(fields[number:])
        return data
    
    def read_message(self,length):
        data = self.cache
        while len(data) < length:
            d = self.server.recv(self.size)
            if not d:
                return None
            data += d
        if data > length:
            self.cache = data[length:]
            data = data[:length]
        else:
            self.cache = ''
        return data

    def send_reset(self):
        print "Test reset"
        self.server.sendall("reset\n")
        response = self.get_response()
        if response != "OK\n":
            print "Failed to reset, got response:"
            print response
        else:
            print "OK"

    def send_put(self,name,subject,data):
        print "Test put"
        self.server.sendall("put %s %s %d\n%s" % (name,subject,len(data),data))
        response = self.get_response()
        if response != "OK\n":
            print "Failed to put a message, got response:"
            print response
        else:
            print "OK"

    def send_put_slow(self,name,subject,data):
        print "Test put"
        self.server.sendall("put %s %s %d\n" % (name,subject,len(data)))
        for c in data:
            self.server.send(c)
        response = self.get_response()
        if response != "OK\n":
            print "Failed to put a message, got response:"
            print response
        else:
            print "OK"

    def send_list(self,name,expected_response):
        print "Test list"
        self.server.sendall("list %s\n" % (name))
        response = self.get_response()
        if response != expected_response:
            print "Failed to list messages, got response:"
            print response
        else:
            print "OK"

    def send_get(self,name,index,subject,data):
        print "Test get"
        self.server.sendall("get %s %d\n" % (name,index))
        response = self.get_response()
        if response != "message %s %d\n%s" % (subject,len(data),data):
            print "Failed to get a message, got response:"
            print response
        else:
            print "OK"

    def send_bad_msg(self,msg):
        print "Test bad message",msg,
        self.server.sendall(msg)
        response = self.get_response()
        try:
            fields = response.split()
            if fields[0] != "error":
                print "Failed to get error message:"
                print response
            else:
                print "OK"
        except:
                print "Failed to get error message:"
                print response


if __name__ == '__main__':
    s = Tester('',5000)

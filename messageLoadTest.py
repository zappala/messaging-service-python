import optparse
import socket
import sys
import threading

class Reset:
    def __init__(self,host,port):
        self.host = host
        self.port = port
        self.server = None
        self.cache = ''
        self.messages = {}
        self.size = 1024
        self.run()

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
        self.open_socket()
        self.send_reset()
        self.close_socket()

    def send_reset(self):
        self.server.sendall("reset\n")
        response = self.get_response()
        if response != "OK\n":
            print "Failed to reset, got response:"
            print response

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
            return message

    def get_message(self):
        index = self.cache.find("\n")
        if index == "-1":
            return None
        message = self.cache[0:index+1]
        self.cache = self.cache[index+1:]
        return message

class Tester(threading.Thread):
    def __init__(self,host,port,repetitions,name):
        threading.Thread.__init__(self)
        # daemon threads will die if the main program exits
        threading.Thread.daemon = True
        # initialize local variables
        self.host = host
        self.port = port
        self.repetitions = repetitions
        self.name = name
        self.server = None
        self.cache = ''
        self.messages = {}
        self.size = 1024

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
        """ run this thread for a certain number of iterations """
        self.open_socket()
        for iteration in range(1,self.repetitions+1):
            success = self.testProtocol(iteration)
            sys.stdout.flush()
            if not success:
                return
        self.close_socket()

    def testProtocol(self,iteration):
        data = 'This is a test message.'
        success = self.send_put('user1','hello',data)
        if not success:
            return success
        success = self.send_list('user1')
        if not success:
            return success
        success = self.send_get('user1',iteration,'hello',data)
        return success

    ### Generic message handling ###

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
        if index == "-1":
            return None
        message = self.cache[0:index+1]
        self.cache = self.cache[index+1:]
        return message

    def handle_message(self,message):
        message = self.parse_message(message)
        return message

    ### Message parsing ###

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

    ### Sending messages ###

    def send_put(self,name,subject,data):
        self.server.sendall("put %s %s %d\n%s" % (name,subject,len(data),data))
        response = self.get_response()
        if response != "OK\n":
            print "Failed with put:", response
            return False
        else:
            return True

    def send_list(self,name):
        self.server.sendall("list %s\n" % (name))
        response = self.get_response()
        try:
            fields = response.split()
            if fields[0] != 'list':
                print "Failed with list:", response
                return False
            print "%s listed %d messages" % (self.name,int(fields[1]))
            return True
        except:
            print "Failed with list:",response
            return False

    def send_get(self,name,index,subject,data):
        self.server.sendall("get %s %d\n" % (name,index))
        response = self.get_response()
        if response != "message %s %d\n%s" % (subject,len(data),data):
            print "Failed with get:", response
            return False
        else:
            return True


class WorkloadGenerator:
    """ Generate a set of threads to make requests to the server """
    def __init__(self, hostname, port, num_threads, repetitions):
        # reset
        r = Reset(hostname,port)
        self.threads = []
        self.hostname = hostname
        self.port = port
        for i in range(num_threads):
            name = "Thread %d" % (i+1)
            self.threads.append(Tester(hostname, port, repetitions, name))
		
    def run(self):
        """ run the workload generator """
        for thread in self.threads:
            thread.start()
        for thread in self.threads:
            thread.join(60)
            if thread.isAlive():
                print "Waited too long ... aborting"
                return
			
if __name__ == "__main__":
    # parse arguments

    parser = optparse.OptionParser(usage = "%prog -s [server] -p [port] -t [threads] -r [repetitions]",version = "%prog 0.1")

    parser.add_option("-p","--port",type="int",dest="port",
                      default=5000,
                      help="port to connect to")

    parser.add_option("-s","--server",type="string",dest="server",
                      default='localhost',
                      help="server to connect to")

    parser.add_option("-t", "--threads", dest="threads", type="int",
                      default=10,
                      help=	"number of busy threads to test")

    parser.add_option("-r", "--repetitions", dest="repetitions", type="int",
                      default=10,
                      help=	"number of repetitions for each thread")


    (options,args) = parser.parse_args()

    # print welcome message
    print "Server:      %s" % (options.server)
    print "Port:        %d" % (options.port)
    print "Threads:     %d" % (options.threads)
    print "Repetitions: %d" % (options.repetitions)
    print "--------------------------------------------------------"
        
    # launch generators
    generator = WorkloadGenerator(options.server, options.port, options.threads,
                                  options.repetitions)
    generator.run()

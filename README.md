# Messaging service in Python

This code is used to illustrate client-server programming in python,
as part of the [CS 360 Internet Programming](http://cs360.byu.edu)
class at BYU.

## Basic messaging service

This portion of the code implements a [basic messaging
service](http://cs360.byu.edu/fall-2013/labs/messaging-service),
showing how to parse a protocol.

The server is in `messageDaemon.py` and the client is in
`messageClient.py`. A testing script in `messageTest.py` validates
that the server handles the protocol properly.

To run the server:

> python messageDaemon.py [-p port]

To run the client:

> python messageClient.py [-s server] [-p port]

To run the test script:

> python messageTest.py [-s server] [-p port]

**Caution**: This code is singly-threaded, so do not use it as
an example of how to build a modern, scalable server.

## Threaded messaging service

This portion of the code tests a [threaded messaging
service](http://cs360.byu.edu/fall-2013/labs/threaded-messaging-service),
ensuring that it handles multiple clients properly.

To run the test script:

> python messageLoad.py [-s server] [-p port] [-t threads] [-r repetitions]

This will use create a number of threads and each will create, list
and read messages from the server simultaneously, for a given number
of repetitions. You can vary the number of threads and the number of
repetitions to test various loads.

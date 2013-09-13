# Basic messaging service in Python

This code implements a [basic messaging
service](http://cs360.byu.edu/fall-2013/labs/messaging-service), to
illustrate simple client-server programming in Python. The spec is
from a lab used in [CS 360 Internet Programming](http://cs360.byu.edu)
at BYU:



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

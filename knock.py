#!/usr/bin/python

import asyncore
import socket

#class KnockHandler(asyncore.dispatcher_with_send):
#
#    def handle_read(self):
#        data = self.recv(8192)
#        if data:
#            self.send(data)


class Knock():

    def __init__(self, sock):
        self.sock = sock


    def handle_hit(self):
        pass


class KnockServer(asyncore.dispatcher):

    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            print 'Incoming connection from %s to %s' % (repr(addr), repr(sock.getsockname()))
            
            try:
                sock.send('Thank you for connecting\n')
            except socket.error:    # Handle the knocking.
                pass

            sock.close()
            #handler = KnockHandler(sock)


if __name__ == '__main__':
    server = KnockServer('localhost', 8080)
    server = KnockServer('localhost', 8081)
    server = KnockServer('localhost', 8082)
    asyncore.loop()

#!/usr/bin/python

import asyncore
import socket
import struct
import time

TTL = 10

#class KnockHandler(asyncore.dispatcher_with_send):
#
#    def handle_read(self):
#        data = self.recv(8192)
#        if data:
#            self.send(data)

class DictDB():

    def __str__(self):
        return str(self.db)


    def __init__(self):
        self.db = {}


    def write_hit(self, int_ip, port):
        print "write_hit: Connection from %d on port %d" % (int_ip, port)

        try:
            db_user = self.db[int_ip]
            if(db_user['last_port'] < port and (db_user['time'] + TTL) > int(time.time())):
                # Grant access, increase state
                if(db_user['state'] == 1):
                    # Access granted. TODO: Alter the iptables rules.
                    print "Access granted! Hooray!"
                    del self.db[int_ip]
                else:
                    db_user['state'] += 1
                    db_user['time'] = int(time.time())
                    db_user['last_port'] = port
            else:
                # Too late, reset state
                del self.db[int_ip]

        except KeyError:
            # Unknown user, initialize the db
            self.db[int_ip] = {'state': 0, 'time': int(time.time()), 'last_port': port}


    def clean_db(self):
        pass


class Knock():

    def __init__(self, sock, db, client_ip):
        self.sock = sock
        self.db = db
        self.ip = client_ip
        self.handle_hit()


    def handle_hit(self):
        int_ip = self.ip2long(self.ip)
        port = self.sock.getsockname()[1]
        self.db.write_hit(int_ip, port)


    def ip2long(self, ip):
        return struct.unpack("!L", socket.inet_aton(ip))[0]

    def long2ip(self, int_ip):
        return socket.inet_ntoa(struct.pack('!L', int_ip))


class KnockServer(asyncore.dispatcher):

    def __init__(self, host, port, db):
        asyncore.dispatcher.__init__(self)
        self.db = db

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(('', port))
        self.listen(5)

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            print 'Incoming connection from %s to %s' % (repr(addr), repr(sock.getsockname()))
            Knock(sock, self.db, addr[0])
            print self.db
            try:
                sock.send('Thank you for connecting\n')
            except socket.error:    # Handle the knocking.
                pass

            sock.close()
            #handler = KnockHandler(sock)


if __name__ == '__main__':
    db = DictDB()
    server = KnockServer('localhost', 8080, db)
    server = KnockServer('localhost', 8081, db)
    server = KnockServer('localhost', 8082, db)
    asyncore.loop()

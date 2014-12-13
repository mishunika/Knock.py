#!/usr/bin/python

import asyncore
import socket
import struct
import time
from subprocess import Popen, PIPE

# DEBUG Start
DEBUG = True


def log(text):
    if DEBUG:
        print "DEBUG: " + str(text)
# DEBUG End.

TTL = 10
SOCKETS = 3
START_PORT = 8080


class DictDB():
    """Dictionary class by using a dictionary.
    """
    def __str__(self):
        return str(self.db)

    def __init__(self):
        """DB initializer. Creates empty dict.
        """
        self.db = {}

    def write_hit(self, int_ip, port):
        """Write the hit in the dictionary database

        :param int_ip: The real, integer, value of the IP address.
        :param port: The port address of the chosen socket.
        """
        self.clean_db()
        try:
            db_user = self.db[int_ip]
            time_cond = (db_user['time'] + TTL) > int(time.time())
            if(db_user['last_port'] < port and time_cond):
                # Grant access, increase state
                if(db_user['state'] == 1):
                    log("Access granted! Hooray!")
                    del self.db[int_ip]
                    return True
                else:
                    db_user['state'] += 1
                    db_user['time'] = int(time.time())
                    db_user['last_port'] = port
            else:
                # Too late, reset state
                del self.db[int_ip]

        except KeyError:
            # Unknown user, initialize the db
            self.db[int_ip] = {
                'state': 0,
                'time': int(time.time()),
                'last_port': port
            }
        return False

    def clean_db(self):
        """This method should clean the database from old, already unuseful data.
        """
        pass


class Knock():
    """The objects of this class will handle the Knock action.
    """
    def __init__(self, sock, db, client_ip):
        """The object initializer. It will do all it's job from here.

        :param sock: The socket object.
        :param db: The database object.
        :param client_ip: The ip address of the client.
        """
        self.sock = sock
        self.db = db
        self.ip = client_ip
        self.handle_hit()

    def handle_hit(self):
        """This method will handle the hit,
        and if it is granted - will alter the firewall rules.
        """
        int_ip = self.ip2long(self.ip)
        port = self.sock.getsockname()[1]
        if(self.db.write_hit(int_ip, port)):
            self.alter_firewall(self.ip)

    def ip2long(self, ip):
        """This method will convert the str ip to the real integer value.

        :param ip: String representation of the ip.
        :return: Integer representation of the ip address.
        """
        return struct.unpack("!L", socket.inet_aton(ip))[0]

    def long2ip(self, int_ip):
        """This method will convert the integer ip back to string.

        :param int_ip: Integer ip.
        :return: String ip address.
        """
        return socket.inet_ntoa(struct.pack('!L', int_ip))

    def alter_firewall(self, ip):
        """This method will alter the firewall rules
        and it will schedule the new rule removal after 1 minute.

        :param ip: The client ip address.
        :return: True if anything went correct.
        """
        rule_enable = [
            'iptables',
            '-I', 'INPUT',
            '-m', 'state',
            '--state', 'NEW',
            '-p', 'tcp',
            '-s', ip,
            '--dport', '22',
            '-j', 'ACCEPT'
        ]
        enable = Popen(rule_enable)

        rule_disable = rule_enable[:]
        rule_disable[1] = '-D'
        rule_disable_str = " ".join(rule_disable)
        disable = Popen(["at", "now", "+", "1", "minute"], stdin=PIPE)
        disable.communicate(rule_disable_str)

        return (enable.wait() and disable.wait())


class KnockServer(asyncore.dispatcher):
    """The sockets will be initialized and handled by this class.
    """
    def __init__(self, host, port, db):
        """Class initializer. Creates the socket with given host, port, db object.

        :param host: Host for listening.
        :param port: Port of the socket.
        :param db: DictDB object.
        """
        asyncore.dispatcher.__init__(self)
        self.db = db

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(('', port))
        self.listen(5)
        log("Knock Socket initialized on port " + str(port))

    def handle_accept(self):
        """Predefined method that will handle the accepted connection.
        """
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            log('Incoming conn. from %s to %s' % (addr, sock.getsockname()))
            Knock(sock, self.db, addr[0])
            log(self.db)
            try:
                sock.send('Thank you for knocking\n')
            except socket.error:
                # Handle the pure knocking.
                log('Expected broken pipe')

            sock.close()
            # handler = KnockHandler(sock)

if __name__ == '__main__':
    db = DictDB()
    for i in xrange(SOCKETS):
        KnockServer('localhost', (START_PORT + i), db)

    asyncore.loop()

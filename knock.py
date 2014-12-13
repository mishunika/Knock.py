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

    def __str__(self):
        return str(self.db)

    def __init__(self):
        self.db = {}

    def write_hit(self, int_ip, port):
        self.clean_db()
        try:
            db_user = self.db[int_ip]
            time_cond = (db_user['time'] + TTL) > int(time.time())
            if(db_user['last_port'] < port and time_cond):
                # Grant access, increase state
                if(db_user['state'] == 1):
                    # Access granted. TODO: Alter the iptables rules.
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
        if(self.db.write_hit(int_ip, port)):
            self.alter_firewall(self.ip)

    def ip2long(self, ip):
        return struct.unpack("!L", socket.inet_aton(ip))[0]

    def long2ip(self, int_ip):
        return socket.inet_ntoa(struct.pack('!L', int_ip))

    def alter_firewall(self, ip):
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

    def __init__(self, host, port, db):
        asyncore.dispatcher.__init__(self)
        self.db = db

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(('', port))
        self.listen(5)
        log("Knock Socket initialized on port " + str(port))

    def handle_accept(self):
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

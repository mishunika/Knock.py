# Knock.py
###### student gr. FAF-111: Mihai Iachimovschi

## Intro
This is the final work for the subject BIE-ADS. The idea of the system is to create a script or a set of scripts that will allow the usage of a service by the method of "port knocking". The access to the service is denied by default. Client should connect to different ports with defined order in defined time interval which will grant the access for the user's ip to the service.

## Prerequisites
For this we need a machine running Linux with iptables and Python2 on it. Iptables should contain a rule that will reject all the incoming SSH traffic.

For example:

```
-A INPUT -p tcp -m state --state NEW -m tcp --dport 22 -j REJECT
```

We will use stateful firewall, so we will be able to block new connections but allow existing ones.

## System description
The system will create few sockets listening on defined ports (flexible). Connecting to a sequence of ports with increasing values will allow, temporarily, the access to the service for this particular client. When granting access the system will alter the iptables rules by adding this rule for the $IP_ADDR of the client:

```
-I INPUT -m state --state NEW -p tcp -s $IP_ADDR --dport 22 -j ACCEPT
```

And there will be scheduled a task that will alter again the iptables content after 1 minute by removing the previous rule, issuing this command:

```
iptables -D INPUT -m state --state NEW -p tcp -s $IP_ADDR --dport 22 -j ACCEPT
```

The scheduling is done by `at` *nix command.
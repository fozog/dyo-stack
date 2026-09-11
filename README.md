Do Your Own Stack is project to help developpers organise their home lab without deploying a full OpenStack or other huge framework. There is no need for isolated tenants and overlayed networks. Just configuring existing DNS and routing so that systems can boot PXE or HTTPboot, access any VM on any host with automated DNS and routing changes.

This project exists essentially to avoid forgetting the details, but should it be usefull for anyone, I am happy.

# Driving use case

As a developper I have several servers, embedded boards on my LAN that run VMs or need TFTP/PXE to boot.

I needed a full fledged DHCP server with control of options to support PXE policies and other features. In addition, and mainly for my cybersecurity posture, I wanted to use ntopng as a permanent observer of all incoming and outgoing traffic.

Because ISP Box DHCP and DNS do not provide flexibility to decorate DHCP response with the right options and is not helpful in observing behaviors, I use a dedicated gateway. 

```
                         [ WAN / Internet ]
                                  |
                       +---------------------+
                       |       ISP Box       |
                       +---------------------+
                                  |
                       +---------------------+
                       | LAN Gateway Server  |
                       |    (192.168.0.30)   |
                       | - dnsmasq (DHCP/DNS)|
                       | - ntopng (Monitor)  |
                       +---------------------+
                                  |
----------------------------------+---------------------------------- [ Switched LAN ]
        |                         |                         |
+-----------------------+ +-----------------------+ +-----------------------+
| Server 1              | | Server 2              | | Client Machine        |
|                       | |                       | |                       |
+-------+-------+-------+ +-------+-------+-------+ +-----------+-----------+
```
Many servers, including the gateway run VMs or containers. Each VM/Container amy need to have access to internet and I wanted a simple way to communicate with them directly.

I don't want to run OpenStack or Kubernetes or use network overlays so I designed a simple naming (DNS) and routing (RIP) environement to reach VM<x>.host<y>.home.arpa.

We thus have:
- box.home.arpa is the ISP box that has DHCP and DNS services stopped
- gw.home.arpa is the control point in the whole architecture
- server1.home.arpa, server2.home.arpa, mbp.home.arpa are nodes that can host VMs

It shall be possible from anywhere (server, client, vm) to communicate with any other element:
- vm1.server1.home.arpa, vm2.server1.home.arpa
- vm3.server2.home.arpa, vm4.server2.home.arpa
- vm1.mbp.home.arpa
```
                         [ WAN / Internet ]
                                  |
                       +---------------------+
                       |       ISP Box       |
                       +---------------------+
                                  |
                       +---------------------+
                       | LAN Gateway Server  |
                       |    (192.168.0.30)   |
                       | - dnsmasq (DHCP/DNS)|
                       | - ntopng (Monitor)  |
                       +---------------------+
                                  |
----------------------------------+---------------------------------- [ Switched LAN ]
        |                         |                         |
+-----------------------+ +-----------------------+ +-----------------------+
| Server 1 (libvirt)    | | Server 2 (libvirt)    | | Client Machine        |
| (192.168.0.10)        | | (192.168.0.11)        | | (192.168.0.150)       |
|     [ rvnet10]        | |       [rvnet11]       |        [rvnet150]       |
+-------+-------+-------+ +-------+-------+-------+ +-----------+-----------+
        |       |                 |       |                     |
   +----+---+ +-----+---+      +----+---+ +-----+---+        +----+---+
   |  VM1   | |  VM2    |      |  VM3   | |  VM4    |        |  VM1   |
   +--------+ +---------+      +--------+ +---------+        +--------+
```
Even if I have some Windows machines I just consider Linux and macOS systems.

macOS do not support any routing client, so I have to use RIPv2 as the global routing procol: I can code a crude Python RIPv2 "router".

# architecture

## tools capabilities and constraiunts

### network/routing
libvirt creates a default NAT network that manifests itself as virb0 and address 192.168.122.0/24. Because of NAT, that prefix cannot be routed to hosts on the LAN or to other VMs.

Apple container creates a default NAT that manifests itself as virb0 and address 192.168.64.0/24. Because of NAT, that prefix cannot be routed to hosts on the LAN.

Docker creates a default network with prefix 172.16/12.

### DNS
libvirt runs a dedicated dnsmasq that maintains <vm name> <DHCP address> associations. This can thus be leveraged by a central dnsmasq which can forward request to the right dnsmasq

## Policies


Each host will be running a routing capable virtual network. Address space will be such that host 192.168.0.x will host a 172.22.x.0/24 network. It will run a RIP capable router, excluding distributing some networks such as the non-routable NAT support networks such as 192.168.122.0/24 from libvirt.

The central dnsmasq server will use matching rules such as 
server=/*.server2.home.arpa/192.168.0.11
to redirect name resolution requests to the "authoritative" server for the VMs.
NOTE: I failed to use authoritative zone and server directives because dnsmasq have specific behavior and cannot recurse requests to non local domains. So it is not about declaring NS for server2.home.arpa, this is a simple DNS request redirect based on matching rule.

Servers can change IP addresses, the GW instance of dnsmasq need to be adapted when a host IP changes: there is a need of a ssh accessible toolset in the GW.

gw.md describes what has to be done on the gw side

host.md describes what has to be done on servers and clients

vm.md describe what need to be done inside the VM and cloud-init parameters to automate creation. It also gives some tricks to control networking aspects (interface ordering and naming).

virt-manager.md give tricks to get things running in multi-OS environment (virt-amanger on macOS has troubles to control Linux libvirt hosts) or with custom drivers (other VMM than known ones such as Qemu)
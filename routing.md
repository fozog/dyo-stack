This about routing for Hosts and GW of the LAN, not for the VMs.
See vm.md for routing configuration

# Linux
The following says that RIP operates on the LAN interface (network 192.168.0.0/24) and on the local routed virtual network for libvirt (network 172.22.30.0/24). You may want to add other bridges should you want to include a particular network. 


Get information on bridges with the custom tool
```
# custom tool
lsbridges
```

Or manually

```
#linux alternative
ip link show type bridge
# macos alternative


#Check which ones are docker:

 sudo docker network ls --filter driver=bridge --format '{{.ID}}' | xargs -r sudo docker network inspect --format '{{index .Options "com.docker.network.bridge.name"}}' | grep -v '^$'
```

Each node (GW, VM servers, desktops) will have to decide on which interfaces RIP is operating and which interfaces they publish.
For this last aspect, the easiest to say "publish every thing" except what does not make sense such as the NATed networks for libvirt  (192.168.122.0/24) 

Use either vtysh command to configure the router (conf terminal) or edit or /etc/frr/frr.conf
```
router rip
! propagate on LAN
 network 192.168.0.0/24
 ! propagate on libvirt bridge
 network 172.22.30.0/24
 redistribute connected route-map REDIST-CONNECTED

! do not public libvirt NATed network
ip prefix-list CONNECTED-TO-RIP seq 10 deny 192.168.122.0/24
! any other network is fine to publish
ip prefix-list CONNECTED-TO-RIP seq 20 permit 0.0.0.0/0 le 32

route-map REDIST-CONNECTED permit 10
 match ip address prefix-list CONNECTED-TO-RIP
```

# macOS

macOS do not have a RIP or OSPF official client. Projects I found where 8 years old as of writing in 2026 and did not compile. so I decided to create yet another project macRIP to have the minimal routing functionalitythat matches the requirements of the driving use case.
see https://github.com/fozog/mac-rip


# Libvirt & Qemu Install

## Linux

Lets allow users to call virsh to avoid using root all the time...

```
export USER=<your name>
sudo apt install qemu-system qemu-efi-aarch64
sudo apt install libvirt-daemon-system libvirt-clients virt-install acl
sudo apt install cloud-image-utils
sudo usermod -aG libvirt,kvm  $USER
sudo systemctl start libvirtd
```

## macOS

```
brew install qemu-system qemu-efi-aarch64
brew install libvirt-daemon-system libvirt-clients virt-install acl
brew install cloud-image-utils
```



# checks

some commands to validate install
```
virsh version
systemctl status libvirtd
virsh -c qemu:///system list --all
virsh -c qemu:///system capabilities >/dev/null && echo "QEMU/libvirt OK"
```



# networking preparation

## vlan creation
the create_vlan tool has been provided to create the routable VLAN for all the VMs of this machine.

update the vlan.xml definition for local routable vlan. The selected prefix can be any local address space. Our assumption is to use 172.22.x.0/24 for host 192.168.0.x.

```
<network>
  <name>vlan</name>
  <forward mode='route'/>
  <bridge name='vlanbr0'/>
  <ip address='172.22.30.1' netmask='255.255.255.0'>
    <dhcp>
      <range start='172.22.30.2' end='172.22.30.254'/>
    </dhcp>
  </ip>
  <domain name="adainville.home.arpa" localOnly="yes"/>
</network>


Then effectively create the VLAN with libvirt.

create_vlan tool has been provided for that:
```
# the LAN network is used to communicate between VMs and Hosts on the LAN
if [ "$(virsh net-list --all | grep vlan)" == "" ]; then 
    # lan.xml shall be updated with
    # - FQDN on the machine on which it is running
    # - unique prefix that is routable on the LAN
    virsh net-define vlan.xml
    virsh net-autostart vlan
    virsh net-start vlan
fi
```
```

# VMs

Then for each VM created see what has to be done in vm.md
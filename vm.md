# resource pool creation (to allow distant virt-manager to use them)

Make sure the images are exposed remotely
allow libvirt-qemu programs to traverse /home/ff
sudo setfacl -m u:libvirt-qemu:--x /home/ff
virsh pool-define-as resilience-vm-pool dir --target ~/resilience/probe/vm
virsh pool-start resilience-vm-pool
virsh pool-autostart resilience-vm-pool


# VM creation

## Disk images

```
cd @base-images
wget https://cdimage.ubuntu.com/ubuntu/releases/26.04.1/release/ubuntu-26.04.1-preinstalled-server-arm64.img.xz
cd ../vm
unxz -kc ../@base-images/ubuntu-26.04.1-preinstalled-server-arm64.img.xz > disk1-ubuntu26.04.1.img
qemu-img resize -f raw disk1-ubuntu-26.04.1.img  32G
#lets check the size has been properly done (disk occupation vs size)
qemu-img info disk1-ubuntu26.04.1.img
# for resource pool stuff
sudo chown libvirt-qemu:kvm disk1-ubuntu26.04.1.img
```

update cloud-init/user-metadata and create the cloud-init.iso image
```
cloud-localds cloud-init.iso cloud-init/user-data cloud-init/meta-data 
# for resource pool stuff
sudo chown libvirt-qemu:kvm cloud-init.iso
```


## libvirt domain

Note the following example use 3 network interfaces.
Rhe first for internet access (default), the second for routed access from the LAN (vlan).
The third one is used to play with DPDK in a VM but there can be many more interfaces.
The PCI addresses are use to force the order of apperance in the VM.
In the VM, the PCIbus X will lead to eth<x> or end<x> or enp<x>s0 dependeing on the Linux distribution and its version. With this control it becomes simple to create the VM with a cloud-init that can easily add a Netplan
```
export VM_ROOT=~/slow/vms/resilience
export VM_DISK=disk1-ubuntu26.04.1.img
ethernet interfaces are assigned a PCI bus to control naming:
bus=0x06 VM name is enp7s0
bus=0x07 VM name is enp8s0
bus=0x08 VM name is enp9s0
virt-install \
  --connect qemu:///system \
  --name VM \
  --arch aarch64 \
  --machine virt \
  --virt-type kvm \
  --qemu-commandline="-nodefaults" \
  --memory 2048 \
  --vcpus 4 \
  --boot loader=/usr/share/AAVMF/AAVMF_CODE.fd,loader.readonly=yes,loader.type=pflash,nvram.template=/usr/share/AAVMF/AAVMF_VARS.fd \
  --import --noautoconsole \
  --os-variant ubuntu-stable-latest \
  --disk path=${VM_ROOT}/${VM_DISK},bus=virtio \
  --disk path=${VM_ROOT}/cloud-init.iso,device=cdrom \
  --network network=default,model=virtio,address.type=pci,address.domain=0x0000,address.bus=0x06,address.slot=0x00,address.function=0x0 \
  --network network=vlan,model=virtio,address.type=pci,address.domain=0x0000,address.bus=0x07,address.slot=0x00,address.function=0x0 \
  --network type=ethernet,model=virtio,address.type=pci,address.domain=0x0000,address.bus=0x08,address.slot=0x00,address.function=0x0
```

to check connectivity:
```
virsh console VM
virsh -c qemu+ssh://mcbin-gw/system console VM

# On french keyboard layouts Ctlr-$ to exit console
```

# VM configuration for routed access


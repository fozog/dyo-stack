
add hugepages in grub
GRUB_CMDLINE_LINUX="intel_iommu=on iommu=pt hugepagesz=2M hugepages=64 quiet splash"
update /etc/fstab
nodev /dev/hugepages hugetlbfs rw,mode=0775,uid=ff,gid=ff 0 0


### preparing the development environment in the VM

sudo apt update
sudo apt install build-essential python3-pip meson ninja-build libnuma-dev python3-pyelftools pkg-config

clone DPDK

meson setup build
ninja -C build
meson install
sudo ldconfig
sudo  mkdir -p /dev/hugepages
sudo mountpoint -q /dev/hugepages || mount -t hugetlbfs nodev /dev/hugepages
sudo su
    echo 64 > /sys/devices/system/node/node0/hugepages/hugepages-2048kB/nr_hugepages


# virt-manager context

## Networking

### Linux
transient route:
sudo route -n add -net 192.168.123.0/24 192.168.0.30

### macOS

permanent route :
sudo networksetup -setadditionalroutes "Thunderbolt Ethernet Slot 0, Port 2" 192.168.123.0 255.255.255.0 192.168.0.30



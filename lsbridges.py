#!/usr/bin/env python3
import ipaddress
import json
import re
import shutil
import subprocess
import sys

def sh(cmd: str) -> str:
    """Runs a shell pipeline and returns stdout as string (ignoring errors)."""
    try:
        return subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True).stdout.strip()
    except Exception:
        return ""

def sudo_sh(test_cmd: str, run_cmd: str, err_label: str) -> str:
    """Runs a sudo command if password-less sudo succeeds, otherwise prints error to stderr."""
    if subprocess.run(f"sudo -n {test_cmd} >/dev/null 2>&1", shell=True).returncode != 0:
        print(f"Lacks password-less sudo {err_label}", file=sys.stderr)
        return ""
    return sh(run_cmd)

def normalize_cidr(val: str) -> str:
    if not val:
        return ""
    try:
        if "/" in val:
            ip_str, mask = val.split("/", 1)
            if mask.lower().startswith("0x"):
                mask = str(ipaddress.IPv4Address(int(mask, 16)))
            val = f"{ip_str}/{mask}"
        return str(ipaddress.ip_network(val, strict=False))
    except Exception:
        return val

def get_iface_subnet(b: str) -> str:
    if shutil.which("ip"):
        return sh(f"ip -4 -o addr show dev '{b}' | awk '{{print $4}}'")
    return sh(f"ifconfig '{b}' 2>/dev/null | awk '/inet / {{print $2 \"/\" $4}}'")

def main():
    # 1. Discover OS bridges
    if shutil.which("ip"):
        raw_bridges = sh("ip -br link show type bridge | awk '{print $1}'")
    else:
        raw_bridges = sh("ifconfig 2>/dev/null | awk '/^[^[:space:]]/ {iface=$1; sub(/:.*/, \"\", iface)} /^[[:space:]]+member:/ {print iface}' | sort -u")

    bridges = {b: "OS" for b in raw_bridges.split() if b}
    prefix = {}

    def update_tags(tag: str, bridge_list: list):
        for b in bridge_list:
            if not b:
                continue
            if bridges.get(b) == "OS":
                bridges[b] = tag
            else:
                print(f"Error: Bridge '{b}' was not found as an OS bridge or had an unexpected value ('{bridges.get(b)}').", file=sys.stderr)

    # 2. Docker
    if shutil.which("docker"):
        dock_out = sudo_sh("docker network ls",
                           "sudo -n docker network ls --filter driver=bridge --format '{{.ID}}' | xargs -r sudo -n docker network inspect 2>/dev/null",
                           "docker")
        if dock_out:
            try:
                for net in json.loads(dock_out):
                    bname = (net.get("Options") or {}).get("com.docker.network.bridge.name") or ("docker0" if net.get("Name") == "bridge" else f"br-{net.get('Id', '')[:12]}")
                    if bname in bridges:
                        update_tags("Docker", [bname])
                        cfg = (net.get("IPAM") or {}).get("Config") or []
                        if cfg and cfg[0].get("Subnet"):
                            prefix[bname] = cfg[0]["Subnet"]
            except Exception:
                pass

    # 3. Libvirt
    if shutil.which("virsh"):
        v_nets = sudo_sh("virsh net-list", "sudo -n virsh net-list --name", "virsh")
        for net in v_nets.split():
            xml = sh(f"sudo -n virsh net-dumpxml '{net}' 2>/dev/null")
            bm = re.search(r"<bridge name='([^']+)'", xml)
            if bm and bm.group(1) in bridges:
                bname = bm.group(1)
                update_tags("Libvirt", [bname])
                ip_m = re.search(r"<ip address='([^']+)'", xml)
                mask_m = re.search(r"netmask='([^']+)'", xml)
                if ip_m:
                    prefix[bname] = f"{ip_m.group(1)}/{mask_m.group(1)}" if mask_m else f"{ip_m.group(1)}/24"

    # 4. Snap (LXD)
    if (shutil.which("snap") and sh("snap list lxd 2>/dev/null")) or shutil.which("lxc"):
        lxc_out = sudo_sh("lxc network list", "sudo -n lxc network list --format csv -c n,t", "lxc")
        for line in lxc_out.splitlines():
            parts = line.split(",")
            if len(parts) >= 2 and parts[1] == "bridge" and parts[0] in bridges:
                bname = parts[0]
                update_tags("Snap (LXD)", [bname])
                prefix[bname] = sh(f"sudo -n lxc network get '{bname}' ipv4.address 2>/dev/null")

    # 5. Apple Container
    if shutil.which("container"):
        c_list = sh("container network list 2>/dev/null | awk 'NR>1 {print $1}'")
        if c_list:
            c_inspect = sh(f"container network inspect {c_list} 2>/dev/null")
            try:
                for net in json.loads(c_inspect):
                    gw = (net.get("status") or {}).get("ipv4Gateway")
                    sn = (net.get("status") or {}).get("ipv4Subnet")
                    for b in list(bridges.keys()):
                        b_ip = get_iface_subnet(b).split("/")[0]
                        if b_ip and (b_ip == gw or (sn and ipaddress.ip_address(b_ip) in ipaddress.ip_network(sn, strict=False))):
                            update_tags("Apple Container", [b])
                            if sn:
                                prefix[b] = sn
            except Exception:
                pass

    # 6. Fallback subnet resolution and output
    for b in sorted(bridges.keys()):
        raw = prefix.get(b) or get_iface_subnet(b)
        print(f"{b} : {bridges[b]} : {normalize_cidr(raw)}")

if __name__ == "__main__":
    main()

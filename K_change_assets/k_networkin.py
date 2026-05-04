import subprocess
import socket
import threading

import k_values


def eliminate(text) -> str:
    j = ''
    for i in range(len(text)):
        if text[i] in '0123456789':
            j = text[i:]
            break

    for i in range(len(j) - 1, -1, -1):
        if j[i] in '0123456789':
            j = j[:i + 1]
            break
    return j


def get_ip_and_subnet() -> list[tuple[str, str]]:  # list of (ip,subnet mask)

    # Run the 'ipconfig' command and capture the output
    result = subprocess.run('ipconfig', shell=True, capture_output=True, universal_newlines=True)
    output = result.stdout

    ip_address = None
    subnet_mask = None
    j = []
    for line in output.lower().splitlines():

        if 'ipv4 address' in line:
            ip_address = eliminate(line[12:])
        elif 'subnet mask' in line:
            subnet_mask = eliminate(line[11:])
            j.append((ip_address, subnet_mask))
    return j


def get_ip_range() -> list[tuple[int, int]]:  # ip start, ip finish
    ips = get_ip_and_subnet()
    j = []
    for i in ips:
        ip_parts = i[0].split('.')
        mask_parts = i[1].split('.')
        j1s = 0
        j2s = 0
        for l in range(4):
            j1 = int(ip_parts[l]) & int(mask_parts[l])
            jt = int(mask_parts[l]) ^ 255
            j2 = jt | int(ip_parts[l])
            j1s = j1s * 256 + j1
            j2s = j2s * 256 + j2
        j.append((j1s + 1, j2s - 1))
    return j


def to_ip(IP: int) -> str:
    ip = str(IP // 16777216)
    ip += '.' + str(IP % 16777216 // 65536)
    ip += '.' + str(IP % 65536 // 256)
    ip += '.' + str(IP % 256)
    return ip


def scan_ip(IP: int, port: int) -> bool:
    global scan_found
    ip = to_ip(IP)
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket.setdefaulttimeout(k_values.connection_timeout)
    result = soc.connect_ex((ip, port))
    if result == 0:
        print('Open port found:', ip, ':', port)
        scan_found = ip
        soc.close()

    soc.close()


def scan_chunk(start, stop, port):
    global scan_found
    threads = []
    print("Scanning range", to_ip(start) + '-' + to_ip(stop) + '...')
    for i in range(start, stop + 1):
        if scan_found == None:
            threading.Thread()
            threads.append(threading.Thread(target=lambda: scan_ip(i, port)))
            threads[-1].start()
    alive = True
    while alive:
        alive = False
        for i in threads:
            if i.is_alive():
                alive = True


def scan_network(port: int) -> str:  # ip address
    global scan_found
    scan_found = None
    ips = get_ip_range()
    print('scanning')

    for ip_start, ip_end in ips:
        for IP in range(ip_start, ip_end + 1, k_values.max_threads):
            if scan_found == None:
                scan_chunk(IP, min(IP + k_values.max_threads, ip_end + 1), port)
            else:
                return scan_found
    print('Not found setting to default(127.0.0.1)')
    return '127.0.0.1'


if __name__ == "__main__":
    ip_addr, subnet = zip(*get_ip_and_subnet())
    if ip_addr:
        print("Your IP Address:", ip_addr)
        print("Your Subnet Mask:", subnet)
    else:
        print("Could not determine IP address and subnet mask")

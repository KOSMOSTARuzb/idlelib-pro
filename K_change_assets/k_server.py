import socket
import re
import threading
import os
try:
    from idlelib import k_values, k_networkin
except (ImportError, ModuleNotFoundError):
    import k_values
    import k_networkin

PORT = k_values.port
storage_path = './downloads'
if not os.path.exists(storage_path):
    os.mkdir(storage_path)


class Connection:
    def __init__(self, conn: socket.socket, addr):
        self.connection = conn
        self.address = addr
        print("Connection by", addr)

    def run(self):
        while True:
            data = self.connection.recv(k_values.max_bytes_to_transfer)
            if not data:
                print("Disconnected:", self.address)
                break
            text = str(data.decode('utf-8'))
            parts = text.split(':', 1)
            command = parts[0]
            if command == 'send':
                parts = parts[1].split('\n', 1)
                slot = self.validate_filename(parts[0]).strip()
                context = parts[1]
                self.save_to_file(slot, context)
                print('File received:', slot)
            elif command == 'recv':
                slot = self.validate_filename(parts[1]).strip()
                content = self.get_file_contents(slot)
                self.connection.sendall(content.encode('utf-8'))
                print('File sent:', slot)

    def save_to_file(self, filename: str, content: str):
        with open(os.path.join(storage_path, filename), 'w') as file:
            file.write(content)

    def get_file_contents(self, filename: str) -> str:
        path = os.path.join(storage_path, filename)
        if not os.path.exists(path):
            return k_values.null
        with open(path, 'r') as file:
            j = file.read()
        return j

    def validate_filename(self, org: str) -> str:

        # 1. Replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*\.]', '_', org)
        filename = filename.replace("\'", '')

        # 2. Remove leading/trailing spaces/dots
        filename = filename.strip(' ._')

        # 3. Replace multiple spaces with a single underscore
        filename = re.sub(r'\s+', '_', filename)

        # 4. Convert to lowercase
        filename = filename.lower()

        # 5. Check for reserved names (case-insensitive)
        reserved_names = ('con', 'prn', 'aux', 'nul', 'com1', 'com2', 'com3', 'com4', 'com5',
                          'com6', 'com7', 'com8', 'com9', 'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5',
                          'lpt6', 'lpt7', 'lpt8', 'lpt9')
        if filename in reserved_names:
            filename = f'_{filename}'  # Prepend an underscore

        # 6. Truncate to a maximum length
        MAX_FILENAME_LENGTH = 255
        filename = filename[:MAX_FILENAME_LENGTH]

        # 7. Handle empty inputs
        if len(filename) == 0:
            filename = "__"

        return filename


class Server:
    def __init__(self, HOST: str, PORT: int):
        self.ip = HOST
        self.port = PORT
        self.thread = threading.Thread(target=self.__run__)

        self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connections = []
        print('IP:', self.ip)

        self.soc.bind((self.ip, self.port))
        self.soc.listen()

    def start(self):
        self.thread.start()

    def __run__(self):
        print(f"Waiting for clients({self.ip})...")
        try:
            while True:
                conn, addr = self.soc.accept()
                connection = Connection(conn, addr)
                thread = threading.Thread(target=connection.run)
                self.connections.append(thread)
                thread.start()
        except Exception as e:
            print(f"ERROR({self.ip}):", e)
            self.soc.close()


servers = []
HOSTs, SUBNETs = zip(*k_networkin.get_ip_and_subnet())

for host in HOSTs:
    server = Server(host, PORT)
    servers.append(server)
    server.start()
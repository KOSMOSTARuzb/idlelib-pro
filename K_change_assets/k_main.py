import tkinter, tkinter.messagebox

from pynput.keyboard import Key, Listener
import socket
import threading
import pymsgbox
import time
import k_values
import k_networkin

HOST = None
PORT = k_values.port
scan_found = None
uploading = None
downloading = None
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
is_connected = False
is_connecting = False
disable_next_popup = False


def send_msg(sock, msg):
    # Prefix each message with its length (10 digits)
    msg_bytes = msg.encode('utf-8')
    header = f"{len(msg_bytes):010d}".encode('utf-8')
    sock.sendall(header + msg_bytes)


def recv_msg(sock):
    # Read the 10-byte header
    header = b''
    while len(header) < 10:
        chunk = sock.recv(10 - len(header))
        if not chunk:
            return None
        header += chunk
    try:
        msg_len = int(header.decode('utf-8'))
    except ValueError:
        return None

    # Read the message content
    msg = b''
    while len(msg) < msg_len:
        chunk = sock.recv(min(msg_len - len(msg), 4096))
        if not chunk:
            return None
        msg += chunk
    return msg.decode('utf-8')


class KeyListner:
    def __init__(self):
        self.listener = Listener(on_press=self.onpress)
        self.key = None
        self.got = 0
        self.listener.start()

    def onpress(self, key):
        if self.got == 0:
            self.key = str(key)
        elif self.got == k_values.number_of_chars - 1:
            self.key += str(key)
            self.listener.stop()
            return 0
        else:
            self.key += str(key)
        self.got += 1


def get_next_key() -> str:
    KL = KeyListner()
    while KL.got < k_values.number_of_chars:
        time.sleep(0.1)
    time.sleep(0.1)
    return str(KL.key)


def show_error(e: str):
    global disable_next_popup
    if disable_next_popup:
        disable_next_popup = False
        return None
    try:
        tkinter.NoDefaultRoot()
        tkinter.messagebox.showerror('Error', str(e))
    except:
        try:
            pymsgbox.alert(e, 'Error')
        except:
            try:
                print(e)
            except:
                pass


def change_editor_state(editr, enable=True):
    to_state = 'normal' if enable else 'disabled'
    try:
        editr.root.after(0, lambda: editr.text.config(state=to_state))
    except Exception as e:
        print(e)


def get_connected(editr=None):
    global is_connected, HOST, is_connecting, s
    if is_connecting:
        # show_error("Stand by,\n\nLaunching Python Interpreter...")
        if not editr == None:
            change_editor_state(editr, False)
            while is_connecting:
                time.sleep(1)
            change_editor_state(editr)
        return False
    else:
        is_connecting = True
        if not editr == None:
            change_editor_state(editr, False)
    try:
        if HOST == None:
            HOST = k_networkin.scan_network(PORT)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(k_values.connection_timeout)
        s.connect((HOST, PORT))

        # Sync slot length from server
        init_msg = recv_msg(s)
        if init_msg and init_msg.startswith('init:'):
            try:
                k_values.number_of_chars = int(init_msg.split(':')[1])
            except:
                pass

        is_connected = True
        is_connecting = False
        if not editr == None:
            change_editor_state(editr)
        return True
    except ConnectionRefusedError:
        if not editr == None:
            change_editor_state(editr)
        show_error("Unable to launch Python IDE.")
    except Exception as e:
        if not editr == None:
            change_editor_state(editr)
        show_error("Unable to launch Python IDE.\n\n" + str(e))
    is_connecting = False
    return False


def uploader(slot: str, content):
    global uploading, is_connected
    if slot == 'f7':
        return None
    if not is_connected:
        if not get_connected():
            show_error('Not launched, try restarting the app...')
        return False
    content = 'send:' + slot + '\n' + content
    try:
        send_msg(s, content)
    except Exception as e:
        is_connected = False
        show_error("Failed to save file: " + str(e) + "\n\nYou may safely ignore this error.")
        return False
    print('done')
    uploading = None
    return True


def upload(_: str):
    print("upload command")
    global uploading
    if uploading == None:
        uploading = threading.Thread(target=lambda: uploader(get_next_key(), _))
        uploading.start()
    elif type(uploading) == threading.Thread:
        if not uploading.is_alive():
            uploading = threading.Thread(target=lambda: uploader(get_next_key(), _))
            uploading.start()
        else:
            show_error('Work in progress...\nPlease wait before trying again.')

    else:
        show_error('Work in progress...\nPlease wait before trying again.')


def downloader(slot: str):
    global is_connected
    if slot == 'f8':
        return None
    if not is_connected:
        if not get_connected():
            show_error('Not launched, try restarting the app...')
        return None
    content = 'recv:' + slot
    try:
        send_msg(s, content)
        print('requested, waiting...')
        content = recv_msg(s)
    except Exception as e:
        is_connected = False
        show_error("Download failed: " + str(e))
        return None
    print('received')
    if content == k_values.null:
        print('Nothing')
        return None
    return content


def download() -> str | None:
    print("download command")
    global downloading
    slot = get_next_key()
    return downloader(slot)


def comment_code(org: str, new: str) -> str:
    if not k_values.comment_existing_code:
        return new
    lines = org.strip().splitlines()
    new = ""
    for i in lines:
        if i.strip():
            new = new + '\n# ' + i
    return org + '\n' + '#'*10 + '\n' + new


if __name__ == '__main__':
    try:
        import idlelib.pyshell
    except ImportError:
        print(3)
        from . import pyshell
        import os

        idledir = os.path.dirname(os.path.abspath(pyshell.__file__))
        if idledir != os.getcwd():
            pypath = os.environ.get('PYTHONPATH', '')
            if pypath:
                os.environ['PYTHONPATH'] = pypath + ':' + idledir
            else:
                os.environ['PYTHONPATH'] = idledir
        pyshell.main()
    else:
        idlelib.pyshell.main()

from tkinter import *
import json
from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
import time

from DiffieHelman import DiffieHelm
from aes.aes import encrypt, decrypt


class User:
    with open('configs/connect-config.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    HOST = data["host"]
    PORT = data["port"]
    BUFSIZ = data["bifsiz"]
    ADDR = (HOST, PORT)

    def __init__(self, title=None):
        self.root = Tk()
        self.root.geometry("700x700")
        self.root.wm_title(title)

        self.a_text = Text(self.root, width=60, height=3, selectbackground="black", state=DISABLED)
        self.g_text = Text(self.root, width=60, height=3, selectbackground="black", state=DISABLED)
        self.p_text = Text(self.root, width=60, height=3, selectbackground="black", state=DISABLED)
        self.key_text = Text(self.root, width=60, height=3, selectbackground="black", state=DISABLED)

        self.sb = Scrollbar(self.root)
        self.mylist = Listbox(self.root, yscrollcommand=self.sb.set, width=50)
        self.message_text = Text(self.root, width=60, height=3, selectbackground="black")

        self.diffie_user = DiffieHelm()

    def draw_widget(self) -> None:
        Label(self.root, text="a:", justify=LEFT, font="Elephant 15").grid(row=0, column=0, sticky=W)
        self.a_text.grid(row=1, column=0, sticky=W)

        Label(self.root, text="g:", justify=LEFT, font="Elephant 15").grid(row=2, column=0, sticky=W)
        self.g_text.grid(row=3, column=0, sticky=W)

        Label(self.root, text="p:", justify=LEFT, font="Elephant 15").grid(row=4, column=0, sticky=W)
        self.p_text.grid(row=5, column=0, sticky=W)

        Label(self.root, text="key:", justify=LEFT, font="Elephant 15").grid(row=8, column=0, sticky=W)
        self.key_text.grid(row=9, column=0, sticky=W)

        Label(self.root, text="chat:", justify=LEFT, font="Elephant 15").grid(row=10, column=0, sticky=W)
        self.sb.grid(row=11, column=0, sticky=W)
        self.message_text.grid(row=12, column=0, sticky=W, pady=20)
        self.mylist.grid(row=11, column=0, sticky=W)
        self.sb.config(command=self.mylist.yview)

    def generate_parameters_to_send(self) -> None:
        self.diffie_user.generate_parameters_client()
        self._insert_to_text(a_text=self.diffie_user.a, p_text=self.diffie_user.p, g_text=self.diffie_user.g)

    def _insert_to_text(self, **kwargs) -> None:
        for k, v in kwargs.items():
            getattr(self, k).configure(state=NORMAL)
            getattr(self, k).delete('1.0', END)
            getattr(self, k).insert('1.0', v)
            getattr(self, k).configure(state=DISABLED)

    def get_text(self, widget: str) -> str:
        return getattr(self, widget).get("1.0", 'end-1c')

    def run_app(self) -> None:
        self.draw_widget()
        self.root.mainloop()


class Client(User):

    def __init__(self, title=None):
        super().__init__(title)
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.client_socket.connect(self.ADDR)

    def __draw_client_widget(self) -> None:
        Button(self.root, text="Сгенерировать", command=lambda: self.generate_parameters_to_send()).grid(row=6,
                                                                                                         column=0,
                                                                                                         sticky=W,
                                                                                                         pady=10)
        Button(self.root, text="Отправить серверу", command=lambda: self.send_to_server(), height=2,
               width=30, font=5).grid(row=7, column=0, sticky=W, pady=10)

        Button(self.root, text="Отправить сообщение", command=lambda: self.send_to_server_message(), height=2,
               width=30, font=5).grid(row=12, column=2, pady=40)

    def send_to_server(self) -> None:
        for data in [self.diffie_user.p, self.diffie_user.g, self.diffie_user.residue_division]:
            data = data.to_bytes((data.bit_length() + 7) // 8, 'big') or b'\0'
            self.send(data)

    def send_to_server_message(self) -> None:
        message = self.get_text("message_text")
        if len(message) % 16 != 0:
            message += ' ' * (16 - len(message) % 16)
        self.mylist.insert(END, f'Клиент: {self.get_text("message_text")}')

        message = message.encode('utf-8')
        res = []
        for i in range(len(message) // 16):
            res.append(encrypt(message[i * 16:i * 16 + 16], self.get_text("key_text")))
        out = res[0]
        if len(res) > 1:
            for array in res[1:]:
                out += array
        self.send(bytes(out))

    def data_handling(self, data) -> None:
        data = int.from_bytes(data, 'big')
        self.diffie_user.stranger_division = data
        self.diffie_user.generate_key()
        self._insert_to_text(key_text=self.diffie_user.key)

    def receive(self) -> None:
        check_key = True
        while True:
            try:
                msg = self.client_socket.recv(1024)
                if check_key:
                    self.data_handling(msg)
                    check_key = False
                else:
                    self.decode_message(msg)
            except OSError:
                break

    def decode_message(self, msg: bytes) -> None:
        msg = list(msg)
        result_message = ''
        for i in range(len(msg) // 16):
            result_message += ''.join(list(map(chr, decrypt(msg[i * 16:i * 16 + 16], str(self.diffie_user.key)))))

        self.mylist.insert(END, f'Сервер: {result_message.strip()}')

    def send(self, data: bytes) -> None:
        self.client_socket.send(data)
        time.sleep(0.5)

    def run_app(self) -> None:
        self.draw_widget()
        self.__draw_client_widget()
        receive_thread = Thread(target=self.receive)
        receive_thread.start()
        self.root.mainloop()


class Server(User):

    def __init__(self, title=None):
        super().__init__(title)

        self.SERVER = socket(AF_INET, SOCK_STREAM)
        self.SERVER.bind(self.ADDR)
        self.ACCEPT_THREAD = None
        self.addresses = {}
        self.data = []

    def generate_parameters_to_send(self) -> None:
        self.diffie_user.generate_parameters_server()
        self._insert_to_text(a_text=self.diffie_user.a, p_text=self.diffie_user.p, g_text=self.diffie_user.g)

    def __draw_server_widget(self) -> None:
        Button(self.root, text="Отправить сообщение", command=lambda: self.send_to_client_message(), height=2,
               width=30, font=5).grid(row=13, column=0, sticky=W, pady=10)

    def send_to_client_message(self) -> None:
        message = self.get_text("message_text")
        if len(message) % 16 != 0:
            message += ' ' * (16 - len(message) % 16)
        self.mylist.insert(END, f'Сервер: {self.get_text("message_text")}')

        message = message.encode('utf-8')
        res = []
        for i in range(len(message) // 16):
            res.append(encrypt(message[i * 16:i * 16 + 16], self.get_text("key_text")))
        out = res[0]
        if len(res) > 1:
            for array in res[1:]:
                out += array

        for clients in self.addresses:
            self.send_message(clients, bytes(out), key=False)

    def create_socket_server(self) -> None:
        self.SERVER.listen(5)
        print("ожидание соединения")
        self.ACCEPT_THREAD = Thread(target=self.accept_incoming_connections)
        self.ACCEPT_THREAD.start()

    def accept_incoming_connections(self) -> None:
        while True:
            client, client_address = self.SERVER.accept()
            print(f"{client_address[0]}:{client_address[1]} соединено")
            self.addresses[client] = client_address
            Thread(target=self.handle_client, args=(client,)).start()

    def handle_client(self, client: socket) -> None:
        check_key = True
        while True:
            msg = client.recv(self.BUFSIZ)
            if check_key:
                self.data.append(msg)
                if len(self.data) == 3:
                    self.data_handling(self.data, client)
                    self.data = []
                    check_key = False
            else:
                self.decode_message(msg)

    @staticmethod
    def send_message(client: socket, msg: int | bytes, key=True) -> None:
        if key:
            msg = msg.to_bytes((msg.bit_length() + 7) // 8, 'big') or b'\0'
        client.send(msg)

    def decode_message(self, msg: bytes) -> None:
        msg = list(msg)
        result_message = ''
        for i in range(len(msg) // 16):
            result_message += ''.join(list(map(chr, decrypt(msg[i * 16:i * 16 + 16], str(self.diffie_user.key)))))

        self.mylist.insert(END, f'Клиент: {result_message.strip()}')

    def data_handling(self, data: list, client: socket) -> None:
        self.diffie_user.p = int.from_bytes(data[0], "big")
        self.diffie_user.g = int.from_bytes(data[1], "big")
        self.diffie_user.stranger_division = int.from_bytes(data[2], "big")

        self.diffie_user.generate_parameters_server()

        self._insert_to_text(a_text=self.diffie_user.a, p_text=self.diffie_user.p, g_text=self.diffie_user.g,
                             key_text=self.diffie_user.key)

        self.send_message(client, self.diffie_user.residue_division)

    def run_app(self) -> None:
        self.draw_widget()
        self.__draw_server_widget()
        self.create_socket_server()
        self.root.mainloop()

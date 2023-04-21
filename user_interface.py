from tkinter import *
import json
from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread

from DiffieHelman import DiffieHelm


class User:
    def __init__(self, title=None):
        self.root = Tk()
        self.root.geometry("700x700")
        self.root.wm_title(title)

        self.a_text = Text(self.root, width=60, height=3, selectbackground="black", state=DISABLED)
        self.g_text = Text(self.root, width=60, height=3, selectbackground="black", state=DISABLED)
        self.p_text = Text(self.root, width=60, height=3, selectbackground="black", state=DISABLED)

        self.diffie_user = DiffieHelm()

    def draw_widget(self) -> None:
        Label(self.root, text="a:", justify=LEFT, font="Elephant 15").grid(row=0, column=0, sticky=W)
        self.a_text.grid(row=1, column=0, sticky=W)

        Label(self.root, text="g:", justify=LEFT, font="Elephant 15").grid(row=2, column=0, sticky=W)
        self.g_text.grid(row=3, column=0, sticky=W)

        Label(self.root, text="p:", justify=LEFT, font="Elephant 15").grid(row=4, column=0, sticky=W)
        self.p_text.grid(row=5, column=0, sticky=W)

        Button(self.root, text="Сгенерировать", command=lambda: self.generate_parameters_to_send()).grid(row=6,
                                                                                                         column=0,
                                                                                                         sticky=W,
                                                                                                         pady=10)

    def generate_parameters_to_send(self) -> None:
        self.diffie_user.generate_parameters()
        self._insert_to_text(a_text=self.diffie_user.a, p_text=self.diffie_user.p, g_text=self.diffie_user.g)

    def _insert_to_text(self, **kwargs) -> None:
        for k, v in kwargs.items():
            getattr(self, k).configure(state=NORMAL)
            getattr(self, k).delete('1.0', END)
            getattr(self, k).insert('1.0', v)
            getattr(self, k).configure(state=DISABLED)

    def run_app(self) -> None:
        self.draw_widget()
        self.root.mainloop()


class Client(User):
    with open('configs/connect-config.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    HOST = data["host"]
    PORT = data["port"]
    BUFSIZ = data["bifsiz"]
    ADDR = (HOST, PORT)

    def __init__(self, title=None):
        super().__init__(title)
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.client_socket.connect(self.ADDR)

    def __draw_client_widget(self) -> None:
        Button(self.root, text="Отправить серверу", command=lambda: self.send_to_server(), height=2,
               width=30, font=5).grid(row=7, column=0, sticky=W, pady=10)

    def send_to_server(self):
        self.send(self.diffie_user.p.to_bytes((self.diffie_user.p.bit_length() + 7) // 8, 'big') or b'\0')

    def receive(self) -> None:
        while True:
            try:
                msg = self.client_socket.recv(2048)
            except OSError:
                break

    def send(self, data) -> None:
        self.client_socket.send(data)

    def run_app(self) -> None:
        self.draw_widget()
        self.__draw_client_widget()
        receive_thread = Thread(target=self.receive)
        receive_thread.start()
        self.root.mainloop()


class Server(User):
    with open('configs/connect-config.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    HOST = data["host"]
    PORT = data["port"]
    BUFSIZ = data["bifsiz"]
    ADDR = (HOST, PORT)

    def __init__(self, title=None):
        super().__init__(title)

        self.SERVER = socket(AF_INET, SOCK_STREAM)
        self.SERVER.bind(self.ADDR)
        self.ACCEPT_THREAD = None
        self.addresses = {}

    def __draw_server_widget(self) -> None:
        Button(self.root, text="Отправить клиенту", height=2, width=30, font=5).grid(row=7, column=0, sticky=W, pady=10)

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

    def handle_client(self, client) -> None:
        while True:
            msg = client.recv(self.BUFSIZ)
            print(msg)

    def run_app(self):
        self.draw_widget()
        self.__draw_server_widget()
        self.create_socket_server()
        self.root.mainloop()
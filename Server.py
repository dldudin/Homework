"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def data_received(self, data: bytes):
        decoded = data.decode()
        print(decoded)

        if self.login is None:
            # login:User
            if decoded.startswith("login:"):
                candidate_login = decoded.replace("login:", "").replace("\r\n", "")
                for client in self.server.clients:
                    if client.login == candidate_login:
                        self.transport.write(f"Логин {candidate_login} уже есть! Соединение будет разорвано.".encode())
                        self.transport.close()
                        break

                self.login = candidate_login
                self.transport.write(f"Привет, {self.login}! \n".encode())
                self.send_history()

        else:
            self.send_message(decoded)
            self.server.chat_history.append(f"{self.login}: {decoded}")


    def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        encoded = format_string.encode()

        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)

    def send_history(self):
        if len(self.server.chat_history)>10:
            self.transport.write("Показаны последние 10 сообщений чата \n".encode())
            last_ten_message = self.server.chat_history[-1:len(self.server.chat_history)-11:-1]
            for message in last_ten_message:
                self.transport.write(f"{message} \n".encode())
        else:
            self.transport.write("Показаны все сообщения чата на данный момент \n".encode())
            for message in self.server.chat_history:
                self.transport.write(f"{message} \n".encode())

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Соединение установлено")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Соединение разорвано")


class Server:
    clients: list
    chat_history: list

    def __init__(self):
        self.clients = []
        self.chat_history = []

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
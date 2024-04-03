import socket
import os
import sys
from threading import Thread

BUFFER_SIZE = 4096
CLIENT_VERSION = "2.0"  # Версия клиента

# Словарь для хранения соединений клиентов
clients = {}
# Словарь для хранения идентификаторов клиентов
client_ids = {}

def send_file(client_socket, filename):
    try:
        filesize = os.path.getsize(filename)
        client_socket.sendall(str(filesize).encode())
        client_socket.recv(1024)  # Ожидаем подтверждение от клиента
        with open(filename, 'rb') as file:
            while True:
                data = file.read(BUFFER_SIZE)
                if not data:
                    break
                client_socket.sendall(data)
        print("Файл '" + filename + "' успешно отправлен клиенту.")
    except FileNotFoundError:
        client_socket.sendall(b"File not found")

def receive_file(client_socket, filename, filesize):
    try:
        with open(filename, 'wb') as file:
            total_received = 0
            while total_received < filesize:
                data = client_socket.recv(BUFFER_SIZE)
                file.write(data)
                total_received += len(data)
                print("Принято: {}/{} байт".format(total_received, filesize)),
        print("\nФайл '" + filename + "' успешно загружен на сервер.")
    except Exception as e:
        print("Ошибка при получении файла:", str(e))

def handle_client(client_socket):
    global client_ids
    clients[client_socket] = client_socket.getpeername()[1]  # Используем порт для идентификации клиента
    client_id = len(client_ids) + 1
    client_ids[client_socket] = client_id
    try:
        while True:
            command = client_socket.recv(1024).decode()
            if not command:
                break

            if command.startswith("download"):
                filename = command.split()[1]
                send_file(client_socket, filename)
            elif command.startswith("upload"):
                filename = command.split()[1]
                filesize = int(client_socket.recv(1024).decode())
                client_socket.sendall(b"Ready to receive")  # Подтверждение готовности к приему файла
                receive_file(client_socket, filename, filesize)
            elif command.startswith("update_check"):
                client_version = command.split()[1]
                if client_version != CLIENT_VERSION:
                    client_socket.sendall(b"New version available")
                else:
                    client_socket.sendall(b"Client is up to date")
            elif command.startswith("update"):
                filename = command.split()[1]
                send_file(client_socket, filename)
            elif command == "chat_list":
                client_socket.sendall(str([client_ids[client] for client in client_ids]).encode())  # Отправка списка идентификаторов клиентов
            elif command.startswith("chat"):
                #client_socket.sendall("А кто это тут такой красивый? Как только захотите покинуть чат, напишите 'exit'.".encode())
                while True:
                    message = client_socket.recv(1024).decode()
                    if message.lower() == "exit":
                        break
                    recipient, message_content = message.split(":")
                    for client, client_id in client_ids.items():
                        if client_id == int(recipient.strip()):
                            client.sendall("Сообщение от клиента {}: {}".format(client_ids[client_socket], message_content).encode())
                            break
                print("Чат завершен для клиента", client_ids[client_socket])
            elif command == "help":
                help_text = """
                Доступные команды:
                download <filename> - скачать файл с сервера
                upload <filename> - загрузить файл на сервер
                update_check <version> - проверить наличие обновлений клиента
                update <filename> - обновить клиент до указанной версии
                chat_list - проверить список клиентов
                chat - начать чат с другим клиентом
                help - показать доступные команды
                """
                client_socket.sendall(help_text.encode())
            else:
                output = run_command(command)
                client_socket.sendall(output.encode())
    finally:
        del clients[client_socket]
        del client_ids[client_socket]
        client_socket.close()

def main():
    if len(sys.argv) != 3:
        print("Usage: python server.py <host> <port>")
        return

    host = sys.argv[1]
    port = int(sys.argv[2])

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)

    print("Ждем подключения клиента...")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            print("Подключение установлено с адресом:", client_address)
            client_handler = Thread(target=handle_client, args=(client_socket,))
            client_handler.start()
    finally:
        server_socket.close()

if __name__ == "__main__":
    main()

import socket
import os
import sys
import select
import multiprocessing

CLIENT_VERSION = "2.0"
BUFFER_SIZE = 4096

def send_file(client_socket, filename):
    try:
        filesize = os.path.getsize(filename)
        client_socket.sendall(str(filesize).encode())
        client_socket.recv(1024)  # Ожидаем подтверждение от сервера
        with open(filename, 'rb') as file:
            while True:
                data = file.read(BUFFER_SIZE)
                if not data:
                    break
                client_socket.sendall(data)
        print("Файл '" + filename + "' успешно отправлен на сервер.")
    except FileNotFoundError:
        print("Файл не найден.")

def receive_file(client_socket, filename):
    try:
        filesize = int(client_socket.recv(1024).decode())
        client_socket.sendall(b"Ready to receive")  # Подтверждение готовности к приему файла
        with open(filename, 'wb') as file:
            total_received = 0
            while total_received < filesize:
                data = client_socket.recv(BUFFER_SIZE)
                file.write(data)
                total_received += len(data)
                print("Принято: {}/{} байт".format(total_received, filesize)),
        print("\nФайл '" + filename + "' успешно получен от сервера.")
    except Exception as e:
        print("Ошибка при получении файла:", str(e))

def receive_chat_messages(client_socket):
    while True:
        server_response = client_socket.recv(1024).decode()
        if server_response.lower() == "exit":
            break
        print(server_response)

def main():
    if len(sys.argv) != 3:
        print("Usage: python client.py <host> <port>")
        return

    host = sys.argv[1]
    port = int(sys.argv[2])

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    # Проверка наличия обновлений
    client_socket.sendall(("update_check " + CLIENT_VERSION).encode())
    response = client_socket.recv(1024).decode()
    if response == "New version available":
        print("Доступна новая версия клиента.")
        choice = input("Хотите обновить клиент? (yes/no): ")
        if choice.lower() == "yes":
            client_socket.sendall("update client_new.py".encode())
            receive_file(client_socket, "client_new.py")
            os.replace("client_new.py", "client.py")  # Заменяем текущий файл клиента новой версией
            print("Клиент успешно обновлен.")
            # Добавляем код для повторного соединения с сервером после обновления клиента
            os.execl(sys.executable, sys.executable, *sys.argv)
            return

    print("Текущая версия клиента:", CLIENT_VERSION)

    try:
        while True:
            command = input("Введите команду: ")
            if not command:
                break

            client_socket.sendall(command.encode())
            if command.startswith("download"):
                filename = command.split()[1]
                receive_file(client_socket, filename)
            elif command.startswith("upload"):
                filename = command.split()[1]
                send_file(client_socket, filename)
            elif command == "chat_list":
                print("Получение списка клиентов: ")
                clients_list = client_socket.recv(4096).decode()
                print(clients_list)
            elif command.startswith("chat"):
                print("Вы вошли в чат. Чтобы отправить сообщение, напишите id клиента: сообщение. 'exit', чтобы выйти из чата.")
                receive_process = multiprocessing.Process(target=receive_chat_messages, args=(client_socket,))
                receive_process.start()
                while True:
                    ready, _, _ = select.select([sys.stdin], [], [], 0.1)
                    if sys.stdin in ready:
                        message = input()
                        client_socket.sendall(message.encode())
                        if message.lower() == "exit":
                            #receive_process.join()
                            break
            else:
                output = client_socket.recv(1024).decode()
                print(output)
    finally:
        client_socket.close()

if __name__ == "__main__":
    main()

import os
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from multiprocessing import Process
from datetime import datetime
import pymongo
from socketserver import ThreadingMixIn

# Налаштування для підключення до MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["messages_db"]
messages_collection = db["messages"]

# HTTP-сервер для обробки запитів
class MyHTTPRequestHandler(BaseHTTPRequestHandler):
    def _serve_file(self, file_path, content_type):
        if os.path.exists(file_path):
            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.end_headers()
            with open(file_path, 'rb') as file:
                self.wfile.write(file.read())
        else:
            if file_path != "error.html":
                self._serve_file("error.html", "text/html")
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"404 Not Found")


    def do_GET(self):
        parsed_path = urlparse(self.path).path
        if parsed_path == '/':
            self._serve_file('index.html', 'text/html')
        elif parsed_path == '/message.html':
            self._serve_file('message.html', 'text/html')
        elif parsed_path == '/style.css':
            self._serve_file('style.css', 'text/css')
        elif parsed_path == '/logo.png':
            self._serve_file('logo.png', 'image/png')
        else:
            self._serve_file('error.html', 'text/html')

    def do_POST(self):
        if self.path == '/message':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = parse_qs(post_data.decode('utf-8'))

            username = data.get('username', [''])[0]
            message = data.get('message', [''])[0]
            if username and message:
                send_message_to_socket_server(username, message)

            self.send_response(302)
            self.send_header('Location', '/')
            self.end_headers()

def run_http_server():
    server_address = ('', 3000)
    httpd = HTTPServer(server_address, MyHTTPRequestHandler)
    print("HTTP сервер працює на порту 3000")
    httpd.serve_forever()

# Socket-сервер для збереження повідомлень у MongoDB
def run_socket_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('localhost', 5000))
    print("Socket сервер працює на порту 5000")
    
    while True:
        data, _ = sock.recvfrom(1024)
        message_data = data.decode('utf-8').split(';')
        username, message = message_data[0], message_data[1]
        messages_collection.insert_one({
            "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "username": username,
            "message": message
        })

# Функція для надсилання повідомлення на Socket-сервер
def send_message_to_socket_server(username, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(f"{username};{message}".encode('utf-8'), ('localhost', 5000))

# Запуск HTTP і Socket серверів у різних процесах
if __name__ == "__main__":
    http_process = Process(target=run_http_server)
    socket_process = Process(target=run_socket_server)
    
    http_process.start()
    socket_process.start()

    http_process.join()
    socket_process.join()

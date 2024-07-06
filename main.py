import os
import socket
import threading
import json
from http.server import SimpleHTTPRequestHandler, HTTPServer
from socketserver import ThreadingUDPServer, BaseRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime


HOST = '127.0.0.1'
HTTP_PORT = 3000
SOCKET_PORT = 5000

class MyHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = '/templates/index.html'
        elif self.path == '/message':
            self.path = '/templates/message.html'
        elif self.path.startswith('/static'):
            self.path = self.path
        else:
            self.path = '/templates/error.html'
        return super().do_GET()

    def do_POST(self):
        if self.path == '/message':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            fields = parse_qs(post_data.decode('utf-8'))
            username = fields.get('username', [''])[0]
            message = fields.get('message', [''])[0]
            data = {'username': username, 'message': message}
            send_to_socket_server(data)
            self.send_response(303)
            self.send_header('Location', '/')
            self.end_headers()
        else:
            self.send_error(404)
            self.end_headers()

def send_to_socket_server(data):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(json.dumps(data).encode(), (HOST, SOCKET_PORT))

class MyUDPHandler(BaseRequestHandler):
    def handle(self):
        data = self.request[0].strip()
        data_dict = json.loads(data.decode('utf-8'))
        timestamp = datetime.now().isoformat()

        if not os.path.exists('storage'):
            os.makedirs('storage')

        if os.path.exists('storage/data.json'):
            with open('storage/data.json', 'r') as f:
                storage_data = json.load(f)
        else:
            storage_data = {}

        storage_data[timestamp] = data_dict

        with open('storage/data.json', 'w') as f:
            json.dump(storage_data, f, indent=4)

def run_http_server():
    server_address = (HOST, HTTP_PORT)
    httpd = HTTPServer(server_address, MyHandler)
    print(f"HTTP сервер запущен на порту {HTTP_PORT}")
    httpd.serve_forever()

def run_socket_server():
    server_address = (HOST, SOCKET_PORT)
    with ThreadingUDPServer(server_address, MyUDPHandler) as server:
        print(f"Сокет-сервер запущен на порту {SOCKET_PORT}")
        server.serve_forever()

if __name__ == '__main__':
    # Запуск сокет-сервера в отдельном потоке
    socket_thread = threading.Thread(target=run_socket_server, daemon=True)
    socket_thread.start()

    # Запуск HTTP-сервера
    run_http_server()

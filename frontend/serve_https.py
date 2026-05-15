import http.server
import ssl
import os

os.chdir(os.path.dirname(__file__))

server_address = ('0.0.0.0', 8080)
httpd = http.server.HTTPServer(server_address, http.server.SimpleHTTPRequestHandler)

certfile = "localhost+2.pem"
keyfile = "localhost+2-key.pem"

# SSL-контекст, не знаю че это такое но спасибо
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile, keyfile)

# Применяем контекст к сокету, интернет спасибо
httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

print("HTTPS server running on https://0.0.0.0:8080")
httpd.serve_forever()
import http.server
import os


class SimpleHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        file_name = self.path.strip("/") + ".txt"

        if os.path.exists(file_name):
            self.send_response(200)

            self.send_header("Content-type", "text/html")
            self.end_headers()

            with open(file_name, "r") as file:
                file_content = file.read()

            self.wfile.write(file_content.encode("utf-8"))

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write("404 Not Found".encode())


os.chdir(os.path.dirname(os.path.abspath(__file__)))

server_address = ("", 4000)

httpd = http.server.HTTPServer(server_address, SimpleHTTPRequestHandler)

print("Starting server...")
httpd.serve_forever()

import functools, http.server, socketserver, os
ROOT = "/Users/simongeils/Desktop/KeyCompass"
os.chdir(ROOT)
H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("127.0.0.1", 4321), H) as s:
    print("serving", ROOT, "on 4321", flush=True)
    s.serve_forever()

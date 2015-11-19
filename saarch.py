from BaseHTTPServer import BaseHTTPRequestHandler
import urlparse
import lib_saarch

class GetHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        parsed_path = urlparse.urlparse(self.path)
	query = parsed_path.query[2:]
	resp, cleaned = lib_saarch.search(query,index)
	#beginHTML = "<!DOCTYPE html> <html lang=\"en\"> <head> Results </head> <body>"
	#endHTML = " </body></html>"
        self.wfile.write("Those are the results of your query: " + query.replace("+", " ") + ", but those words were not included in the research because were not present in our database: " + "".join(cleaned) + "\n\n" + resp)
        return

if __name__ == '__main__':
    import sys
    reload(sys)
    sys.setdefaultencoding("utf-8")
    from BaseHTTPServer import HTTPServer
    index = lib_saarch.retIndex()
    server = HTTPServer(("0.0.0.0", 8080), GetHandler)
    print 'Starting server, use <Ctrl-C> to stop'
    server.serve_forever()

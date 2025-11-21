import webview

def open(link, name=""):
    webview.create_window(name, link, fullscreen=False)
    webview.start()

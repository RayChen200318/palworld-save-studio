import sys
import threading
import time
import requests
import traceback
import webbrowser
import webview
from palworld_save_studio.config import version_info, Config
from palworld_save_studio.utils import LOGGER
from palworld_save_studio.webui import main as web_main


def main():
    t = threading.Thread(target=web_main)
    t.daemon = True
    t.start()

    while True:
        LOGGER.info("Waiting for backend response...")
        try:
            response = requests.get(f"http://127.0.0.1:{Config.port}/api/ready")
            if response.status_code == 200:
                LOGGER.info("Backend ready, launching GUI...")
                break
            time.sleep(0.5)
        except requests.exceptions.ConnectionError:
            time.sleep(0.5)

    try:
        webview.create_window(
            f"Palworld Save Studio · {version_info()}",
            url=f"http://127.0.0.1:{Config.port}/",
            width=1600,
            height=1000,
            min_size=(1280, 720),
        )
        webview.start()
    except KeyboardInterrupt:
        pass
    except:
        LOGGER.warning(f"Failed Launching pywebview: {traceback.format_exc()}")
        LOGGER.info(f"Fallback to web browser, opening http://127.0.0.1:{Config.port} ...")
        threading.Timer(1, lambda: webbrowser.open(f"http://127.0.0.1:{Config.port}") ).start()
        t.join()
    sys.exit()

if __name__ == "__main__":
    main()

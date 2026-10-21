#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在电脑上起一个本地服务，让同一 WiFi 下的手机能打开。

双击「启动.bat」即可，不用装任何东西。
"""

import http.server
import os
import socket
import socketserver
import sys
import threading
import webbrowser

PORT = 8000
ROOT = os.path.dirname(os.path.abspath(__file__))


def lan_ip():
    """拿到本机在局域网里的地址（不是 127.0.0.1）。"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def end_headers(self):
        # 改了文件刷新就能看到，不用清缓存
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt, *args):
        pass  # 不刷屏


def main():
    ip = lan_ip()
    line = "=" * 52
    print(line)
    print("  初三数学 · 盲点诊断    已在电脑上启动")
    print(line)
    print()
    print("  1. 让手机连上和这台电脑同一个 WiFi")
    print("  2. 在手机浏览器地址栏输入：")
    print()
    print("         http://%s:%d" % (ip, PORT))
    print()
    print("  3. 打开后点「分享 → 添加到主屏幕」，")
    print("     以后点桌面图标就能用，不用再输网址。")
    print()
    print("  电脑上也会自动打开一份：http://127.0.0.1:%d" % PORT)
    print()
    print("  这个窗口关掉，服务就停了。")
    print(line)

    threading.Timer(1.0, lambda: webbrowser.open("http://127.0.0.1:%d/" % PORT)).start()

    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.ThreadingTCPServer(("0.0.0.0", PORT), Handler) as httpd:
            httpd.serve_forever()
    except OSError as e:
        print()
        print("启动失败：%s" % e)
        print("可能是 %d 端口被别的程序占了，关掉那个程序再试。" % PORT)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n已停止。")


if __name__ == "__main__":
    main()

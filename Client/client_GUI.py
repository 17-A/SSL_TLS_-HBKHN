# Giao diện chat

import tkinter as tk
from tkinter import scrolledtext
import threading
import client_CORE  # file này để xử lý socket

class ChatClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat by SSL/TLS secure (Tkinter GUI)")
        self.root.geometry("400x500")

        # Khung hiển thị tin nhắn
        self.chat_display = scrolledtext.ScrolledText(root, wrap=tk.WORD, state='disabled')
        self.chat_display.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Ô nhập tin nhắn
        self.msg_entry = tk.Entry(root)
        self.msg_entry.pack(padx=10, pady=(0,10), fill=tk.X)
        self.msg_entry.bind("<Return>", self.send_message)

        # Nút gửi
        self.send_button = tk.Button(root, text="Gửi", command=self.send_message)
        self.send_button.pack(padx=10, pady=(0,10))

        # Khởi động client socket ở luồng riêng
        self.client = client_CORE.SSLClient(self.display_message)
        threading.Thread(target=self.client.connect, daemon=True).start()

    def send_message(self, event=None):
        message = self.msg_entry.get()
        if message:
            self.client.send(message)
            self.msg_entry.delete(0, tk.END)

    def display_message(self, message):
        self.chat_display.configure(state='normal')
        self.chat_display.insert(tk.END, message + "\n")
        self.chat_display.configure(state='disabled')
        self.chat_display.see(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatClientApp(root)
    root.mainloop()

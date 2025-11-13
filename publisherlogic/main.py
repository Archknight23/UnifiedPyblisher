import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QPushButton, QVBoxLayout, QWidget, QLabel
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, pyqtSignal
from atproto import Client as BskyCLient
import tweepy
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

class MainWin(QMainWindow):
    message_changed = pyqtSignal(str) #Stuff changes, this goes off

    def  __init__(self):
        super().__init__()
        self.setWindowTitle("Chaos Foundry Comms Publisher")
        self.setGeometry(100, 100, 600, 400)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.text_edit = QTextEdit() # Textbox
        self.text_edit.textChanged.connect(self.on_text_changed)
        layout.addWidget(self.text_edit)
        #Character Limit Logic
        self.char_label = QLabel("Characters: 0 || Limits: X: 250 (included with bluescheck) || Bsky: 150, XHS: 1000 Mandarin Characters")
        layout.addWidget(self.char_label)

    #Login Button 
        login_button = QPushButton("Access Platform")
        login_button.clicked.connect(self.open_login_windows)
        layout.addWidget(login_button)

    #Post Button
        post_button = QPushButton("Post to selected Platforms")
        post_button.clicked.connect(self.post_all)
        layout.addWidget(post_button)

    #Hyprland
        self.bsky_windows = None
        self.x_windows = None
        self.xhs_windows = None
    
    def on_text_changed(self):
        message = self.text_edit.toPlainText()
        count = len(message)
        self.char_label.setText(f"Characters: {count} / || limits: X: 250, Bsky: 300, XHS: 1000")
        if count > 280:
            self.char_label.setStyleSheet("color: red;")
        else:
            self.char_label.setStyleSheet("")
        self.message_changed.emit(message) #Shows the message to other windows
    
    def open_login_windows(self):
        #WINDOW SPAWNING LET"S GOOOOO
        self.bsky_window = BrowserWindow("Bsky", "https://bsky.app/login", self.message_changed)
        self.
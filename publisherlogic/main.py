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

        self.char_label = QLabel("Characters: 0 || Limits: X: 250 (included with bluescheck) || Bsky: 150, XHS: 1000 Mandarin Characters")
        layout.addWidget(self)
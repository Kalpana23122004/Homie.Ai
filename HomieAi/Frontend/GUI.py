from PyQt5.QtWidgets import (QApplication, QMainWindow, QTextEdit, QStackedWidget, 
                            QWidget, QLineEdit, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QFrame, QLabel, QSizePolicy)
from PyQt5.QtGui import (QIcon, QPixmap, QMovie, QColor, QTextCharFormat, 
                        QFont, QTextBlockFormat, QPainter)  # <- Add QPainter here
from PyQt5.QtCore import Qt, QSize, QTimer

from dotenv import dotenv_values
import sys
import os
import pygame._sdl2.audio  # For better audio control in v2.6.0+
from pygame import mixer
from dotenv import load_dotenv

load_dotenv()

AssistantName = os.getenv('AssistantName','Assistant')
current_dir = os.getcwd()

old_chat_message = ""
TempDirPath = os.path.join(current_dir, "Frontend", "Files")
GraphicsDirPath = os.path.join(current_dir, "Frontend", "Graphics")

def AnswerModifier(Answer):
    lines = Answer.split('\n')
    new_query_lines = [line for line in lines if line.strip()]
    modified_answer = '\n'.join(new_query_lines)
    return modified_answer

def QueryModifier(Query):
    new_query = Query.lower().strip()
    query_words = new_query.split()
    question_words = ['how', 'what', 'who', 'where', 'when', 'why', 
                     'which', 'whose', 'whom', 'can you', "what's", 
                     "where's", "how's"]

    if any(word in new_query for word in question_words):
        if query_words[-1][-1] in ['?', '.', ',']:
            new_query = new_query[:-1] + '?'
        else:
            new_query += '?'
    else:
        if query_words[-1][-1] in ['?', '.', ',']:
            new_query = new_query[:-1] + '.'
        else:
            new_query += '.'
    return new_query.capitalize()

def SetMicrophoneStatus(Status):
    with open(os.path.join(TempDirPath, "Mic_data"), 'w', encoding='utf-8') as file:
        file.write(Status)

def GetMicrophoneStatus():
    with open(os.path.join(TempDirPath, "Mic_data"), 'r', encoding='utf-8') as file:
        Status = file.read()
    return Status

def SetAssistantStatus(Status):
    with open(os.path.join(TempDirPath, "Status.data"), 'w', encoding='utf-8') as file:
        file.write(Status)

def GetAssistantStatus():
    with open(os.path.join(TempDirPath, "Status.data"), 'r', encoding='utf-8') as file:
        Status = file.read()
    return Status

def MLcButtonInitialed():
    SetMicrophoneStatus("False")

def MLcButtonClosed():
    SetMicrophoneStatus("True")

def GraphicsDirectoryPath(filename):
    return os.path.join(GraphicsDirPath, filename)

def TempDirectoryPath(filename):
    return os.path.join(TempDirPath, filename)

def ShowTextToScreen(Text):
    with open(os.path.join(TempDirPath, "Responses.data"), 'w', encoding='utf-8') as file:
        file.write(Text)

class ChatSection(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(-10, 40, 40, 100)
        layout.setSpacing(-100)
        
        self.chat_text_edit = QTextEdit()
        self.chat_text_edit.setReadOnly(True)
        self.chat_text_edit.setTextInteractionFlags(Qt.NoTextInteraction)
        self.chat_text_edit.setFrameShape(QFrame.NoFrame)
        layout.addWidget(self.chat_text_edit)
        
        self.setStyleSheet("""
            QScrollBar:vertical {
                border: none;
                background: black;
                width: 10px;
                margin: 8px 8px 8px 8px;
            }
            QScrollBar::handle:vertical {
                background: white;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical {
                background: black;
                subcontrol-position: bottom;
                subcontrol-origin: margin;
                height: 10px;
            }
            QScrollBar::sub-line:vertical {
                background: black;
                subcontrol-position: top;
                subcontrol-origin: margin;
                height: 10px;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                border: none;
                background: none;
                color: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        text_color = QColor('cyan')
        text_color_text = QTextCharFormat()
        text_color_text.setForeground(text_color)
        self.chat_text_edit.setCurrentCharFormat(text_color_text)
        
        self.gif_label = QLabel()
        self.gif_label.setStyleSheet("border: none;")
        movie = QMovie(GraphicsDirectoryPath('Jarvis.gif'))
        max_gif_size_W = 480
        max_gif_size_H = 270
        movie.setScaledSize(QSize(max_gif_size_W, max_gif_size_H))
        self.gif_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.gif_label.setMovie(movie)
        movie.start()
        layout.addWidget(self.gif_label)
        
        self.label = QLabel("")
        self.label.setStyleSheet("""
            color: white; 
            font-size:16px; 
            margin-right: 195px; 
            border: none; 
            margin-top: -36px;
        """)
        self.label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.label)
        
        font = QFont()
        font.setPointSize(13)
        self.chat_text_edit.setFont(font)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.loadMessages)
        self.timer.timeout.connect(self.SpeechRecogText)
        self.timer.start(5)
        self.stop_button = QPushButton("Stop Speaking")
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #ff4444;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
            }
        """)
        self.stop_button.clicked.connect(self.stop_speech)
        layout.addWidget(self.stop_button)

    def stop_speech(self):
        pygame.mixer.music.stop()
        
    def loadMessages(self):
        global old_chat_message
        with open(TempDirectoryPath("Responses.data"), 'r', encoding='utf-8') as file:
            messages = file.read()
        if not messages:
            pass
        elif len(messages) <= 1:
            pass
        elif str(old_chat_message) == str(messages):
            pass
        else:
            self.addMessage(messages, color='white')
            old_chat_message = messages
    
    def SpeechRecogText(self):
        with open(TempDirectoryPath("Status.data"), 'r', encoding='utf-8') as file:
            messages = file.read()
        self.label.setText(messages)
    
    def addMessage(self, message, color='white'):
        # Replace chat_text_append with the correct QTextEdit method
        self.chat_text_edit.append(message)
        
class InitialScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Debug output
        print("Initializing home screen...")
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. Add status label at top
        self.status_label = QLabel("Initializing...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            color: white; 
            font-size: 16px;
            padding: 10px;
        """)
        layout.addWidget(self.status_label)
        
        # 2. Add animated GIF
        self.gif_label = QLabel()
        gif_path = GraphicsDirectoryPath("Jarvis.gif")
        if os.path.exists(gif_path):
            self.movie = QMovie(gif_path)
            if self.movie.isValid():
                self.movie.setScaledSize(QSize(400, 225))  # Adjust size as needed
                self.gif_label.setMovie(self.movie)
                self.movie.start()
            else:
                print(f"Invalid GIF file: {gif_path}")
        else:
            print(f"GIF not found: {gif_path}")
        
        self.gif_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.gif_label)
        
        # 3. Add microphone button
        self.mic_button = QPushButton()
        self.update_mic_icon()  # Set initial icon
        
        # Style the button
        self.mic_button.setFixedSize(80, 80)
        self.mic_button.setStyleSheet("""
            QPushButton {
                border: 2px solid white;
                border-radius: 40px;
                background-color: rgba(0,0,0,0);
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,0.1);
            }
        """)
        
        # Connect click event
        self.mic_button.clicked.connect(self.toggle_microphone)
        
        # Add to layout with centering
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.addWidget(self.mic_button)
        button_layout.setAlignment(Qt.AlignCenter)
        layout.addWidget(button_container)
        
        # Set background
        self.setStyleSheet("background-color: black;")
        
        # Start status update timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_status)
        self.timer.start(100)  # Update every 100ms
    
    def update_mic_icon(self):
        """Update microphone icon based on state"""
        state = GetMicrophoneStatus()
        icon_path = GraphicsDirectoryPath("MLc_on.png" if state == "True" else "MLc_off.png")
        if os.path.exists(icon_path):
            self.mic_button.setIcon(QIcon(icon_path))
            self.mic_button.setIconSize(QSize(60, 60))
    
    def toggle_microphone(self):
        """Toggle microphone state"""
        current = GetMicrophoneStatus()
        new_state = "False" if current == "True" else "True"
        SetMicrophoneStatus(new_state)
        self.update_mic_icon()
    
    def update_status(self):
        """Update status from status file"""
        status = GetAssistantStatus()
        self.status_label.setText(status)
# Check if files exist before using them
print("Checking graphics files:")
print("Jarvis.gif exists:", os.path.exists(GraphicsDirectoryPath('Jarvis.gif')))
print("MLc_on.png exists:", os.path.exists(GraphicsDirectoryPath('MLc_on.png')))
print("MLc_off.png exists:", os.path.exists(GraphicsDirectoryPath('MLc_off.png')))


class MessageScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()
        
        layout = QVBoxLayout()
        label = QLabel()
        layout.addWidget(label)
        
        chat_section = ChatSection()
        layout.addWidget(chat_section)
        
        self.setLayout(layout)
        self.setStyleSheet('background-color: black;')
        self.setFixedHeight(screen_height)
        self.setFixedWidth(screen_width)

class CustomTopBar(QWidget):
    def __init__(self, parent, stacked_widget):
        super().__init__(parent)
        self.initUI()
        self.current_screen = None
        self.stacked_widget = stacked_widget
    
    def initUI(self):
        self.setFixedHeight(55)
        layout = QHBoxLayout(self)
        layout.setAlignment(Qt.AlignRight)
        
        title_label = QLabel(f" {AssistantName.capitalize()} AI ")
        title_label.setStyleSheet("""
            color: black; 
            font-size: 18px; 
            background-color: white
        """)
        
        home_button = QPushButton()
        home_icon = QIcon(GraphicsDirectoryPath("Home.png"))
        home_button.setIcon(home_icon)
        home_button.setText(" Home")
        home_button.setStyleSheet("""
            height: 40px; 
            line-height: 40px; 
            background-color: white; 
            color: black
        """)
        
        message_button = QPushButton()
        message_icon = QIcon(GraphicsDirectoryPath("Chats.png"))
        message_button.setIcon(message_icon)
        message_button.setText(" Chat")
        message_button.setStyleSheet("""
            height: 40px; 
            line-height: 40px; 
            background-color: white; 
            color: black
        """)
        
        minimize_button = QPushButton()
        minimize_icon = QIcon(GraphicsDirectoryPath("Minimize2.png"))
        minimize_button.setIcon(minimize_icon)
        minimize_button.setStyleSheet("background-color: white")
        minimize_button.clicked.connect(self.minimizeWindow)
        
        self.maximize_button = QPushButton()
        self.maximize_icon = QIcon(GraphicsDirectoryPath("Maximize.png"))
        self.restore_icon = QIcon(GraphicsDirectoryPath("Minimize.png"))
        self.maximize_button.setIcon(self.maximize_icon)
        self.maximize_button.setFlat(True)
        self.maximize_button.setStyleSheet("background-color: white")
        self.maximize_button.clicked.connect(self.maximizeWindow)
        
        close_button = QPushButton()
        close_icon = QIcon(GraphicsDirectoryPath("Close.png"))
        close_button.setIcon(close_icon)
        close_button.setStyleSheet("background-color: white")
        close_button.clicked.connect(self.closeWindow)
        
        line_frame = QFrame()
        line_frame.setFixedHeight(1)
        line_frame.setFrameShape(QFrame.HLine)
        line_frame.setFrameShadow(QFrame.Sunken)
        line_frame.setStyleSheet("border-color: black;")
        
        layout.addWidget(title_label)
        layout.addStretch(1)
        layout.addWidget(home_button)
        layout.addWidget(message_button)
        layout.addStretch(1)
        layout.addWidget(minimize_button)
        layout.addWidget(self.maximize_button)
        layout.addWidget(close_button)
        layout.addWidget(line_frame)
        
        self.draggable = True
        self.offset = None
        
        home_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        message_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.white)
        super().paintEvent(event)
    
    def minimizeWindow(self):
        self.parent().showMinimized()
    
    def maximizeWindow(self):
        if self.parent().isMaximized():
            self.parent().showNormal()
            self.maximize_button.setIcon(self.maximize_icon)
        else:
            self.parent().showMaximized()
            self.maximize_button.setIcon(self.restore_icon)
    
    def closeWindow(self):
        self.parent().close()
    
    def mousePressEvent(self, event):
        if self.draggable:
            self.offset = event.pos()
    
    def mouseMoveEvent(self, event):
        if self.draggable and self.offset:
            new_pos = event.globalPos() - self.offset
            self.parent().move(new_pos)
    
    def showMessageScreen(self):
        if self.current_screen is not None:
            self.current_screen.hide()
        
        message_screen = MessageScreen(self)
        layout = self.parent().layout()
        if layout is not None:
            layout.addWidget(message_screen)
            self.current_screen = message_screen

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.initUI()
    
    def initUI(self):
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()
        
        stacked_widget = QStackedWidget(self)
        initial_screen = InitialScreen()
        message_screen = MessageScreen()
        
        stacked_widget.addWidget(initial_screen)
        stacked_widget.addWidget(message_screen)
        
        self.setGeometry(0, 0, screen_width, screen_height)
        self.setStyleSheet("background-color: black;")
        
        top_bar = CustomTopBar(self, stacked_widget)
        self.setMenuWidget(top_bar)
        self.setCentralWidget(stacked_widget)

def GraphicalUserInterface():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    GraphicalUserInterface()
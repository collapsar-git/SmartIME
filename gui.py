import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QTextEdit, QLineEdit, QLabel, QFrame, QPushButton)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QFont

# 引入后端
from main import HMM_Model

# 尝试引入语音模块
try:
    from voice import VoiceRecognizer
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False
    print("提示: 未检测到 voice.py 或 SpeechRecognition 库，语音功能已禁用。")

# 语音工作线程
class VoiceThread(QThread):
    text_received = pyqtSignal(str)
    status_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self._is_running = False

    def run(self):
        if not VOICE_AVAILABLE:
            self.status_changed.emit("模块缺失")
            return
        
        self._is_running = True
        recognizer = VoiceRecognizer()
        
        while self._is_running:
            try:
                success, text = recognizer.listen_and_convert()
            except Exception:
                success, text = False, ""

            if not self._is_running: break 
            
            if success:
                self.text_received.emit(text)
            elif "超时" not in text and "无法识别" not in text:
                # 忽略正常的静音超时，只报严重错误
                self.status_changed.emit(f"状态: {text}")

    def stop(self):
        """ 设置停止标记，但不再阻塞等待 """
        self._is_running = False
        # 线程会在当前的 listen 结束后自动自然死亡

# 候选词标签
class ClickableLabel(QLabel):
    clicked = pyqtSignal(int)
    hovered = pyqtSignal(int)

    def __init__(self, index, parent=None):
        super().__init__(parent)
        self.index = index
        self.setFont(QFont("Segoe UI Emoji", 14)) 
        self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QLabel { color: #0044CC; padding: 4px; border-radius: 4px; }
            QLabel:hover { background-color: #E6F3FF; }
        """)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.index)

    def enterEvent(self, event):
        self.hovered.emit(self.index)

# 主窗口
class InputMethodWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.candidates = []   
        self.page_index = 0    
        self.PAGE_SIZE = 5
        self.is_voice_active = False 
        self.voice_thread = None     
        
        self.init_model() 
        self.init_ui()    
        
    def init_ui(self):
        self.setWindowTitle("Python HMM 输入法 (丝滑语音版)")
        self.resize(850, 600)
        
        layout = QVBoxLayout()
        
        # 状态栏
        self.status_label = QLabel("正在初始化...")
        self.update_status_text()
        layout.addWidget(self.status_label)
        
        # 文本编辑器
        self.text_editor = QTextEdit()
        self.text_editor.setFont(QFont("微软雅黑", 14))
        layout.addWidget(self.text_editor)
        
        # 输入区域
        input_layout = QHBoxLayout()
        
        self.pinyin_input = QLineEdit()
        self.pinyin_input.setFont(QFont("Arial", 12))
        self.pinyin_input.setPlaceholderText("输入拼音... (按 → 翻页)")
        self.pinyin_input.textChanged.connect(self.on_text_changed)
        self.pinyin_input.keyPressEvent = self.line_edit_key_press
        input_layout.addWidget(self.pinyin_input)
        
        # 语音按钮
        self.voice_btn = QPushButton("🎤 开始识别")
        self.voice_btn.setFont(QFont("微软雅黑", 10))
        self.voice_btn.setFixedWidth(120)
        self.voice_btn.setCursor(Qt.PointingHandCursor)
        self.voice_btn.clicked.connect(self.toggle_voice_input)
        
        if not VOICE_AVAILABLE:
            self.voice_btn.setEnabled(False)
            self.voice_btn.setText("语音不可用")
            self.voice_btn.setStyleSheet("color: gray;")
            
        input_layout.addWidget(self.voice_btn)
        
        layout.addLayout(input_layout)
        
        # 候选词区域
        candidate_frame = QFrame()
        candidate_frame.setStyleSheet("background-color: #FAFAFA; border-top: 1px solid #DDD; border-bottom: 1px solid #DDD;")
        h_layout = QHBoxLayout(candidate_frame)
        h_layout.setContentsMargins(5, 5, 5, 5)
        
        self.candidate_labels = []
        for i in range(5):
            lbl = ClickableLabel(i)
            lbl.clicked.connect(self.select_candidate_by_ui_index)
            lbl.hovered.connect(self.show_definition_by_ui_index)
            h_layout.addWidget(lbl)
            self.candidate_labels.append(lbl)
        
        self.page_label = QLabel("")
        self.page_label.setStyleSheet("color: #999; font-size: 10px; margin-left: 10px;")
        self.page_label.setFixedWidth(50)
        self.page_label.setAlignment(Qt.AlignCenter)
        h_layout.addWidget(self.page_label)

        layout.addWidget(candidate_frame)
        
        # 词义百科
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True) 
        self.info_text.setFixedHeight(140) 
        self.info_text.setPlaceholderText("词义百科 (鼠标悬停候选词查看)")
        
        self.info_text.setStyleSheet("""
            QTextEdit {
                background-color: #FFFFE0; 
                padding: 8px; 
                color: #333;
                border: 1px solid #CCC;
                font-family: '楷体';
                font-size: 14px;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.info_text)
        
        self.setLayout(layout)

    def init_model(self):
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # 所有语料统一放在本目录的data文件夹中
            data_dir = os.path.join(current_dir, "data")
            hmm_dir = data_dir
            # 如果当前目录没有data文件夹，尝试上级目录的data（兼容不同运行路径）
            if not os.path.isdir(data_dir):
                parent_dir = os.path.dirname(current_dir)
                alt_data = os.path.join(parent_dir, "data")
                if os.path.isdir(alt_data):
                    data_dir = alt_data
                    hmm_dir = data_dir
                
            self.model = HMM_Model()
            
            pinyin_path = os.path.join(hmm_dir, "pinyin.txt")
            if not os.path.exists(pinyin_path): pinyin_path = "pinyin.txt"
            
            self.model.load_data(
                pinyin_path,
                os.path.join(hmm_dir, "CharFreq.txt"),
                os.path.join(hmm_dir, "Bigram.txt")
            )
            
            if hasattr(self.model, 'kb'):
                self.model.kb.load_data(data_dir)
                
        except Exception as e:
            print(f"Init Error: {e}")

    def update_status_text(self):
        if hasattr(self, 'model') and hasattr(self.model, 'kb'):
            c = len(self.model.kb.emoji_dict)
            voice_status = "✅" if VOICE_AVAILABLE else "❌"
            self.status_label.setText(f"系统就绪 | Emoji: {c} | 语音: {voice_status}")
            self.status_label.setStyleSheet("color: green")

    # 无阻塞的切换逻辑
    def toggle_voice_input(self):
        if not self.is_voice_active:
            self.start_voice()
        else:
            self.stop_voice()

    def start_voice(self):
        self.is_voice_active = True
        self.voice_btn.setText("⏸️ 停止识别")
        self.voice_btn.setStyleSheet("background-color: #FFEEEE; color: red; border: 1px solid red;")
        self.status_label.setText("🎙️ 语音监听中...")
        
        self.voice_thread = VoiceThread()
        self.voice_thread.text_received.connect(self.on_voice_text)
        self.voice_thread.status_changed.connect(self.on_voice_status)
        self.voice_thread.start()
        
        self.pinyin_input.setFocus()

    def stop_voice(self):
        """ 立即停止，不等待线程 """
        self.is_voice_active = False
        
        # 界面立刻复原 (给用户“秒停”的感觉)
        self.voice_btn.setText("🎤 开始识别")
        self.voice_btn.setStyleSheet("")
        self.status_label.setText("语音已暂停")
        
        if self.voice_thread:
            # 设置线程停止标记
            self.voice_thread.stop()
            
            # 断开所有信号连接！
            # 这样即使线程还在后台跑完最后几秒，它的结果也传不回界面
            try:
                self.voice_thread.text_received.disconnect()
                self.voice_thread.status_changed.disconnect()
            except:
                pass
            
            # 丢弃引用，让它自生自灭
            self.voice_thread = None

    def on_voice_text(self, text):
        self.text_editor.insertPlainText(text)
        self.status_label.setText("识别成功，继续监听...")

    def on_voice_status(self, msg):
        self.status_label.setText(f"🎙️ {msg}")

    def line_edit_key_press(self, event):
        key = event.key()
        text = event.text()
        
        if key == Qt.Key_Right or text == '=':
            self.next_page()
            return
        if key == Qt.Key_Left or text == '-':
            self.prev_page()
            return
        if text in ['1', '2', '3', '4', '5']:
            idx = int(text) - 1
            self.select_candidate_by_ui_index(idx)
            return 
        if key == Qt.Key_Return:
            if event.modifiers() & Qt.ControlModifier: 
                self.text_editor.insertPlainText(self.pinyin_input.text())
                self.pinyin_input.clear()
            elif self.candidates:
                self.select_candidate_by_ui_index(0)
            return
        QLineEdit.keyPressEvent(self.pinyin_input, event)

    def next_page(self):
        max_page = (len(self.candidates) - 1) // self.PAGE_SIZE
        if self.page_index < max_page:
            self.page_index += 1
            self.update_ui()

    def prev_page(self):
        if self.page_index > 0:
            self.page_index -= 1
            self.update_ui()

    def on_text_changed(self, text):
        text = text.strip()
        self.candidates = []
        self.page_index = 0 
        
        if not text:
            self.clear_ui()
            return
        
        idiom = self.model.kb.get_idiom(text.replace(" ", ""))
        if idiom: self.candidates.append(idiom)
        
        emoji = self.model.kb.get_emoji(text.replace(" ", ""))
        if emoji and emoji not in self.candidates:
            self.candidates.append(emoji)
            
        if not idiom:
            res = self.model.get_top_candidates(text, top_k=50) 
            for w in res:
                if w not in self.candidates:
                    self.candidates.append(w)
        
        self.update_ui()

    def select_candidate_by_ui_index(self, ui_idx):
        real_idx = self.page_index * self.PAGE_SIZE + ui_idx
        if real_idx < len(self.candidates):
            word = self.candidates[real_idx]
            self.text_editor.insertPlainText(word)
            self.pinyin_input.clear()
            self.candidates = []
            self.page_index = 0
            
            xhy = self.model.get_xiehouyu_answer(word)
            if xhy:
                self.candidates = [xhy]
                self.update_ui()
                self.info_text.setText(f"【歇后语补全】\n{xhy}")
            else:
                last = word[-1]
                assoc = self.model.get_associations(last, top_k=20)
                if assoc:
                    self.candidates = assoc
                    self.update_ui()
                else:
                    self.clear_ui()

    def update_ui(self):
        start = self.page_index * self.PAGE_SIZE
        end = start + self.PAGE_SIZE
        current_page_data = self.candidates[start:end]
        
        for i in range(5):
            lbl = self.candidate_labels[i]
            if i < len(current_page_data):
                word = current_page_data[i]
                lbl.setText(f"{i+1}. {word}")
                lbl.setVisible(True)
            else:
                lbl.setText("")
                lbl.setVisible(False)
        
        total_pages = (len(self.candidates) + self.PAGE_SIZE - 1) // self.PAGE_SIZE
        if total_pages > 1:
            self.page_label.setText(f"{self.page_index + 1}/{total_pages}")
        else:
            self.page_label.setText("")

        if current_page_data:
            self.show_definition_by_ui_index(0)

    def show_definition_by_ui_index(self, ui_idx):
        real_idx = self.page_index * self.PAGE_SIZE + ui_idx
        if real_idx < len(self.candidates):
            w = self.candidates[real_idx]
            defn = self.model.kb.get_definition(w)
            if w == "守株待兔" and len(defn) < 50:
                 defn += "\n\n【测试文本】\n" + "测试滚动条 " * 20
            self.info_text.setText(f"【{w}】\n{defn}")

    def clear_ui(self):
        for lbl in self.candidate_labels:
            lbl.setText("")
        self.page_label.setText("")
        self.info_text.setText("")

if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    app.setFont(QFont("微软雅黑", 10))
    
    win = InputMethodWindow()
    win.show()
    sys.exit(app.exec_())
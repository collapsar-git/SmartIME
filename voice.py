import speech_recognition as sr

class VoiceRecognizer:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        
    def listen_and_convert(self):
        """
        监听麦克风并转换为文字
        :return: (success: bool, content: str)
        """
        try:
            with sr.Microphone() as source:
                # 调整环境噪音 (防止一开始就录入杂音)
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                print(">>> 正在聆听...")
                # 开始录音 (timeout=5 表示如果5秒没说话就超时)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
                print(">>> 正在识别...")
                # 调用 Google 免费 API (需联网)
                # language='zh-CN'，指定识别中文
                text = self.recognizer.recognize_google(audio, language='zh-CN')
                return True, text

        except sr.WaitTimeoutError:
            return False, "聆听超时 (没听到声音)"
        except sr.UnknownValueError:
            return False, "无法识别 (没听清)"
        except sr.RequestError as e:
            return False, f"网络请求失败: {e}"
        except Exception as e:
            return False, f"麦克风错误: {e}"

# 测试代码
if __name__ == "__main__":
    vr = VoiceRecognizer()
    print("请说话...")
    success, res = vr.listen_and_convert()
    print(f"结果: {res}")
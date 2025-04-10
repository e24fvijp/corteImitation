import pyaudio
import websocket
import json
import threading
import logging
import time
import wave
import io

class SpeechRecognizer:
    def __init__(self, authorization_key, grammar_file_names="-a-medical"):
        # ログ設定
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(threadName)s %(message)s")

        # 設定
        self.server = 'wss://acp-api.amivoice.com/v1/'
        self.codec = "16K"
        self.audio_block_size = 16000
        self.grammar_file_names = grammar_file_names
        self.options = {
            "profileId": "",
            "profileWords": "",
            "keepFillerToken": "",
            "resultUpdatedInterval": "1000",
            "authorization": authorization_key,
        }

        # 音声録音設定
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000

        # 初期化
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.is_recording = False
        self.audio_buffer = io.BytesIO()
        self.wave_file = wave.open(self.audio_buffer, 'wb')
        self.wave_file.setnchannels(self.CHANNELS)
        self.wave_file.setsampwidth(self.p.get_sample_size(self.FORMAT))
        self.wave_file.setframerate(self.RATE)
        self.last_send_time = 0
        self.audio_data = bytearray()
        self.ws_connected = False
        self.recognition_results = []
        self.ws = None
        self.recorder = None
        self.recognition_completed = False

    def set_ws_connected(self, connected):
        self.ws_connected = connected

    def add_recognition_result(self, text):
        self.recognition_results.append(text)

    def get_all_results(self):
        return "\n".join(self.recognition_results)

    def clear_results(self):
        self.recognition_results = []

    def set_recognition_completed(self, completed):
        self.recognition_completed = completed

    def is_recognition_completed(self):
        return self.recognition_completed

    def start_recording(self):
        self.is_recording = True
        self.stream = self.p.open(format=self.FORMAT,
                                channels=self.CHANNELS,
                                rate=self.RATE,
                                input=True,
                                frames_per_buffer=self.CHUNK)
        
        def record():
            while self.is_recording:
                try:
                    data = self.stream.read(self.CHUNK)
                    self.audio_data.extend(data)
                    
                    # 音声データの送信間隔を調整
                    current_time = time.time()
                    if current_time - self.last_send_time >= 0.1:  # 100msごとに送信
                        if len(self.audio_data) >= self.CHUNK and self.ws_connected:
                            try:
                                self.ws.send(b'p' + bytes(self.audio_data), opcode=websocket.ABNF.OPCODE_BINARY)
                                self.audio_data.clear()
                                self.last_send_time = current_time
                            except Exception as e:
                                self.logger.error(f"音声データ送信エラー: {e}")
                                self.ws_connected = False
                except Exception as e:
                    self.logger.error(f"録音エラー: {e}")

        threading.Thread(target=record).start()

    def stop_recording(self):
        self.is_recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.wave_file.close()
        self.audio_buffer.close()

    def on_open(self, ws):
        print("WebSocket接続を開始しました")
        self.set_ws_connected(True)
        def start(*args):
            command = f"s {self.codec} {self.grammar_file_names}"
            for k, v in self.options.items():
                if v != "":
                    if k == 'profileWords':
                        v = '"' + v.replace('"', '""') + '"'
                    command += f" {k}={v}"
            print(f"送信コマンド: {command}")
            ws.send(command)
        threading.Thread(target=start).start()

    def on_message(self, ws, message):
        try:
            print(f"受信メッセージ: {message}")
            event = message[0]
            content = message[2:].rstrip()
            
            if event == 'A':  # 最終認識結果
                try:
                    result = json.loads(content)
                    print(f"解析結果: {result}")
                    if 'text' in result:
                        self.add_recognition_result(result['text'])
                        print(f"認識結果を追加: {result['text']}")
                        self.set_recognition_completed(True)
                    else:
                        print(f"textキーが見つかりません: {result}")
                except json.JSONDecodeError as e:
                    print(f"JSONデコードエラー: {e}")
            elif event == 'e':
                print("セッション終了イベントを受信")
                self.set_ws_connected(False)
                self.set_recognition_completed(True)
                ws.close()
            else:
                print(f"未処理のイベント: {event}")
        except Exception as e:
            print(f"メッセージ処理エラー: {e}")
            self.logger.error(f"メッセージ処理エラー: {e}")

    def on_error(self, ws, error):
        print(f"WebSocketエラー: {error}")  # デバッグ用
        self.logger.error(f"WebSocketエラー: {error}")
        self.set_ws_connected(False)

    def on_close(self, ws, close_status_code, close_msg):
        print(f"WebSocket接続を終了: {close_status_code} - {close_msg}")  # デバッグ用
        self.set_ws_connected(False)

    def start(self):
        print("音声認識を開始します")  # デバッグ用
        # WebSocket接続の確立
        self.ws = websocket.WebSocketApp(self.server,
                                    on_open=self.on_open,
                                    on_message=self.on_message,
                                    on_error=self.on_error,
                                    on_close=self.on_close)
        
        # WebSocket接続を別スレッドで開始
        ws_thread = threading.Thread(target=self.ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()
        
        # 音声録音の開始
        self.start_recording()

    def stop(self):
        print("音声認識を停止します")  # デバッグ用
        self.stop_recording()
        if self.ws:
            self.ws.close()
import pyaudio
import websocket
import json
import threading
import logging
import time
import wave
import io

# ログ設定
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(threadName)s %(message)s")

# 設定
server = 'wss://acp-api.amivoice.com/v1/'
codec = "16K"
audio_block_size = 16000
grammar_file_names = "-a-medical"
options = {
    "profileId": "",
    "profileWords": "",
    "keepFillerToken": "",
    "resultUpdatedInterval": "1000",
    "authorization": "BBAC06D6306C65E12301E942BECA07C9A9A6A8C8E0174628ABA6D0B32597130D",
}

# 音声録音設定
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

class AudioRecorder:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.is_recording = False
        self.audio_buffer = io.BytesIO()
        self.wave_file = wave.open(self.audio_buffer, 'wb')
        self.wave_file.setnchannels(CHANNELS)
        self.wave_file.setsampwidth(self.p.get_sample_size(FORMAT))
        self.wave_file.setframerate(RATE)
        self.last_send_time = 0
        self.audio_data = bytearray()

    def start_recording(self):
        self.is_recording = True
        self.stream = self.p.open(format=FORMAT,
                                channels=CHANNELS,
                                rate=RATE,
                                input=True,
                                frames_per_buffer=CHUNK)
        
        def record():
            while self.is_recording:
                try:
                    data = self.stream.read(CHUNK)
                    self.audio_data.extend(data)
                    
                    # 音声データの送信間隔を調整
                    current_time = time.time()
                    if current_time - self.last_send_time >= 0.1:  # 100msごとに送信
                        if len(self.audio_data) >= CHUNK:
                            try:
                                ws.send(b'p' + bytes(self.audio_data), opcode=websocket.ABNF.OPCODE_BINARY)
                                logger.debug(f"音声データ送信: {len(self.audio_data)} bytes")
                                self.audio_data.clear()
                                self.last_send_time = current_time
                            except Exception as e:
                                logger.error(f"音声データ送信エラー: {e}")
                except Exception as e:
                    logger.error(f"録音エラー: {e}")

        threading.Thread(target=record).start()

    def stop_recording(self):
        self.is_recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.wave_file.close()
        self.audio_buffer.close()

def on_open(ws):
    logger.info("WebSocket接続を開始")
    def start(*args):
        command = f"s {codec} {grammar_file_names}"
        for k, v in options.items():
            if v != "":
                if k == 'profileWords':
                    v = '"' + v.replace('"', '""') + '"'
                command += f" {k}={v}"
        logger.info(f"送信コマンド: {command}")
        ws.send(command)
    threading.Thread(target=start).start()

def on_message(ws, message):
    try:
        event = message[0]
        content = message[2:].rstrip()
        
        logger.debug(f"受信メッセージ: {message}")
        
        if event == 'U':
            try:
                result = json.loads(content)
                if 'result' in result:
                    print(f"\n認識結果: {result['result']}")
            except json.JSONDecodeError as e:
                logger.error(f"JSONデコードエラー: {e}")
        elif event == 'e':
            logger.info("セッション終了")
            ws.close()
    except Exception as e:
        logger.error(f"メッセージ処理エラー: {e}")

def on_error(ws, error):
    logger.error(f"WebSocketエラー: {error}")

def on_close(ws, close_status_code, close_msg):
    logger.info(f"WebSocket接続を終了: {close_status_code} - {close_msg}")

def main():
    global ws
    # WebSocket接続の確立
    ws = websocket.WebSocketApp(server,
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)
    
    # WebSocket接続を別スレッドで開始
    ws_thread = threading.Thread(target=ws.run_forever)
    ws_thread.daemon = True
    ws_thread.start()
    
    # 音声録音の開始
    recorder = AudioRecorder()
    print("音声認識を開始します。Ctrl+Cで終了します。")
    print("マイクに向かって話しかけてください...")
    try:
        recorder.start_recording()
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n音声認識を終了します...")
        recorder.stop_recording()
        ws.close()

if __name__ == "__main__":
    main() 
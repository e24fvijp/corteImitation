import pyaudio
import websocket
import json
import threading
import logging
import time
import wave
import io
import streamlit as st

# ログ設定
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(threadName)s %(message)s")

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
        self.recognized_texts = []

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
                    
                    current_time = time.time()
                    if current_time - self.last_send_time >= 0.1:
                        if len(self.audio_data) >= CHUNK:
                            try:
                                ws.send(b'p' + bytes(self.audio_data), opcode=websocket.ABNF.OPCODE_BINARY)
                                self.audio_data.clear()
                                self.last_send_time = current_time
                            except Exception as e:
                                st.error(f"音声データ送信エラー: {e}")
                except Exception as e:
                    st.error(f"録音エラー: {e}")

        threading.Thread(target=record).start()

    def stop_recording(self):
        self.is_recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.wave_file.close()
        self.audio_buffer.close()

    def add_recognized_text(self, text):
        if text and text != "..." and text not in self.recognized_texts:
            self.recognized_texts.append(text)

def on_message(ws, message):
    try:
        event = message[0]
        content = message[2:].rstrip()
        
        if event == 'U':
            try:
                result = json.loads(content)
                if 'results' in result and len(result['results']) > 0:
                    text = result['results'][0]['text']
                    if text and text != "...":
                        recorder.add_recognized_text(text)
            except json.JSONDecodeError:
                pass
        elif event == 'e':
            ws.close()
    except Exception:
        pass

def on_open(ws):
    def start(*args):
        command = f"s {codec} {grammar_file_names}"
        for k, v in options.items():
            if v != "":
                if k == 'profileWords':
                    v = '"' + v.replace('"', '""') + '"'
                command += f" {k}={v}"
        ws.send(command)
    threading.Thread(target=start).start()

def on_error(ws, error):
    st.error(f"WebSocketエラー: {error}")

def on_close(ws, close_status_code, close_msg):
    pass

# Streamlitアプリケーション
st.title("音声認識アプリ")

if 'recorder' not in st.session_state:
    st.session_state.recorder = AudioRecorder()
    st.session_state.ws = None
    st.session_state.is_recording = False

recorder = st.session_state.recorder

if not st.session_state.is_recording:
    if st.button("録音開始"):
        st.session_state.is_recording = True
        # WebSocket接続の確立
        ws = websocket.WebSocketApp(server,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
        st.session_state.ws = ws
        
        # WebSocket接続を別スレッドで開始
        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()
        
        # 接続が確立するまで待機
        time.sleep(2)
        
        # 録音開始
        recorder.start_recording()
        st.rerun()
else:
    if st.button("録音停止"):
        st.session_state.is_recording = False
        recorder.stop_recording()
        if st.session_state.ws:
            st.session_state.ws.close()
        
        # 認識結果を表示
        st.write("### 認識結果")
        for text in recorder.recognized_texts:
            st.write(text)
        
        # 結果をクリア
        # recorder.recognized_texts = []
        # st.rerun()

if st.session_state.is_recording:
    st.write("録音中...")


import streamlit as st
import AmiVoice_recognition
import time

# 認証キーの設定
AUTH_KEY = "BBAC06D6306C65E12301E942BECA07C9A9A6A8C8E0174628ABA6D0B32597130D"

# セッション状態の初期化
if 'recognizer' not in st.session_state:
    print("SpeechRecognizerを初期化します")
    st.session_state.recognizer = AmiVoice_recognition.SpeechRecognizer(AUTH_KEY)
    st.session_state.is_recording = False
    st.session_state.results = ""
    st.session_state.last_results = ""

def toggle_recording():
    if not st.session_state.is_recording:
        # 録音開始
        print("録音を開始します")
        st.session_state.recognizer.clear_results()
        st.session_state.recognizer.start()
        st.session_state.is_recording = True
        st.session_state.results = ""
    else:
        # 録音停止
        print("録音を停止します")
        st.session_state.recognizer.stop()
        results = st.session_state.recognizer.get_all_results()
        print(f"取得した認識結果: {results}")
        st.session_state.results = results
        st.session_state.last_results = results
        st.session_state.is_recording = False

# アプリケーションのタイトル
st.title("音声認識アプリケーション")

# 録音状態の表示
status_text = st.empty()
if st.session_state.is_recording:
    status_text.info("録音中... マイクに向かって話しかけてください")
else:
    status_text.info("録音を開始するにはボタンを押してください")

# 録音ボタン
button_text = "録音停止" if st.session_state.is_recording else "録音開始"
if st.button(button_text, on_click=toggle_recording):
    pass

# 認識結果の表示
if st.session_state.last_results:
    st.subheader("認識結果")
    st.text_area("認識結果", st.session_state.last_results, height=200, label_visibility="collapsed") 
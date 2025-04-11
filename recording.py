import streamlit as st
import pickle
import datetime 
import time
import AmiVoice_recognition
import dotenv
import os

import function

dotenv.load_dotenv()
APP_KEY = os.getenv("AMIVOICE_API_KEY")
# セッション状態の初期化
if 'recognizer' not in st.session_state:
    st.session_state.recognizer = AmiVoice_recognition.SpeechRecognizer(APP_KEY)
    st.session_state.is_recording = False
    st.session_state.results = ""
    st.session_state.last_results = ""
    st.session_state.recognition_completed = False
    st.session_state.processing_started = False
    st.session_state.remarks = ""  # 備考欄の状態を追加

# 備考欄のセッション状態が存在しない場合は初期化
if 'remarks' not in st.session_state:
    st.session_state.remarks = ""

#ページの翻訳提案をしないように設定
st.markdown(
    '<meta name="google" content="notranslate">', 
    unsafe_allow_html=True
)

st.title('音声解析アプリケーション')

#薬剤師リストの読み込み
pharmacist_list_path = "save_dir/pharmacist_list.pickle"
with open(pharmacist_list_path,"rb") as f:
    pharmacist_list = pickle.load(f)
    pharmacist_list = [name for name in pharmacist_list if name]

user = st.radio(
    "薬剤師を選択",
    pharmacist_list,
    horizontal = True
)

# 備考欄をセッション状態と連動させる
remarks_input = st.text_area(
    "備考欄(検索キー)",
    value=st.session_state.remarks,
    height=68,
    max_chars=200,
    key="remarks_input",
    on_change=lambda: setattr(st.session_state, 'remarks', st.session_state.remarks_input)
)

def toggle_recording():
    if not st.session_state.is_recording:
        # 録音開始
        print("録音を開始します")
        st.session_state.recognizer.clear_results()
        st.session_state.recognizer.start()
        st.session_state.is_recording = True
        st.session_state.results = ""
        st.session_state.recognition_completed = False
        st.session_state.processing_started = False
    else:
        # 録音停止
        print("録音を停止します")
        st.session_state.recognizer.stop()
        results = st.session_state.recognizer.get_all_results()
        st.session_state.results = results
        st.session_state.last_results = results
        st.session_state.is_recording = False
        st.session_state.recognition_completed = st.session_state.recognizer.is_recognition_completed()
        st.session_state.processing_started = True

# 録音状態の表示
status_text = st.empty()
if st.session_state.is_recording:
    status_text.info("録音中... マイクに向かって話しかけてください\n録音は10秒未満ではうまく認識されない場合があります")
else:
    status_text.info("録音を開始するにはボタンを押してください")

# 録音ボタン
button_text = "録音停止" if st.session_state.is_recording else "録音開始"
if st.button(button_text, on_click=toggle_recording):
    pass

place1 = st.empty()

if st.session_state.processing_started and st.session_state.recognition_completed:
    if st.session_state.last_results != "":
        place1.warning("音声認識が完了しました。要約中です。")
        f = function.Functions()
        recoganised_text = st.session_state.last_results
        summary = f.make_summary(recoganised_text)
        f.append_pickle_files(user, "now", st.session_state.remarks, summary)
        st.session_state.processing_started = False
        st.session_state.recognition_completed = False
        st.session_state.results = ""
        st.session_state.last_results = ""
        st.session_state.remarks = ""  # 備考欄を空にする
        place1.warning("要約が完了しデータを保存しました。")
    else:
        place1.warning("認識結果のテキストが存在しません。\n録音が短すぎる可能性があります。")

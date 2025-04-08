import datetime
import io
import os
import pathlib
import pickle
import time
import numpy as np
import noisereduce as nr

from audio_recorder_streamlit import audio_recorder
from dotenv import load_dotenv
from openai import OpenAI
from pydub import AudioSegment
import requests
import streamlit as st

#ページの翻訳提案をしないように設定
st.markdown(
    '<meta name="google" content="notranslate">', 
    unsafe_allow_html=True
)

# OpenAI API キー（環境変数から取得）
WHISPER_API_URL = "https://api.openai.com/v1/audio/transcriptions"

# 環境変数よりOPENAIAPIKEYの取得
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 音声ファイル保存用のディレクトリを作成
AUDIO_DIR = "./audioData"

def save_audio_file(audio_bytes, user):
    """
    音声ファイルを保存する関数
    """
    # 現在の日時を取得
    now = datetime.datetime.now()
    date_str = now.strftime("%Y%m%d")
    time_str = now.strftime("%H%M%S")
    # 日付ごとのディレクトリを作成
    date_dir = os.path.join(AUDIO_DIR, date_str)
    pathlib.Path(date_dir).mkdir(exist_ok=True)
    # ファイル名を生成（日付_時間_ユーザー名.wav）
    filename = f"{date_str}_{time_str}_{user}.wav"
    filepath = os.path.join(date_dir, filename)
    # 音声ファイルを保存
    with open(filepath, "wb") as f:
        f.write(audio_bytes)
    
    return filepath

def transcribe_whisper(audio_bytes) -> str:
    """
    OpenAI Whisper API を使って音声をテキストに変換する
    """
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }

    files = {
        "file": ("audio.wav", audio_bytes, "audio/wav"),
        "model": (None, "whisper-1"),
        "language": (None, "ja"),  # 日本語を指定
    }

    response = requests.post(WHISPER_API_URL, headers=headers, files=files)
    
    if response.status_code == 200:
        return response.json().get("text", "テキスト化に失敗しました")
    else:
        return f"エラー: {response.text}"

def transcribe_AmiVoice(audio_bytes) -> str:
    pass

def make_summary(prompt):

    client = OpenAI(api_key=OPENAI_API_KEY)

    with open("prompt.txt","r", encoding="utf-8") as f:
        system_content = f.read()

    res = client.chat.completions.create(
        model = "gpt-4o-mini",
        messages= [
            {"role": "system", "content": system_content},
            {"role": "user", "content": prompt}
        ]
    )
    # 要約結果を返す
    return res.choices[0].message.content

def append_pickle_files(user, time_str, remarks, text, audio_path):
    """
    データをpickleファイルに保存する関数
    """
    today = datetime.date.today().strftime("%Y%m%d")
    save_path = f"./pickleData/{today}.pickle"
    append_data = [user, time_str, remarks, text, audio_path]  # 音声ファイルパスを追加
    if os.path.exists(save_path):
        with open(save_path,"rb") as f:
            data = pickle.load(f)
        data.append(append_data)
    else:
        data = [append_data]
    with open(save_path,"wb") as f:
        pickle.dump(data,f)

def audio_processor(audio_byte):
    # BytesIO オブジェクトに変換
    audio_io = io.BytesIO(audio_byte)
    # pydub で wav 読み込み & モノラル変換
    audio = AudioSegment.from_wav(audio_io)
    audio_np = np.array(audio.get_array_of_samples())
    reduced_audio_np = nr.reduce_noise(y=audio_np,sr=audio.frame_rate)
    reduced_audio = AudioSegment(
        reduced_audio_np.tobytes(),
        frame_rate=audio.frame_rate,
        sample_width=audio.sample_width,
        channels=audio.channels
    )
    # 音量の正規化（-20dBFSに正規化）
    normalized_audio = reduced_audio.normalize(headroom=0.1)
    # 音声データをバイト列に変換
    wav_io = io.BytesIO()
    normalized_audio.export(wav_io, format="wav")
    wav_bytes = wav_io.getvalue()
    return wav_bytes


#メインプログラム
# タイトルを設定
st.title('音声解析アプリケーション')

#薬剤師リストの読み込み
pharmacist_list_path = "pharmacist_list.pickle"
with open(pharmacist_list_path,"rb") as f:
    pharmacist_list = pickle.load(f)
    pharmacist_list = [name for name in pharmacist_list if name]

user = st.radio(
    "薬剤師を選択",
    pharmacist_list,
    horizontal = True
)

engine = st.radio(
    "音声解析エンジンを選択   whisper:約50円/時間 AmiVoice 297.0円/時間 医療特化",
    ["whisper","AmiVoice"],
    horizontal=True
)

remarks_input = st.text_area("備考欄(検索キー)","",height=68, max_chars=200)

audio_bytes = audio_recorder(pause_threshold=60.0)

place1 = st.empty()
place2 = st.empty()

if audio_bytes:
    place1.write("未解析の音声があります。解析開始を押してください。")
else:
    place1.write("音声データはありません")

if st.button("解析開始"):
    place1.write("")
    if not audio_bytes:
        place2.warning("録音が存在しません")
    else:
        place2.warning("音声解析中です。終了するまで他のページに移動しないでください。")
        # 音声ファイルを保存
        audio_filepath = save_audio_file(audio_bytes, user)
        # 音声ファイルのノイズリダクション、音量の正規化
        wav_bytes = audio_processor(audio_bytes)
        # テキスト変換
        transcript = transcribe_whisper(wav_bytes) if engine == "Whisper" else transcribe_AmiVoice(wav_bytes)
        place2.warning("音声解析完了 GPTで要約中 完了後ページ遷移します。")
        summary = make_summary(transcript)
        time_str = datetime.datetime.now().strftime("%H:%M")
        append_pickle_files(user, time_str, remarks_input, summary, audio_filepath)
        place2.warning("解析完了 保存しました") 
        time.sleep(0.5)
        st.switch_page("pages/data.py")
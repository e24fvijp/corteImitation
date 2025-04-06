import datetime
import io
import os
import pickle
import pathlib

from audio_recorder_streamlit import audio_recorder
from dotenv import load_dotenv
from openai import OpenAI
from pydub import AudioSegment
import requests
import streamlit as st
import streamlit.components.v1 as stc


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

def transcribe_audio(audio_bytes) -> str:
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

def make_summary(prompt):

    client = OpenAI(api_key=OPENAI_API_KEY)

    with open("prompt.txt","r", encoding="utf-8") as f:
        system_content = f.read()

    # 修正：ChatCompletion.create を使用
    res = client.chat.completions.create(
        model = "gpt-4o-mini",
        messages= [
            {"role": "system", "content": system_content},
            {"role": "user", "content": prompt}
        ]
    )
    # 要約結果を返す
    return res.choices[0].message.content

def append_pickle_files(user, remarks, text, audio_path):
    """
    データをpickleファイルに保存する関数
    """
    today = datetime.date.today().strftime("%Y%m%d")
    save_path = f"./pickleData/{today}.pickle"
    append_data = [user, remarks, text, audio_path]  # 音声ファイルパスを追加
    if os.path.exists(save_path):
        with open(save_path,"rb") as f:
            data = pickle.load(f)
        data.append(append_data)
    else:
        data = [append_data]
    with open(save_path,"wb") as f:
        pickle.dump(data,f)

#メインプログラム
# タイトルを設定
st.title('音声解析アプリケーション')

user = st.radio(
    "薬剤師を選択",
    ["薬剤師A","薬剤師B","薬剤師C"],
    horizontal = True
)

remarks_input = st.text_area("備考欄(検索キー)","",height=68, max_chars=200)

audio_bytes = audio_recorder(pause_threshold=60.0)

if st.button("解析開始"):
    place1 = st.empty()
    if not audio_bytes:
        place1.write("録音が存在しません")
    else:
        place1.write("")
        place2 = st.empty()
        place2.write("解析中...")

        # 音声ファイルを保存
        audio_filepath = save_audio_file(audio_bytes, user)

        # BytesIO オブジェクトに変換
        audio_io = io.BytesIO(audio_bytes)

        # pydub で wav 読み込み & モノラル変換
        audio = AudioSegment.from_wav(audio_io)
        audio = audio.set_channels(1).set_frame_rate(16000)

        # 音声データをバイト列に変換
        wav_io = io.BytesIO()
        audio.export(wav_io, format="wav")
        wav_bytes = wav_io.getvalue()

        # テキスト変換
        transcript = transcribe_audio(wav_bytes)
        place2.write("音声解析完了 GPTで要約中")
        summary = make_summary(transcript)  
        append_pickle_files(user, remarks_input, summary, audio_filepath)
        place2.write("解析完了 保存しました") 


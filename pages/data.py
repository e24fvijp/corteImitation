import datetime
import os
import pickle
import streamlit as st
import streamlit.components.v1 as stc
from pathlib import Path
from pydub import AudioSegment
from dotenv import load_dotenv
import requests
import io
import numpy as np
import noisereduce as nr
from openai import OpenAI

#ページの翻訳提案をしないように設定
st.markdown(
    '<meta name="google" content="notranslate">', 
    unsafe_allow_html=True
)

#cssで余白の設定
st.markdown(
    """
    <style>
    .copy-button {
        padding: 0px;  /* 余白を完全に削減 */
        margin: 0px;   /* 余白を完全に削減 */
        font-size: 6px;  /* 文字サイズをさらに小さく */
        background-color: #4CAF50;
        color: yellow;
        border: none;
        cursor: pointer;
        display: inline-block;
        height: 10px;  /* ボタン高さを小さく */
        width: 15px;   /* ボタン幅を小さく */
    }
    .custom {
        background-color: #f9f9f9;
        padding: 0px;
        border-radius: 5px;
        font-size: 18px;  /* 小さな文字サイズ */
    }
    </style>
    """,
    unsafe_allow_html=True)

# OpenAI API キー（環境変数から取得）
WHISPER_API_URL = "https://api.openai.com/v1/audio/transcriptions"

# 環境変数よりOPENAIAPIKEYの取得
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def write_copyable_text(text):
    if ":" in text:
        copy_text = text.split(":")[1].strip()
    else:
        copy_text = text
    html_content = f"""
    <button class="copy-button" onclick="navigator.clipboard.writeText('{copy_text}')">
        copy
    </button>
    """

    if ":" in text:
        col1, col2, col3 = st.columns([1,3,20])
        with col1:
            st.markdown(f'<div class="custom">{text.split(":")[0]}</div>', unsafe_allow_html=True)
        with col2:
            stc.html(html_content, height=30)
        with col3:
            st.markdown(f'<div class="custom">{text.split(":")[1]}</div>', unsafe_allow_html=True)
    else:
        col1, col2, col3 = st.columns([1,3,20])
        with col2:
            stc.html(html_content, height=30)
        with col3:
            st.markdown(f'<div class="custom">{text}</div>', unsafe_allow_html=True)

def play_audio(audio_path):
    """
    音声ファイルを再生する関数
    """
    if os.path.exists(audio_path):
        audio = AudioSegment.from_wav(audio_path)
        st.audio(audio_path, format="audio/wav")
    else:
        st.error("音声ファイルが見つかりません")

def show_result(data_list):
    remarks_list = [""] + [x[2] for x in data_list]
    remarks_select = st.selectbox(
        "備考欄で検索",
        remarks_list
    )
    if remarks_select != "":
        data_list = [x for x in data_list if x[2] == remarks_select]
    for data in data_list:
        time, remarks, text, audio_path = data[1], data[2], data[3], data[4]
        
        # 各データをexpanderで囲む
        with st.expander(f"時間: {time}   備考: {remarks}", expanded=True):
            # テキストの表示
            for line in text.split("\n"):
                if line.strip() != "":
                    for line_sprit in line.strip().split("。"):
                        if line_sprit.strip() != "":
                            write_copyable_text(line_sprit.strip())
            # 音声再生ボタン
            if st.button(f"音声を再生", key=f"play_{audio_path}"):
                play_audio(audio_path)

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

def append_pickle_files(user, remarks, text, audio_path):
    """
    データをpickleファイルに保存する関数
    """
    time_part = Path(audio_path).name.split("_")[1]
    time_str = datetime.datetime.strptime(time_part, "%H%M%S").strftime("%H:%M")
    date_str = Path(audio_path).name.split("_")[0]
    save_path = f"./pickleData/{date_str}.pickle"
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

def check_unprocessed(date):
    #audioファイルはあるが、解析済みのpickleデータがないもののチェック
    unprocessed_wav_list = []
    date_str = date.strftime('%Y%m%d')
    pickle_file_path = f"./pickleData/{date_str}.pickle"
    wav_folder_path = Path(f"audioData/{date_str}/")
    wav_file_paths = list(wav_folder_path.glob("*.wav"))
    if os.path.exists(pickle_file_path):
        with open(pickle_file_path,"rb") as f:
            all_data = pickle.load(f)
        for wav_file_path in wav_file_paths:
            wav_path_list_from_pickle = [Path(data[-1]).resolve() for data in all_data]
            if Path(wav_file_path).resolve() not in wav_path_list_from_pickle:
                unprocessed_wav_list.append(wav_file_path)
    else:
        unprocessed_wav_list = wav_file_paths
    return unprocessed_wav_list

def load_and_analyze_unprocessed(unprocessed_list):
    for audio_path in unprocessed_list:
        audio = AudioSegment.from_wav(audio_path)
        wav_io = io.BytesIO()
        audio.export(wav_io, format="wav")
        audio_bytes = wav_io.getvalue()
        wav_bytes = audio_processor(audio_bytes)
        engine = "Whisper"
        transcript = transcribe_whisper(wav_bytes) if engine == "Whisper" else transcribe_AmiVoice(wav_bytes)
        summary = make_summary(transcript)
        user = Path(audio_path).name.split("_")[2].split(".")[0]
        append_pickle_files(user, "", summary, audio_path)

selected_date = st.date_input(
    "日付を選択(録音日)",
    value="today",
    min_value=None,
    max_value=None,
    format="YYYY/MM/DD"
)

place1 = st.empty()

unprocessed_list = check_unprocessed(selected_date)

if unprocessed_list:
    place1.warning("選択した日付に録音後解析済みでない音声ファイルが存在します。必要であれば再解析ボタンを押してください。備考欄は復旧できません")
    if st.button("再解析"):
        place1.warning("音声の再解析中 終了まで数分かかる場合があります")
        load_and_analyze_unprocessed(unprocessed_list)
        place1.warning("解析終了")
        

if selected_date:
    search_file_path = f"./pickleData/{selected_date.strftime('%Y%m%d')}.pickle"
    if os.path.exists(search_file_path):
        with open(search_file_path, "rb") as f:
            data = pickle.load(f)
        user_list = list(set([x[0] for x in data]))
        user = st.radio(
            "薬剤師を選択",
            user_list,
            horizontal=True
        )
        show_data = [x for x in data if x[0] == user]
        show_result(show_data)
    else:
        st.write(f"{selected_date}のデータはありません")

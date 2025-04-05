import os
import io
import openai
import requests
import streamlit as st
import streamlit.components.v1 as stc
from audio_recorder_streamlit import audio_recorder
from pydub import AudioSegment
from dotenv import load_dotenv
import os

# OpenAI API キー（環境変数から取得）
WHISPER_API_URL = "https://api.openai.com/v1/audio/transcriptions"
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

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
    openai.api_key = OPENAI_API_KEY  # OpenAI APIキーを設定
    
    system_content = """
    あなたは薬剤師です。薬剤師と患者の会話シーンです。
    誰が喋っている言葉かは想像してください。
    文章を患者の主観（Ｓ）、データなどの客観情報（Ｏ）、薬剤師の評価考察（Ａ）、薬剤師の指導内容（Ｐ）として内容を要約して、
    S:
    O:
    A:
    P:
    のような形式で箇条書きで事実のみを出力してください。各項目に2文ある場合は句点、読点で改行。
    :はS,O,A,Pの後以外では使わないでください。
    2行ある場合はS:とつけるのは一つ目の項目のみ。
    質問とその解答がある場合はその解答を完結に書いてください。(例    心不全ですか？はい → 心不全)など
    会話の中に出てこなかったものは出力せず、SOAPに合致するものがなければその項目は出力不要。
    自己紹介文や関係なさそうなものは省いてください。
    """

    # 修正：ChatCompletion.create を使用
    res = openai.ChatCompletion.create(
    model="gpt-4o-mini",
    messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": prompt}
        ]
    )

    # 要約結果を返す
    return res["choices"][0]["message"]["content"]

def write_copyable_text(text):
    html_content = f"""
    <button onclick="navigator.clipboard.writeText('{text}')">
        copy
    </button>
    """

    if ":" in text:
        st.write(text.split(":")[0])
        col1,col2 = st.columns([1,3])
        with col1:
            stc.html(html_content,height=30)
        with col2:
            st.write(text.split(":")[1])
    else:
        col1,col2 = st.columns([1,3])
        with col1:
            stc.html(html_content,height=30)
        with col2:
            st.write(text)

audio_bytes = audio_recorder(pause_threshold=60.0)

if st.button("解析開始"):
    place1 = st.empty()
    if not audio_bytes:
        place1.write("録音が存在しません")
    else:
        place1.write("")
        place2 = st.empty()
        place2.write("解析中...")

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
        place2.write("")
        
        sql.ConnectSQl()
        

        # st.write(summary)
        lines = summary.split("\n")
        for line in lines:
            write_copyable_text(line)


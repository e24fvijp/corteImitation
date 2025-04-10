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

load_dotenv()

class Functions:

    def __init__(self):
        self.AUDIO_DIR = "./audioData"
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.WHISPER_API_URL = "https://api.openai.com/v1/audio/transcriptions"

    def save_audio_file(self, audio_file, user):
        """
        音声ファイルを保存する関数
        """
        # 現在の日時を取得
        now = datetime.datetime.now()
        date_str = now.strftime("%Y%m%d")
        time_str = now.strftime("%H%M%S")
        # 日付ごとのディレクトリを作成
        date_dir = os.path.join(self.AUDIO_DIR, date_str)
        pathlib.Path(date_dir).mkdir(exist_ok=True)
        # ファイル名を生成（日付_時間_ユーザー名.wav）
        filename = f"{date_str}_{time_str}_{user}.wav"
        filepath = os.path.join(date_dir, filename)
        # 音声ファイルを保存
        with open(filepath, "wb") as f:
            f.write(audio_file)
        
        return filepath
    
    def transcribe_whisper(self, audio_bytes) -> str:
        """
        OpenAI Whisper API を使って音声をテキストに変換する
        """
        headers = {
            "Authorization": f"Bearer {self.OPENAI_API_KEY}",
        }

        files = {
            "file": ("audio.wav", audio_bytes, "audio/wav"),
            "model": (None, "whisper-1"),
            "language": (None, "ja"),  # 日本語を指定
        }

        response = requests.post(self.WHISPER_API_URL, headers=headers, files=files)
        
        if response.status_code == 200:
            return response.json().get("text", "テキスト化に失敗しました")
        else:
            return f"エラー: {response.text}"
        
    def transcribe_AmiVoice():
        pass


    def make_summary(self, prompt):

        client = OpenAI(api_key=self.OPENAI_API_KEY)

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

    def append_pickle_files(self,user, time_str, remarks, text, audio_path):
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

    def audio_processor(self, audio_byte):
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
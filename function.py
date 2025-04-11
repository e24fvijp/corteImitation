import datetime
import io
import os
import pickle
import numpy as np
import noisereduce as nr
from dotenv import load_dotenv
from openai import OpenAI
from pydub import AudioSegment
import streamlit as st
import streamlit.components.v1 as stc

load_dotenv()

class Functions:

    def __init__(self):
        self.PICKLE_PATH = "save_dir/pickleData/"
        self.AUDIO_DIR = "./audioData"
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.WHISPER_API_URL = "https://api.openai.com/v1/audio/transcriptions"

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

    def append_pickle_files(self,user, time_str, remarks, text, completed = False, audio_path=None):
        """
        データをpickleファイルに保存する関数
        """
        today = datetime.date.today().strftime("%Y%m%d")
        save_path = self.PICKLE_PATH + f"{today}.pickle"
        if time_str == "now":
            time_str = datetime.datetime.now().strftime("%H:%M")
        append_data = [user, time_str, remarks, text, completed]  # 音声ファイルパスを追加
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

    def check_unprocessed(self,date):
        pass
        #audioファイルはあるが、解析済みのpickleデータがないもののチェック
        # unprocessed_wav_list = []
        # date_str = date.strftime('%Y%m%d')
        # pickle_file_path = f"./pickleData/{date_str}.pickle"
        # wav_folder_path = pathlib.Path(f"audioData/{date_str}/")
        # wav_file_paths = list(wav_folder_path.glob("*.wav"))
        # if os.path.exists(pickle_file_path):
        #     with open(pickle_file_path,"rb") as f:
        #         all_data = pickle.load(f)
        #     for wav_file_path in wav_file_paths:
        #         wav_path_list_from_pickle = [pathlib.Path(data[-1]).resolve() for data in all_data]
        #         if wav_file_path.resolve() not in wav_path_list_from_pickle:
        #             unprocessed_wav_list.append(wav_file_path)
        # else:
        #     unprocessed_wav_list = wav_file_paths
        # return unprocessed_wav_list
    
    def load_and_analyze_unprocessed(unprocessed_list):
        pass
        # for audio_path in unprocessed_list:
        #     audio = AudioSegment.from_wav(audio_path)
        #     wav_io = io.BytesIO()
        #     audio.export(wav_io, format="wav")
        #     audio_bytes = wav_io.getvalue()
        #     wav_bytes = audio_processor(audio_bytes)
        #     engine = "Whisper"
        #     transcript = transcribe_whisper(wav_bytes) if engine == "Whisper" else transcribe_AmiVoice(wav_bytes)
        #     summary = make_summary(transcript)
        #     user = Path(audio_path).name.split("_")[2].split(".")[0]
        #     append_pickle_files(user, "", summary, audio_path)

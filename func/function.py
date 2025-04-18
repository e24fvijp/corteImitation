import streamlit as st
import streamlit_authenticator as stauth
# import yaml
# from yaml.loader import SafeLoader
import datetime
import os
import pickle
# import dotenv 
from openai import OpenAI
import yaml

class Auth:
    def __init__(self):
        try:
            # Secretsから認証情報を取得
            config = {
                'credentials': {
                    'usernames': st.secrets["credentials"]["usernames"]
                },
                'cookie': st.secrets["cookie"]
            }
            
            self.authenticator = stauth.Authenticate(
                config['credentials'],
                config['cookie']['name'],
                config['cookie']['key'],
                config['cookie']['expiry_days']
            )
        except Exception as e:
            st.error(f"認証設定の読み込みに失敗しました: {str(e)}")
            st.error("Secretsの設定を確認してください。")
            st.stop()

class Functions:

    def __init__(self):
        self.PICKLE_PATH = "save_dir/pickleData/"
        # self._decrypt_env_file()
        self.OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]#os.getenv("OPENAI_API_KEY")
        self.AMIVOICE_APP_KEY = st.secrets["AMIVOICE_APP_KEY"]#os.getenv("AMIVOICE_APP_KEY")
        # self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        # self.WHISPER_API_URL = "https://api.openai.com/v1/audio/transcriptions"

    # def _decrypt_env_file(self,key_file='APIs/key.key', encrypted_file='APIs/.env.encrypted'):
    # #暗号化された.envファイルを復号化
    # #exe化した後はAPIsのフォルダも一緒に配布する必要あり、
    #     try:
    #         # 暗号化キーを読み込み
    #         with open(key_file, 'rb') as file:
    #             key = file.read()
            
    #         # 暗号化されたデータを読み込み
    #         with open(encrypted_file, 'rb') as file:
    #             encrypted_data = file.read()
            
    #         # 復号化
    #         f = Fernet(key)
    #         decrypted_data = f.decrypt(encrypted_data)
            
    #         # 一時的な.envファイルを作成
    #         with open('.env.temp', 'wb') as file:
    #             file.write(decrypted_data)
            
    #         # 環境変数を読み込み
    #         dotenv.load_dotenv('.env.temp')
            
    #         # 一時ファイルを削除
    #         os.remove('.env.temp')
            
    #     except Exception as e:
    #         return 
    #         logger.error(f"環境変数の復号化に失敗しました: {str(e)}")
    #         st.error("環境変数の読み込みに失敗しました。")
    #         st.stop()

    def make_summary(self, prompt):

        client = OpenAI(api_key=self.OPENAI_API_KEY)

        # with open("prompt.txt","r", encoding="utf-8") as f:
        #     system_content = f.read()
        system_content = """あなたは薬剤師です。薬剤師と患者の会話シーンです。
        誰が喋っている言葉かは想像してください。
        文章を患者の主観（Ｓ）、データなどの客観情報（Ｏ）、薬剤師の評価考察（Ａ）、薬剤師の指導内容（Ｐ）として内容を要約して、
        S:
        O:
        A:
        P:
        のような形式で箇条書きで事実のみを出力してください。:はS,O,A,Pの後以外では使わないでください。
        質問とその解答がある場合はその解答を完結に書いてください。(例    心不全ですか？はい → 心不全)など
        会話の中に出てこなかったものは出力せず、SOAPに合致するものがなければその項目は出力不要。
        自己紹介文やお大事にという閉めの言葉など関係なさそうなものはSOAPに含まないでください。
        """

        res = client.chat.completions.create(
            model = "gpt-4o-mini",
            messages= [
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt}
            ]
        )
        # 要約結果を返す
        return res.choices[0].message.content

    def append_pickle_files(self,user, time_str, remarks, recognition_text, summary_text, completed = False, audio_path=None):
        """
        データをpickleファイルに保存する関数
        """
        if not os.path.exists(self.PICKLE_PATH):
            os.makedirs(self.PICKLE_PATH)
        today = datetime.date.today().strftime("%Y%m%d")
        save_path = self.PICKLE_PATH + f"{today}.pickle"
        if time_str == "now":
            time_str = datetime.datetime.now().strftime("%H:%M")
        append_data = [user, time_str, remarks, recognition_text, summary_text, completed]  # 音声ファイルパスを追加
        if os.path.exists(save_path):
            with open(save_path,"rb") as f:
                data = pickle.load(f)
            data.append(append_data)
        else:
            data = [append_data]
        with open(save_path,"wb") as f:
            pickle.dump(data,f)

    # def audio_processor(self, audio_byte):
    #     # BytesIO オブジェクトに変換
    #     audio_io = io.BytesIO(audio_byte)
    #     # pydub で wav 読み込み & モノラル変換
    #     audio = AudioSegment.from_wav(audio_io)
    #     audio_np = np.array(audio.get_array_of_samples())
    #     reduced_audio_np = nr.reduce_noise(y=audio_np,sr=audio.frame_rate)
    #     reduced_audio = AudioSegment(
    #         reduced_audio_np.tobytes(),
    #         frame_rate=audio.frame_rate,
    #         sample_width=audio.sample_width,
    #         channels=audio.channels
    #     )
    #     # 音量の正規化（-20dBFSに正規化）
    #     normalized_audio = reduced_audio.normalize(headroom=0.1)
    #     # 音声データをバイト列に変換
    #     wav_io = io.BytesIO()
    #     normalized_audio.export(wav_io, format="wav")
    #     wav_bytes = wav_io.getvalue()
    #     return wav_bytes

    # def check_unprocessed(self,date):
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
    
    # def load_and_analyze_unprocessed(unprocessed_list):
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

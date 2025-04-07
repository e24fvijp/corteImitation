import os
import io
from google.cloud import speech
import streamlit as st
from audio_recorder_streamlit import audio_recorder
from pydub import AudioSegment

def transcribe_audio(audio_bytes) -> str:
    """
    ローカルの音声ファイルを読み込んでテキスト変換した結果を返す（話者識別付き）
    """
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:/corteImitation/speech-to-text-test-403802-733d27e22b93.json"

    client = speech.SpeechClient()

    # 音声データをバイト型に変換
    audio = speech.RecognitionAudio(content=audio_bytes)

    diarization_config = speech.SpeakerDiarizationConfig(
        enable_speaker_diarization=True,
        min_speaker_count=1,
        max_speaker_count=3,
    )

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="ja-JP",
        enable_word_confidence=True,
        diarization_config=diarization_config,
        use_enhanced=True,
        enable_automatic_punctuation=True,
    )

    response = client.recognize(config=config, audio=audio)

    # 話者識別結果を処理
    transcript = ""
    speaker_labels = {}

    for result in response.results:
        for word in result.alternatives[0].words:
            speaker = word.speaker_tag  # 話者タグを取得
            speaker_labels.setdefault(speaker, []).append(word.word)

    # 話者ごとの発話を整理
    for speaker, words in sorted(speaker_labels.items()):
        transcript += f"\n話者 {speaker}: " + " ".join(words) + "\n"

    return transcript

audio_bytes = audio_recorder(pause_threshold=30.0)



if st.button("解析開始"):
    if not audio_bytes:
        st.write("録音が存在しません")
    else:
        place_holder = st.empty()
        place_holder.write("解析中")
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
        place_holder.write("解析完了")
        st.write(transcript)
import os
import pickle
import streamlit as st
import streamlit.components.v1 as stc
from pydub import AudioSegment
import io

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
    remarks_list = [""] + [x[1] for x in data_list]
    remarks_select = st.selectbox(
        "備考欄で検索",
        remarks_list
    )
    if remarks_select != "":
        data_list = [x for x in data_list if x[1] == remarks_select]
    for data in data_list:
        remarks, text, audio_path = data[1], data[2], data[3]
        
        # 各データをexpanderで囲む
        with st.expander(f"備考: {remarks}", expanded=True):
            # テキストの表示
            st.write("**内容:**")
            for line in text.split('\n'):
                st.write(line)
            
            # 音声再生ボタン
            if st.button(f"音声を再生", key=f"play_{audio_path}"):
                play_audio(audio_path)

selected_date = st.date_input(
    "日付を選択",
    value=None,
    min_value=None,
    max_value=None,
    format="YYYY/MM/DD"
)

if selected_date:
    search_file_path = f"./pickleData/{selected_date.strftime('%Y%m%d')}.pickle"
    if os.path.exists(search_file_path):
        with open(search_file_path,"rb") as f:
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

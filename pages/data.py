import os
import pickle
import streamlit as st
import streamlit.components.v1 as stc
from pydub import AudioSegment

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

selected_date = st.date_input(
    "日付を選択(録音日)",
    value="today",
    min_value=None,
    max_value=None,
    format="YYYY/MM/DD"
)

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
        print(show_data)
        show_result(show_data)
    else:
        st.write(f"{selected_date}のデータはありません")

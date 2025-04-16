import streamlit as st


def save_custom_prompt(title,text):
    with open(f"save_dir/prompts/{title}.txt","a", encoding="utf-8") as f:
        f.write(text)

st.title("要約指示文の編集ページ")

with open("save_dir/prompts/default.txt","r", encoding="utf-8") as f:
    default_prompt = f.read()

st.subheader("デフォルトの指示文です。")
st.info(default_prompt)

col1,col2 = st.columns([5,1])
with col1:
    st.subheader("カスタム指示文のタイトル、指示内容を入力し保存しておくと、要約時に使用できます。")
with col2:
    if st.button("保存"):
        save_custom_prompt(st.session_state["custom_prompt_title"],st.session_state["custom_prompt_text"])

custom_prompt_title = st.text_area("カスタム指示文のタイトル",key="custom_prompt_title",height=68)
custom_prompt_text = st.text_area("カスタム指示文の内容",key="custom_prompt_text",height=500)       






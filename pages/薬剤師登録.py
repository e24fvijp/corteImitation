import os
import pickle
import streamlit as st

from func.function import Auth

st.set_page_config(
    page_title="薬剤師登録",
    layout="wide",
    initial_sidebar_state="expanded"
)


#ページの翻訳提案をしないように設定
st.markdown(
    '<meta name="google" content="notranslate">', 
    unsafe_allow_html=True
)

# データディレクトリのパスを設定
pharmacist_list_path = "save_dir/pharmacist_list.pickle"


def add_text_inputs(pharmacist_list=None, num_columns=1):
    inputs = []
    
    # 必要な列数を設定
    columns = st.columns(num_columns)
    
    for i in range(10):
        column_index = i % num_columns  # 列のインデックス
        with columns[column_index]:
            try:
                user_input = st.text_input(f"薬剤師 {i+1}", key=f"text_input_{i}", value=pharmacist_list[i])
            except:
                user_input = st.text_input(f"薬剤師 {i+1}", key=f"text_input_{i}")
            inputs.append(user_input)
    
    return inputs

def update_pharmacist_list(pharmacist_list):
    # os.makedirs(os.path.dirname(pharmacist_list_path), exist_ok=True)
    with open(pharmacist_list_path, "wb") as f:
        pickle.dump(pharmacist_list, f)

auth = Auth()

auth.authenticator.login()

#-------------------ログインできているときの処理-------------------
if st.session_state['authentication_status']:
    col1, col2, col3 = st.columns([6, 1, 1])
    with col3:
        auth.authenticator.logout()

    st.title("薬剤師の名前リスト")
    st.write("薬剤師名を追加、変更、削除し画面下の更新ボタンを押してください")

    # 既存データ読み込み
    if os.path.exists(pharmacist_list_path) and os.path.getsize(pharmacist_list_path) > 0:
        with open(pharmacist_list_path, "rb") as f:
            pharmacist_list = pickle.load(f)
    else:
        pharmacist_list = []
        st.write("薬剤師のリストを作成してください。")

    # 入力欄を作成（デフォルトで1列表示、横並びの場合はnum_columnsを指定）
    inputs = add_text_inputs(pharmacist_list, num_columns=2)  # 2列で横並び


    # ボタンで保存
    if st.button("更新"):
        update_pharmacist_list(inputs)
        st.success("薬剤師リストが更新されました！")
    

#-------------------ログインできていない場合-------------------

elif st.session_state["authentication_status"] is False:
    st.error("ユーザー名またはパスワードが正しくありません")
elif st.session_state["authentication_status"] is None:
    st.warning("ユーザー名とパスワードを入力しログインしてください")


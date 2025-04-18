import os
import pickle
import streamlit as st
import streamlit.components.v1 as stc

from func.function import Auth

st.set_page_config(
    page_title="データ",
    layout="wide",
    initial_sidebar_state="expanded"
)

#ページの翻訳提案をしないように設定
st.markdown(
    '<meta name="google" content="notranslate">', 
    unsafe_allow_html=True
)

#cssで余白の設定
st.markdown(
    """
    <style>
    .custom {
        background-color: #87cefa;
        padding: 0px;
        border-radius: 3px;
        font-size: 14px;  /* 小さな文字サイズ */
        text-align:center;
    }
    .action-button {
        padding: 5px 10px;
        margin: 0 5px;
        border: none;
        border-radius: 3px;
        cursor: pointer;
        font-size: 14px;
    }
    .delete-button {
        background-color: #ff4444;
        color: white;
    }
    .complete-button {
        background-color: #4CAF50;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True)


def toggle_completion(item_key):
    search_file_path = f"./save_dir/pickleData/{selected_date.strftime('%Y%m%d')}.pickle"
    with open(search_file_path,"rb") as f:
        result_list = pickle.load(f)
    for i, result in enumerate(result_list):
        time, remarks, recognition_text, summary_text, completed = result[1:6]
        if item_key == f"{time}_{remarks}_{recognition_text}":
            result_list[i][5] = not completed  # 現在の状態を反転
    with open(search_file_path,"wb") as f:
        pickle.dump(result_list,f)

def delete_data(item_key):
    try:
        search_file_path = f"./save_dir/pickleData/{selected_date.strftime('%Y%m%d')}.pickle"
        with open(search_file_path,"rb") as f:
            result_list = pickle.load(f)
        
        # 削除するインデックスを先に特定
        delete_index = None
        for i, result in enumerate(result_list):
            time, remarks, recognition_text, summary_text, completed = result[1:6]
            current_key = f"{time}_{remarks}_{recognition_text}"
            if item_key == current_key:
                delete_index = i
                break
        
        # インデックスが見つかった場合のみ削除
        if delete_index is not None:
            result_list.pop(delete_index)
            with open(search_file_path,"wb") as f:
                pickle.dump(result_list,f)
            return True
        return False
    except Exception as e:
        st.error(f"削除中にエラーが発生しました: {str(e)}")
        return False
    
def generate_string_to_paste(text):
    section_split = {"S":"","O":"","A":"","P":""}
    for line in text.split("\n"):
        section = line.strip()[0]
        section_split[section] += line.split(":")[1].strip() + "\n"
    result_text = ""
    for section in section_split.keys():
        if section_split[section] != "":
            result_text += section_split[section] + "\n"
        else:
            result_text += "\n"
    return result_text


def show_result(data_list):
    # セッションステートの初期化
    if 'delete_confirm' not in st.session_state:
        st.session_state.delete_confirm = None
    if 'checkbox_states' not in st.session_state:
        st.session_state.checkbox_states = {}
    if 'selected_texts_dict' not in st.session_state:
        st.session_state.selected_texts_dict = {}
    if 'checkbox_keys' not in st.session_state:
        st.session_state.checkbox_keys = []
    if 'last_action' not in st.session_state:
        st.session_state.last_action = None
    if 'force_rerun' not in st.session_state:
        st.session_state.force_rerun = False

    # セッション状態のリセット
    if 'reset_checkboxes' not in st.session_state:
        st.session_state.reset_checkboxes = True
        st.session_state.checkbox_states = {}
        st.session_state.selected_texts_dict = {}
        st.session_state.checkbox_keys = []
        st.session_state.last_action = None
        st.session_state.force_rerun = False
        st.session_state.reset_checkboxes = False

    col1, col2 = st.columns([5,1])
    remarks_list = [""] + [x[2] for x in data_list]
    with col1:
        remarks_select = st.selectbox(
            "備考欄で検索",
            remarks_list,
            key="remarks_select"
        )
    with col2:
        completed_hide = st.checkbox("完了済み\n非表示", key="hide_completed")

    # フィルタリング処理
    if remarks_select != "":
        data_list = [x for x in data_list if x[2] == remarks_select]
    if completed_hide:
        data_list = [x for x in data_list if not x[5]]
    
    for i, data in enumerate(data_list[::-1]):
        time, remarks, recognition_text, summary_text, completed = data[1:6]
        item_key = f"{time}_{remarks}_{recognition_text}"
        
        # 各データの選択テキストを初期化
        if item_key not in st.session_state.selected_texts_dict:
            st.session_state.selected_texts_dict[item_key] = []
        
        with st.expander(f"時間: {time}   備考: {remarks}", expanded=True):
            col1, col2 = st.columns([5, 1])
            
            with col1:
                section = ""
                for line in summary_text.split("\n"):
                    if line.strip() != "":
                        for line_sprit in line.strip().split("。"):
                            if ":" in line_sprit:
                                section = line_sprit.split(":")[0]
                            if line_sprit.strip() != "":
                                if ":" not in line_sprit:
                                    checkbox_label = section + ":" + line_sprit.strip()
                                else:
                                    checkbox_label = line_sprit.strip()
                                
                                checkbox_key = f"{item_key}_{checkbox_label.strip()}"
                                
                                # チェックボックスのキーを保存
                                if checkbox_key not in st.session_state.checkbox_keys:
                                    st.session_state.checkbox_keys.append(checkbox_key)
                                
                                # チェックボックスの状態を初期化
                                if checkbox_key not in st.session_state.checkbox_states:
                                    st.session_state.checkbox_states[checkbox_key] = False
                                
                                # チェックボックスの表示と状態更新
                                checkbox_state = st.checkbox(
                                    checkbox_label,
                                    key=checkbox_key,
                                    value=st.session_state.checkbox_states[checkbox_key]
                                )
                                
                                # 状態の更新を即時反映
                                if checkbox_state != st.session_state.checkbox_states[checkbox_key]:
                                    st.session_state.checkbox_states[checkbox_key] = checkbox_state
                                    st.session_state.last_action = checkbox_key
                                    st.session_state.force_rerun = True
                                    if checkbox_state and checkbox_label not in st.session_state.selected_texts_dict[item_key]:
                                        st.session_state.selected_texts_dict[item_key].append(checkbox_label)
                                    elif not checkbox_state and checkbox_label in st.session_state.selected_texts_dict[item_key]:
                                        st.session_state.selected_texts_dict[item_key].remove(checkbox_label)
                                elif checkbox_state and checkbox_label not in st.session_state.selected_texts_dict[item_key]:
                                    st.session_state.selected_texts_dict[item_key].append(checkbox_label)
                
                # 選択されたテキストの表示
                if st.session_state.selected_texts_dict[item_key]:
                    st.markdown("""<div class='custom'>選択したテキスト表示。
                                下のボックスの右上のコピーボタンを押してください。<br>
                                薬歴が空の状態でペーストしてください。</div>"""
                                , unsafe_allow_html=True)
                    code_text = generate_string_to_paste("\n".join(st.session_state.selected_texts_dict[item_key]))
                    st.code(code_text,language="markdown")
            
            with col2:
                # 削除ボタン
                if st.session_state.delete_confirm == item_key:
                    st.warning("本当に削除しますか？")
                    col_confirm, col_cancel = st.columns([1, 1])
                    with col_confirm:
                        if st.button("はい", key=f"confirm_{i}"):
                            if delete_data(item_key):
                                st.success("削除しました")
                                st.session_state.delete_confirm = None
                                st.rerun()
                            else:
                                st.error("削除に失敗しました")
                                st.session_state.delete_confirm = None
                    with col_cancel:
                        if st.button("いいえ", key=f"cancel_{i}"):
                            st.session_state.delete_confirm = None
                            st.rerun()
                else:
                    if st.button("🗑️ 削除", key=f"delete_{i}", type="primary"):
                        st.session_state.delete_confirm = item_key
                        st.rerun()
                
                # 完了ボタン
                if completed:
                    if st.button("✓ 完了済み", key=f"complete_{i}", type="secondary"):
                        toggle_completion(item_key)
                        st.rerun()
                else:
                    if st.button("○ 未完了", key=f"complete_{i}"):
                        toggle_completion(item_key)
                        st.rerun()

            # recognition_textを表示
            if st.checkbox("✨認識テキストを表示✨", key=f"show_recognition_{i}"):
                st.text_area("認識テキスト", recognition_text.replace("\n","   "), height=200, key=f"recognition_{i}")

    # 強制再レンダリング
    if st.session_state.force_rerun:
        st.session_state.force_rerun = False
        st.rerun()

auth = Auth()
auth.authenticator.login()

#-------------------ログインできているときの処理-------------------
if st.session_state['authentication_status']:
    auth.authenticator.logout()

    selected_date = st.date_input(
        "日付を選択(録音日)",
        value="today",
        min_value=None,
        max_value=None,
        format="YYYY/MM/DD"
    )

    if selected_date:
        search_file_path = f"./save_dir/pickleData/{selected_date.strftime('%Y%m%d')}.pickle"
        if os.path.exists(search_file_path):
            with open(search_file_path, "rb") as f:
                data = pickle.load(f)
            if not data:
                st.write(f"{selected_date}のデータはありません")
            else:
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

#-------------------ログインできていない場合-------------------

elif st.session_state["authentication_status"] is False:
    st.error("ユーザー名またはパスワードが正しくありません")
elif st.session_state["authentication_status"] is None:
    st.warning("ユーザー名とパスワードを入力しログインしてください")
import os
import pickle
import streamlit as st
import streamlit.components.v1 as stc

#ページの翻訳提案をしないように設定
st.markdown(
    '<meta name="google" content="notranslate">', 
    unsafe_allow_html=True
)

#cssで余白の設定
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


def toggle_completion(item_key):
    search_file_path = f"./save_dir/pickleData/{selected_date.strftime('%Y%m%d')}.pickle"
    with open(search_file_path,"rb") as f:
        result_list = pickle.load(f)
    for i, result in enumerate(result_list):
        time, remarks, text, completed = result[1], result[2], result[3], result[4]
        if item_key == f"{time}_{remarks}_{text}":
            result_list[i][4] = not completed  # 現在の状態を反転
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
            time, remarks, text, completed = result[1], result[2], result[3], result[4]
            current_key = f"{time}_{remarks}_{text}"
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

def show_result(data_list):
    # セッションステートの初期化
    if 'delete_confirm' not in st.session_state:
        st.session_state.delete_confirm = None
    
    col1, col2 = st.columns([5,1])
    remarks_list = [""] + [x[2] for x in data_list]
    with col1:
        remarks_select = st.selectbox(
            "備考欄で検索",
            remarks_list
        )
    with col2:
        completed_hide = st.checkbox("完了済み\n非表示", key="hide_completed")

    # フィルタリング処理
    if remarks_select != "":
        data_list = [x for x in data_list if x[2] == remarks_select]
    if completed_hide:
        data_list = [x for x in data_list if not x[4]]
    
    for i, data in enumerate(data_list[::-1]):
        time, remarks, text, completed = data[1], data[2], data[3], data[4]
        item_key = f"{time}_{remarks}_{text}"
        
        # 各データをexpanderで囲む
        with st.expander(f"時間: {time}   備考: {remarks}", expanded=True):
            col1, col2 = st.columns([5, 1])
            
            with col1:
                # テキストの表示
                for line in text.split("\n"):
                    if line.strip() != "":
                        for line_sprit in line.strip().split("。"):
                            if line_sprit.strip() != "":
                                write_copyable_text(line_sprit.strip())
            
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
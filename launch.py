import subprocess
import sys
import os

# 現在のスクリプトと同じディレクトリにあるapp.pyを実行
script_path = os.path.join(os.path.dirname(__file__), 'recording.py')

# streamlit run app.py を実行する
subprocess.call([sys.executable, "-m", "streamlit", "run", script_path])

import streamlit as st
import pandas as pd

st.set_page_config(page_title="マイク料金見積シミュレータ", page_icon="🎤")

st.title("🎤 マイク料金見積シミュレータ")
st.write("会場とマイクの本数を選択するだけで、概算料金と明細を即座に算出します。")

# データ読み込み関数（キャッシュ対応）
@st.cache_data
def load_data():
    # Excelファイルを読み込み
    excel_file = 'マイク料金表.xlsx'
    xls = pd.ExcelFile(excel_file)
    sheets = xls.sheet_names
    
    # 全シートを辞書形式で読み込む
    data_dict = {}
    for sheet in sheets:
        data_dict[sheet] = pd.read_excel(excel_file, sheet_name=sheet)
    return data_dict

try:
    data = load_data()
    
    # 会場（シート名）の選択
    venues = list(data.keys())
    selected_venue = st.selectbox("会場を選択してください", venues)
    
    df = data[selected_venue]
    
    st.subheader(f"📍 選択中の会場: {selected_venue}")
    
    # 料金表の表示
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"料金表ファイルの読み込み時にエラーが発生しました: {e}")
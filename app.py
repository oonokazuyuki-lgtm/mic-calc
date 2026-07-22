import streamlit as st
import pandas as pd

st.set_page_config(page_title="マイク料金見積シミュレータ", page_icon="🎤")

st.title("🎤 マイク料金見積シミュレータ")
st.write("会場とマイクの本数を選択するだけで、概算料金と明細を即座に算出します。")

# データ読み込み関数
@st.cache_data
def load_data():
    excel_file = 'マイク料金表.xlsx'
    xls = pd.ExcelFile(excel_file)
    sheets = xls.sheet_names
    
    data_dict = {}
    for sheet in sheets:
        data_dict[sheet] = pd.read_excel(excel_file, sheet_name=sheet)
    return data_dict

try:
    data = load_data()
    
    # 1. 会場の選択
    venues = list(data.keys())
    selected_venue = st.selectbox("📍 会場を選択してください", venues)
    
    df = data[selected_venue]
    
    st.subheader(f"🏢 選択中: {selected_venue}")
    
    # 2. マイク本数の入力フォーム
    st.markdown("---")
    st.subheader("🎤 マイクの本数を指定してください")
    
    # 料金や本数を計算するための準備
    total_price = 0
    details = []
    
    # Excelの各行（マイクの種類）ごとに数量選択を作る
    for index, row in df.iterrows():
        # 列名の揺れに対応（「マイク種類」「品名」など／「単価」「料金」など）
        mic_name = row.iloc[0]  # 1列目を品名とみなす
        price = row.iloc[1]     # 2列目を単価とみなす
        
        # 数量入力（0〜10本など）
        qty = st.number_input(f"{mic_name} (単価: {price:,}円)", min_value=0, max_value=20, value=0, key=f"mic_{index}")
        
        if qty > 0:
            subtotal = price * qty
            total_price += subtotal
            details.append({"マイク種類": mic_name, "単価": price, "数量": qty, "小計": subtotal})
            
    # 3. 見積結果の表示
    st.markdown("---")
    st.subheader("💰 見積結果")
    
    if details:
        details_df = pd.DataFrame(details)
        st.table(details_df)
        st.markdown(f"### **合計金額: {total_price:,} 円**")
    else:
        st.info("マイクの本数を1本以上指定すると、ここに合計金額が表示されます。")

except Exception as e:
    st.error(f"エラーが発生しました: {e}")
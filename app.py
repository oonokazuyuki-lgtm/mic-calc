import streamlit as st
import pandas as pd

st.set_page_config(page_title="マイク料金見積シミュレータ", page_icon="🎤", layout="wide")

st.title("🎤 マイク料金見積シミュレータ")
st.write("会場とご希望のマイク本数を入力すると、最適なプランの概算料金と内訳を算出します。")

# データ読み込み
@st.cache_data
def load_data():
    excel_file = 'マイク料金表.xlsx'
    xls = pd.ExcelFile(excel_file)
    data_dict = {}
    for sheet in xls.sheet_names:
        df = pd.read_excel(excel_file, sheet_name=sheet)
        # NaN（空欄）を0に置き換え
        df = df.fillna(0)
        data_dict[sheet] = df
    return data_dict

try:
    data = load_data()
    
    # 1. 会場選択
    venues = list(data.keys())
    selected_venue = st.selectbox("📍 会場を選択してください", venues)
    
    df = data[selected_venue]
    
    st.markdown("---")
    st.subheader("🎤 ご希望のマイク本数を指定してください")
    
    col1, col2, col3 = st.columns(3)
    
    # シートごとの存在する列名に合わせて本数入力を表示
    with col1:
        req_wired = st.number_input("有線マイク (本)", min_value=0, max_value=10, value=1)
    with col2:
        req_wireless = st.number_input("ワイヤレスマイク (本)", min_value=0, max_value=10, value=2)
    with col3:
        req_pin = st.number_input("ピンマイク (本)", min_value=0, max_value=10, value=0)
        
    st.markdown("---")
    
    # 該当する行を検索
    # 合計本数または各列の合計値と一致するものを検索
    matched = pd.DataFrame()
    
    # パケット内の本数判定列を探す
    wired_col = [c for c in df.columns if '有線' in str(c) and ('合計' in str(c) or '基本' in str(c))]
    wireless_col = [c for c in df.columns if 'ワイ合計' in str(c)]
    pin_col = [c for c in df.columns if 'ピン合計' in str(c)]
    
    # 検索条件の作成
    cond = pd.Series([True] * len(df))
    if wireless_col:
        cond = cond & (df[wireless_col[0]] == req_wireless)
    if pin_col:
        cond = cond & (df[pin_col[0]] == req_pin)
        
    matched = df[cond]
    
    st.subheader("💰 見積・内訳結果")
    
    if not matched.empty:
        # 一番最初に見つかった適合プランを表示
        row = matched.iloc[0]
        
        total_price = row['合計'] if '合計' in row else 0
        
        st.success(f"### **概算合計金額: {int(total_price):,} 円**")
        
        if '連絡' in row and row['連絡'] == '〇':
            st.warning("⚠️ この構成は音響オペレーターまたは追加機器の調整が必要です（連絡要）。")
            
        st.write("#### 📋 料金内訳明細")
        
        # 明細テーブルの作成 (金額が0でない項目だけ抽出)
        detail_data = []
        for col in df.columns:
            val = row[col]
            if isinstance(val, (int, float)) and val > 0 and col not in ['ワイ合計', 'ピン合計', '有線合計']:
                # 料金列か数量列かを判定
                if '料金' in col or 'ミキサー' in col or 'オペレーター' in col or '追加' in col or '仮設' in col or col == '合計':
                    if col != '合計':
                        detail_data.append({"項目名": col, "内容 / 金額": f"{int(val):,} 円"})
                else:
                    detail_data.append({"項目名": col, "内容 / 金額": f"{int(val)} 本"})
                    
        if detail_data:
            st.table(pd.DataFrame(detail_data))
            
    else:
        st.error("指定されたマイク本数の組み合わせに該当するプランが見つかりませんでした。本数を調整してください。")
        
    # 参考：全パターン料金表の表示
    with st.expander("📄 この会場の全パターン料金表を確認する"):
        st.dataframe(df)

except Exception as e:
    st.error(f"エラーが発生しました: {e}")
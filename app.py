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

# 安全に整数に変換するヘルパー関数
def safe_int(val):
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return 0

# 安全にカンマ区切りの金額文字列を作るヘルパー関数
def format_price(val):
    try:
        num = float(val)
        return f"{int(num):,} 円"
    except (ValueError, TypeError):
        return str(val)

try:
    data = load_data()
    
    # 1. 会場選択
    venues = list(data.keys())
    selected_venue = st.selectbox("📍 会場を選択してください", venues)
    
    df = data[selected_venue]
    
    st.markdown("---")
    st.subheader("🎤 ご希望のマイク本数を指定してください")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        req_wired = st.number_input("有線マイク (本)", min_value=0, max_value=10, value=1, key="wired")
    with col2:
        req_wireless = st.number_input("ワイヤレスマイク (本)", min_value=0, max_value=10, value=2, key="wireless")
    with col3:
        req_pin = st.number_input("ピンマイク (本)", min_value=0, max_value=10, value=0, key="pin")
        
    st.markdown("---")
    
    # 列名の特定
    wireless_col = [c for c in df.columns if 'ワイ合計' in str(c)]
    pin_col = [c for c in df.columns if 'ピン合計' in str(c)]
    
    # 検索条件の作成
    cond = pd.Series([True] * len(df))
    if wireless_col:
        cond = cond & (df[wireless_col[0]].apply(safe_int) == req_wireless)
    if pin_col:
        cond = cond & (df[pin_col[0]].apply(safe_int) == req_pin)
        
    matched = df[cond]
    
    st.subheader("💰 見積・内訳結果")
    
    if not matched.empty:
        # 適合する最初のプランを取得
        row = matched.iloc[0]
        
        total_price = safe_int(row['合計']) if '合計' in row else 0
        
        st.success(f"### **概算合計金額: {total_price:,} 円**")
        
        if '連絡' in row and str(row['連絡']).strip() in ['〇', '○', '1']:
            st.warning("⚠️ この構成は音響オペレーターまたは追加機器の調整が必要です（連絡要）。")
            
        st.write("#### 📋 料金内訳明細")
        
        # 明細テーブルの作成
        detail_data = []
        for col in df.columns:
            # 重複する列名（例: 追加ワイヤレスマイク.1 など）の表示をきれいに整形
            clean_col_name = str(col).split('.')[0]
            val = row[col]
            
            # 0や空文字以外を表示
            if val != 0 and str(val).strip() != '0' and str(val).strip() != '':
                if clean_col_name in ['ワイ合計', 'ピン合計', '有線合計']:
                    continue
                
                # 数値の場合と文字列の場合で安全に表示を分ける
                num_val = safe_int(val)
                if num_val > 0:
                    if any(k in clean_col_name for k in ['料金', 'ミキサー', 'オペレーター', '追加', '仮設', '合計']):
                        if clean_col_name != '合計':
                            detail_data.append({"項目名": clean_col_name, "内容 / 金額": f"{num_val:,} 円"})
                    else:
                        detail_data.append({"項目名": clean_col_name, "内容 / 金額": f"{num_val} 本"})
                elif isinstance(val, str) and val.strip() not in ['0', '〇', '○']:
                    detail_data.append({"項目名": clean_col_name, "内容 / 金額": val})
                    
        if detail_data:
            st.table(pd.DataFrame(detail_data))
            
    else:
        st.error("指定されたマイク本数の組み合わせに該当するプランが見つかりませんでした。本数を調整してください。")
        
    # 参考：全パターン料金表の表示
    with st.expander("📄 この会場の全パターン料金表を確認する"):
        st.dataframe(df)

except Exception as e:
    st.error(f"エラーが発生しました: {e}")
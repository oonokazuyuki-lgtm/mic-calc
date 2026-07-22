import streamlit as st
import pandas as pd

# ページの基本設定
st.set_page_config(page_title="マイク料金見積シミュレーター", page_icon="🎤", layout="centered")

st.title("🎤 マイク料金見積シミュレーター")
st.caption("会場とマイクの本数を選択するだけで、概算料金と明細を即座に算出します。")

# エクセルファイルの読み込み
excel_path = 'マイク料金表.xlsx'

@st.cache_data
def load_data(path):
    xls = pd.ExcelFile(path)
    return xls, xls.sheet_names

try:
    xls, sheets = load_data(excel_path)
    
    # 1. 会場選択
    venue = st.selectbox("■ 会場を選択してください", sheets, index=0)
    
    st.markdown("---")
    st.subheader("■ マイク本数の指定")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        # パビリオンの場合のみ有線マイクを選択可能
        if venue == 'パビリオン':
            wired_count = st.number_input("有線マイク (本)", min_value=1, max_value=6, value=1)
        else:
            wired_count = 0
            st.caption("※有線マイク設定なし")
            
    with c2:
        wl_count = st.number_input("ワイヤレス (本)", min_value=0, max_value=10, value=2)
    with c3:
        pin_count = st.number_input("ピンマイク (本)", min_value=0, max_value=10, value=0)

    st.markdown("---")

    # 2. 判定ロジック
    df = pd.read_excel(excel_path, sheet_name=venue)
    cond = pd.Series(True, index=df.index)
    
    if venue == 'パビリオン' and '有線合計' in df.columns:
        cond &= (df['有線合計'].fillna(0) == wired_count)
    if 'ワイ合計' in df.columns:
        cond &= (df['ワイ合計'].fillna(0) == wl_count)
    if 'ピン合計' in df.columns:
        cond &= (df['ピン合計'].fillna(0) == pin_count)
        
    result = df[cond]

    if result.empty:
        st.warning("⚠️ 指定された本数条件に一致するプランが見つかりませんでした。本数を変更してお試しください。")
    else:
        for idx, row in result.iterrows():
            contact_flag = str(row.get('連絡', '')).strip() == '〇'
            
            # 連絡要メッセージ
            if contact_flag:
                st.error("【⚠️ ご連絡・事前確認が必要なプランです】\n\n事前の機材手配およびオペレーター準備が必要となるため、あらかじめご連絡いただけますようお願いいたします。")

            # 合計金額の大きな表示
            total_price = row['合計']
            st.metric(label=f"【{venue}】 ご利用合計金額（税込）", value=f"￥{total_price:,.0f}")
            
            # 明細表示
            st.markdown("### 📋 料金内訳明細")
            
            # 1. 基本料金
            base_price = row.get('基本料金', 0)
            if pd.isna(base_price): base_price = 0
            st.write(f"**【基本セット料金】**: ￥{base_price:,.0f}")
            
            base_wired = int(row.get('基本有線マイク', 0)) if pd.notna(row.get('基本有線マイク')) else 0
            base_wl = int(row.get('基本ワイヤレスマイク', 0)) if pd.notna(row.get('基本ワイヤレスマイク')) else 0
            base_pin = int(row.get('基本ピンマイク', 0)) if pd.notna(row.get('基本ピンマイク')) else 0
            
            if base_wired > 0: st.caption(f"・(付属) 基本有線マイク: {base_wired}本 (基本料金内)")
            if base_wl > 0: st.caption(f"・(付属) 基本ワイヤレスマイク: {base_wl}本 (基本料金内)")
            if base_pin > 0: st.caption(f"・(付属) 基本ピンマイク: {base_pin}本 (基本料金内)")
            if venue == 'ボールルーム':
                st.caption("・(付属) 基本オペレーター人件費: 1名分 (基本料金内 ※ワンマン対応)")

            st.write("---")

            # 2. オペレーター・人件費
            operator = row.get('オペレーター', 0) if pd.notna(row.get('オペレーター')) and str(row.get('オペレーター')).replace('.','').isdigit() else 0
            if float(operator) > 0:
                if venue == 'ボールルーム':
                    st.write(f"**【追加オペレーター人件費 (2人目手配分)】**: ￥{float(operator):,.0f}")
                    st.caption("※ワンマン対応（1名）で対応しきれない大規模・複雑構成のためオペレーターを追加しています。")
                else:
                    st.write(f"**【音響オペレーター技術料】**: ￥{float(operator):,.0f}")
            else:
                if venue == 'ボールルーム':
                    st.caption("・追加人件費なし (基本料金内のオペレーター1名で対応可能)")

except Exception as e:
    st.error(f"料金表ファイルの読み込み時にエラーが発生しました: {e}")
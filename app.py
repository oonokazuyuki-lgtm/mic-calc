import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- ページ設定 ---
st.set_page_config(page_title="マイク料金計算ツール", layout="centered")

st.title("🎤 マイク料金計算ツール")

# --- Excelファイルの読み込み ---
@st.cache_data
def load_data():
    # 同一フォルダ内のExcelファイルを読み込む
    df = pd.read_excel("マイク料金表.xlsx")
    return df

try:
    df = load_data()
    
    # --- 画面入力項目 ---
    st.header("📋 条件の選択")
    
    # マイク種類の選択
    mic_types = df["マイク種類"].unique()
    selected_mic = st.selectbox("マイクの種類を選択してください", mic_types)
    
    # 利用日数の入力
    days = st.number_input("利用日数（日）", min_value=1, value=1, step=1)
    
    # 数量の入力
    quantity = st.number_input("数量（本）", min_value=1, value=1, step=1)
    
    # --- 料金計算 logic ---
    selected_row = df[df["マイク種類"] == selected_mic].iloc[0]
    unit_price = selected_row["日額単価"]
    
    total_price = unit_price * days * quantity
    
    # --- 結果表示 ---
    st.markdown("---")
    st.header("💰 計算結果")
    st.metric(label="単価（日額）", value=f"{unit_price:,} 円")
    st.subheader(f"合計金額: **{total_price:,} 円** (税別)")
    
    # --- スプレッドシートへの保存処理 ---
    st.markdown("---")
    st.header("💾 履歴の保存")
    
    if st.button("この見積を履歴に保存"):
        try:
            # Secretsから認証情報を取得
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            creds = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=scopes
            )
            client = gspread.authorize(creds)
            
            # スプレッドシートを開く
            spreadsheet_name = st.secrets.get("SPREADSHEET_NAME", "見積履歴")
            sheet = client.open(spreadsheet_name).sheet1
            
            # 追加するデータ（日時, マイク種類, 日数, 数量, 単価, 合計金額）
            import datetime
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_row = [now, selected_mic, days, quantity, unit_price, total_price]
            
            # 行の追加
            sheet.append_row(new_row)
            st.success("✅ スプレッドシートに見積履歴を保存しました！")
            
        except Exception as e:
            st.error(f"⚠️ 保存に失敗しました: {e}")

except Exception as e:
    st.error(f"エラーが発生しました: {e}")
    st.info("※『マイク料金表.xlsx』が同じフォルダ内にアップロードされているか確認してください。")

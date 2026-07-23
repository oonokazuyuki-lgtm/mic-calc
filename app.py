import streamlit as st
import pandas as pd
import math
import datetime
import os
import unicodedata

st.set_page_config(page_title="マイク料金見積シミュレータ", page_icon="🎤", layout="wide")

st.title("🎤 マイク料金見積シミュレータ")
st.write("会場・宴席情報・利用時間・ご希望のマイク本数を入力すると、最適なプランの概算料金と内訳を算出します。")

# 備考欄などのテーブルセルを折り返さず1行にするCSS
st.markdown("""
<style>
    /* Streamlitのテーブルセル全般で折り返しを禁止し1行表示にする */
    div[data-testid="stTable"] td, div[data-testid="stTable"] th {
        white-space: nowrap !important;
    }
</style>
""", unsafe_allow_html=True)

# 履歴保存用のCSVファイルパス
HISTORY_FILE = "estimates_history.csv"

# 履歴データを読み込む関数
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            return pd.read_csv(HISTORY_FILE)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

# 履歴データを保存する関数
def save_history(record):
    df_hist = load_history()
    new_df = pd.DataFrame([record])
    if df_hist.empty:
        df_hist = new_df
    else:
        df_hist = pd.concat([df_hist, new_df], ignore_index=True)
    df_hist.to_csv(HISTORY_FILE, index=False, encoding="utf-8-sig")

# 特定の履歴を削除する関数（保存日時で一致判定）
def delete_history_by_timestamp(timestamp):
    df_hist = load_history()
    if not df_hist.empty and "保存日時" in df_hist.columns:
        df_hist = df_hist[df_hist["保存日時"] != timestamp]
        df_hist.to_csv(HISTORY_FILE, index=False, encoding="utf-8-sig")

# 全角・半角・大文字・小文字を揃えて正規化する関数
def normalize_text(text):
    if not isinstance(text, str):
        text = str(text) if text is not None else ""
    return unicodedata.normalize('NFKC', text).lower()

# データ読み込みおよび会場名の置換マップ定義
NAME_MAPPING = {
    "ボールルーム": "シャングリ・ラボールルーム",
    "コンウェイ1・2・3": "コンウェイルーム（各Ⅰ・Ⅱ・Ⅲ）",
    "コンウェイルーム": "コンウェイルーム（Ⅱ＆Ⅲ）",
    "パビリオン": "ザ・パビリオン"
}

@st.cache_data
def load_data():
    excel_file = 'マイク料金表.xlsx'
    xls = pd.ExcelFile(excel_file)
    data_dict = {}
    for sheet in xls.sheet_names:
        display_name = NAME_MAPPING.get(sheet, sheet)
        df = pd.read_excel(excel_file, sheet_name=sheet)
        df = df.fillna(0)
        data_dict[display_name] = df
    return data_dict

def safe_int(val):
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return 0

try:
    data = load_data()
    venues = list(data.keys())

    # --- 📜 過去ログ読み込み＆全角半角あいまい検索・削除エリア ---
    st.markdown("### 📜 過去の見積履歴")
    df_history = load_history()

    # セッション状態の初期化
    if "loaded_data" not in st.session_state:
        st.session_state["loaded_data"] = None

    if not df_history.empty:
        col_s1, col_s2 = st.columns([1, 2])
        with col_s1:
            search_query = st.text_input(
                "🔍 履歴検索（宴席名・担当者名・日付・会場など）", 
                value="", 
                placeholder="例: 「 Party 」「 Tanaka 」「 ＡＢＣ 」「 23 」など"
            )
            
        # 全角半角・大文字小文字を吸収したフィルタリング
        filtered_df = df_history.copy()
        
        # 検索キーワードがある場合は「全データ」から絞り込み
        if search_query.strip():
            q = normalize_text(search_query.strip())
            mask = (
                filtered_df["宴席名"].apply(normalize_text).str.contains(q, regex=False) |
                filtered_df["担当者名"].fillna("").apply(normalize_text).str.contains(q, regex=False) |
                filtered_df["利用日付"].apply(normalize_text).str.contains(q, regex=False) |
                filtered_df["会場名"].apply(normalize_text).str.contains(q, regex=False) |
                filtered_df["保存日時"].apply(normalize_text).str.contains(q, regex=False)
            )
            filtered_df = filtered_df[mask]
            label_prefix = f"（検索結果: {len(filtered_df)}件）"
        else:
            # 未検索時は「直近20件」のみに絞り込む（最新順）
            filtered_df = filtered_df.tail(20)
            label_prefix = f"（直近{len(filtered_df)}件を表示中）"

        with col_s2:
            if not filtered_df.empty:
                # ドロップダウン用のラベル作成（新しい順）
                history_options = ["（選択してください）"] + [
                    f"【{row['利用日付']}】{row['宴席名']} / 担当:{row.get('担当者名', '未入力')}（会場: {row['会場名']} / 保存: {row['保存日時']}）"
                    for _, row in filtered_df.iloc[::-1].iterrows()
                ]
                selected_hist = st.selectbox(f"検索結果から呼び出す {label_prefix}:", history_options)
                
                if selected_hist != "（選択してください）":
                    selected_idx = history_options.index(selected_hist) - 1
                    target_row = filtered_df.iloc[::-1].iloc[selected_idx]
                    
                    col_btn1, col_btn2 = st.columns([2, 1])
                    with col_btn1:
                        if st.button("📋 このデータをフォームに呼び出す", use_container_width=True):
                            st.session_state["loaded_data"] = target_row.to_dict()
                            st.success(f"「{target_row['宴席名']}」の見積データを呼び出しました。下のフォームに反映されています。")
                    with col_btn2:
                        # 🗑️ 削除ボタン
                        if st.button("🗑️ 選択中の履歴を削除", type="secondary", use_container_width=True):
                            delete_history_by_timestamp(target_row["保存日時"])
                            st.session_state["loaded_data"] = None
                            st.toast("🗑️ 履歴を1件削除しました！", icon="🧹")
                            st.rerun()
            else:
                st.warning("⚠️ 該当する見積履歴が見つかりませんでした。文字や数字を変えてお試しください。")
    else:
        st.caption("※まだ保存された過去の履歴はありません。")

    st.markdown("---")

    # 呼び出しデータの準備
    loaded = st.session_state.get("loaded_data", {}) or {}

    # 0. 宴席情報・基本情報の入力（上部）
    st.subheader("📝 宴席情報・基本情報")
    col_info1, col_info2 = st.columns(2)
    with col_info1:
        default_banquet = loaded.get("宴席名", "")
        banquet_name = st.text_input("宴席名（手入力）", value=default_banquet, placeholder="例：〇〇株式会社 様 ご利用")
        
        default_staff = loaded.get("担当者名", "")
        staff_name = st.text_input("担当者名（アルファベット手入力）", value=default_staff, placeholder="例：Tanaka / John Smith")

    with col_info2:
        default_date = datetime.datetime.strptime(loaded["利用日付"], "%Y-%m-%d").date() if "利用日付" in loaded else datetime.date.today()
        event_date = st.date_input("利用日付", value=default_date)
        
    st.markdown("---")
    
    # 1. 会場選択
    default_venue_idx = venues.index(loaded["会場名"]) if "会場名" in loaded and loaded["会場名"] in venues else 0
    selected_venue = st.selectbox("📍 会場を選択してください", venues, index=default_venue_idx)
    
    df = data[selected_venue]
    
    # デフォルトマイク本数
    first_row = df.iloc[0]
    def get_base_qty(col_keyword):
        col = next((c for c in df.columns if col_keyword in str(c)), None)
        return safe_int(first_row[col]) if col else 0

    default_wired = loaded.get("有線マイク本数", max(1, get_base_qty("基本有線")))
    default_wireless = loaded.get("ワイヤレスマイク本数", get_base_qty("基本ワイヤレス"))
    default_pin = loaded.get("ピンマイク本数", get_base_qty("基本ピン"))

    st.markdown("---")
    
    # 2. 利用時間選択（30分単位）
    st.subheader("⏰ ご利用時間を指定してください（幹事来館〜終了）")
    
    time_options = []
    for h in range(7, 24):
        time_options.append(f"{h:02d}:00")
        if h < 23:
            time_options.append(f"{h:02d}:30")
    
    start_idx = time_options.index(loaded["開始時間"]) if "開始時間" in loaded and loaded["開始時間"] in time_options else 2
    end_idx = time_options.index(loaded["終了時間"]) if "終了時間" in loaded and loaded["終了時間"] in time_options else 14

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        start_time_str = st.selectbox("幹事来館時間", time_options, index=start_idx, key="start_time")
    with col_t2:
        end_time_str = st.selectbox("終了時間", time_options, index=end_idx, key="end_time")
        
    start_h, start_m = map(int, start_time_str.split(":"))
    end_h, end_m = map(int, end_time_str.split(":"))
    
    start_val = start_h + start_m / 60.0
    end_val = end_h + end_m / 60.0
    
    use_hours = end_val - start_val
    
    if use_hours <= 0:
        st.warning("⚠️ 終了時間は開始時間より後の時間を選択してください。")
        use_hours = 0
        extension_hours = 0
    else:
        st.info(f"💡 利用予定時間: **{use_hours:.1f} 時間**")
        raw_extension_hours = max(0.0, use_hours - 6.0)
        extension_hours = math.ceil(raw_extension_hours)
    
    st.markdown("---")
    
    # 3. マイク本数指定
    st.subheader("🎤 ご希望のマイク本数を指定してください")
    st.caption("※基本料金に含まれるマイク本数も含めた「全体の必要本数」をご指定ください。")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        req_wired = st.number_input("有線マイク (本)", min_value=1, max_value=10, value=safe_int(default_wired), key=f"wired_{selected_venue}")
    with col2:
        req_wireless = st.number_input("ワイヤレスマイク (本)", min_value=0, max_value=10, value=safe_int(default_wireless), key=f"wireless_{selected_venue}")
    with col3:
        req_pin = st.number_input("ピンマイク (本)", min_value=0, max_value=10, value=safe_int(default_pin), key=f"pin_{selected_venue}")
        
    st.markdown("---")
    
    # 検索処理
    wireless_col = next((c for c in df.columns if 'ワイ合計' in str(c)), None)
    pin_col = next((c for c in df.columns if 'ピン合計' in str(c)), None)
    wired_col = next((c for c in df.columns if '有線合計' in str(c)), None)
    if not wired_col:
        wired_col = next((c for c in df.columns if '基本有線' in str(c)), None)
    
    cond = pd.Series([True] * len(df))
    if wireless_col:
        cond = cond & (df[wireless_col].apply(safe_int) == req_wireless)
    if pin_col:
        cond = cond & (df[pin_col].apply(safe_int) == req_pin)
    if wired_col:
        cond = cond & (df[wired_col].apply(safe_int) == req_wired)
        
    matched = df[cond]
    
    st.subheader("💰 見積・内訳結果")
    
    if not matched.empty:
        row = matched.iloc[0]
        raw_total_price = safe_int(row['合計']) if '合計' in row else 0
        
        op_col = next((c for c in df.columns if 'オペレーター' in str(c)), None)
        op_price = safe_int(row[op_col]) if op_col else 0
        
        is_ballroom = ("ボールルーム" in selected_venue)
        base_ext_unit_price = 15000 if is_ballroom else 3000
        base_ext_price = extension_hours * base_ext_unit_price
        
        op_ext_unit_price = 15000
        op_ext_price = extension_hours * op_ext_unit_price if op_price > 0 else 0
        
        calc_total_price = (raw_total_price - op_price) + base_ext_price
        
        col_res1, col_res2 = st.columns([3, 1])
        with col_res1:
            if op_price > 0:
                st.success(f"### **概算合計金額: {calc_total_price:,} 円** (※オペレーター料金除く)")
            else:
                st.success(f"### **概算合計金額: {calc_total_price:,} 円**")
        with col_res2:
            # 💾 履歴保存ボタン
            if st.button("💾 この見積を履歴に保存", use_container_width=True):
                record = {
                    "保存日時": datetime.datetime.now().strftime("%Y/%m/%d %H:%M"),
                    "宴席名": banquet_name if banquet_name.strip() else "（未入力）",
                    "担当者名": staff_name if staff_name.strip() else "（未入力）",
                    "利用日付": event_date.strftime("%Y-%m-%d"),
                    "会場名": selected_venue,
                    "開始時間": start_time_str,
                    "終了時間": end_time_str,
                    "有線マイク本数": req_wired,
                    "ワイヤレスマイク本数": req_wireless,
                    "ピンマイク本数": req_pin,
                    "概算合計金額": calc_total_price
                }
                save_history(record)
                st.toast("✅ 見積履歴に保存しました！", icon="🎉")
                st.rerun()

        if '連絡' in row and str(row['連絡']).strip() in ['〇', '○', '1']:
            if op_price > 0:
                st.warning("⚠️ この構成は音響オペレーターまたは追加機器の調整が必要です（連絡要）。")
            else:
                st.warning("⚠️ この構成は追加機器の調整が必要です（連絡要）。")
            
        display_banquet_name = banquet_name if banquet_name.strip() else "（未入力）"
        display_staff_name = staff_name if staff_name.strip() else "（未入力）"
        formatted_date = event_date.strftime("%Y年%m月%d日")
        
        st.info(f"📌 **宴席・基本情報**\n\n"
                f"- **宴席名:** {display_banquet_name}\n"
                f"- **担当者名:** {display_staff_name}\n"
                f"- **利用日付:** {formatted_date}\n"
                f"- **会場名:** {selected_venue}\n"
                f"- **ご利用時間:** {start_time_str} 〜 {end_time_str} （{use_hours:.1f}時間）")

        st.write("#### 📋 料金内訳明細")
        
        detail_table = []
        cols = list(df.columns)
        base_price_idx = next((i for i, c in enumerate(cols) if '基本料金' in str(c)), -1)
        
        if base_price_idx != -1:
            base_price = safe_int(row[cols[base_price_idx]])
            if base_price > 0:
                base_info = []
                for idx in range(0, base_price_idx):
                    c_name = str(cols[idx]).split('.')[0]
                    c_qty = safe_int(row[cols[idx]])
                    if '基本' in c_name and c_qty > 0:
                        base_info.append(f"{c_name}:{c_qty}本")
                
                info_str = f"{', '.join(base_info)}込" if base_info else ""
                detail_table.append({
                    "項目名": "基本料金",
                    "備考": f"6時間まで ({info_str})" if info_str else "6時間まで",
                    "数量": "1 式",
                    "単価": f"{base_price:,} 円",
                    "小計": f"{base_price:,} 円"
                })
            
            if extension_hours > 0:
                detail_table.append({
                    "項目名": "会場基本料金 延長",
                    "備考": f"6時間超え分 (繰り上げ算定: {extension_hours}時間)",
                    "数量": f"{extension_hours} 時間",
                    "単価": f"{base_ext_unit_price:,} 円",
                    "小計": f"{base_ext_price:,} 円"
                })
            
            for idx in range(base_price_idx + 1, len(cols)):
                col_name = str(cols[idx])
                clean_name = col_name.split('.')[0]
                
                if clean_name in ['合計', '連絡', 'ワイ合計', 'ピン合計', '有線合計']:
                    continue
                    
                subtotal = safe_int(row[col_name])
                if subtotal > 0:
                    qty = 1
                    unit_str = "式"
                    matching_qty_cols = [c for c in cols[:base_price_idx] if str(c).split('.')[0] == clean_name]
                    if matching_qty_cols:
                        found_qty = safe_int(row[matching_qty_cols[0]])
                        if found_qty > 0:
                            qty = found_qty
                            unit_str = "本"
                        else:
                            qty = 1
                            unit_str = "式"
                    elif 'オペレーター' in clean_name:
                        unit_str = "名"
                    
                    unit_price = subtotal // qty if qty > 0 else subtotal
                    
                    note = "-"
                    if 'デジタルミキサー' in clean_name:
                        if subtotal == 60000:
                            note = "ピンマイク3本以上で必要となります"
                        elif subtotal == 40000:
                            note = "小部屋でピンマイクが入った時、マイクの本数が多い時必要となります。"
                        else:
                            note = "小部屋でピンマイクが入った時、マイクの本数が多い時必要となります。"
                    elif is_ballroom:
                        if '追加' in clean_name:
                            note = "ワイヤレス（ハンド・ピン）4本以下使用の為"
                        elif '仮設' in clean_name:
                            note = "ワイヤレス（ハンド・ピン）5本以上使用の為"
                    
                    if 'オペレーター' in clean_name:
                        detail_table.append({
                            "項目名": clean_name,
                            "備考": "6時間まで (※参考価格/要確認)",
                            "数量": f"{qty} {unit_str}",
                            "単価": f"{unit_price:,} 円",
                            "小計": f"{subtotal:,} 円"
                        })
                        if extension_hours > 0:
                            detail_table.append({
                                "項目名": "オペレーター 延長",
                                "備考": f"6時間超え分 (繰り上げ算定: {extension_hours}時間 / ※参考価格/要確認)",
                                "数量": f"{extension_hours} 時間",
                                "単価": f"{op_ext_unit_price:,} 円",
                                "小計": f"{op_ext_price:,} 円"
                            })
                    else:
                        detail_table.append({
                            "項目名": clean_name,
                            "備考": note,
                            "数量": f"{qty} {unit_str}",
                            "単価": f"{unit_price:,} 円",
                            "小計": f"{subtotal:,} 円"
                        })
                        
        if detail_table:
            st.table(pd.DataFrame(detail_table))

        st.markdown("---")

        # 📄 PDF印刷機能
        with st.expander("🖨️ PDF保存・印刷用のページを表示（保存ボタン）", expanded=False):
            st.caption("※下の「ブラウザの印刷機能を開く」ボタンを押すと、内訳とサマリーのみのレイアウトでPDF保存・印刷が可能です。")
            df_detail = pd.DataFrame(detail_table)
            table_html = df_detail.to_html(index=False, classes='print-table')

            print_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: sans-serif; padding: 20px; color: #333; }}
                    h2 {{ border-bottom: 2px solid #333; padding-bottom: 5px; }}
                    .summary {{ background: #f8f9fa; border: 1px solid #ddd; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                    .summary p {{ margin: 5px 0; font-size: 14px; }}
                    .price-box {{ font-size: 20px; font-weight: bold; color: #1a5276; margin: 15px 0; }}
                    table.print-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                    table.print-table th, table.print-table td {{ border: 1px solid #ccc; padding: 8px 12px; text-align: left; font-size: 13px; white-space: nowrap; }}
                    table.print-table th {{ background-color: #f2f2f2; }}
                    @media print {{
                        .no-print {{ display: none; }}
                    }}
                </style>
            </head>
            <body>
                <h2>🎤 音響マイク機材 見積・内訳明細書</h2>
                <div class="summary">
                    <p><strong>宴席名:</strong> {display_banquet_name}</p>
                    <p><strong>担当者名:</strong> {display_staff_name}</p>
                    <p><strong>利用日付:</strong> {formatted_date}</p>
                    <p><strong>会場名:</strong> {selected_venue}</p>
                    <p><strong>ご利用時間:</strong> {start_time_str} 〜 {end_time_str} （{use_hours:.1f}時間）</p>
                </div>
                <div class="price-box">
                    概算合計金額: {calc_total_price:,} 円 {"(※オペレーター料金除く)" if op_price > 0 else ""}
                </div>
                <h3>📋 料金内訳明細</h3>
                {table_html}
                <br><br>
                <button class="no-print" onclick="window.print()" style="padding: 10px 20px; font-size: 16px; cursor: pointer; background: #007bff; color: white; border: none; border-radius: 5px;">
                    🖨️ PDF保存 / 印刷ウィンドウを開く (Ctrl+P)
                </button>
            </body>
            </html>
            """
            st.components.v1.html(print_html, height=500, scrolling=True)

    else:
        st.error("指定されたマイク本数の組み合わせに該当するプランが見つかりませんでした。本数を調整してください。")
        
    with st.expander("📄 この会場の全パターン料金表を確認する"):
        st.dataframe(df)

except Exception as e:
    st.error(f"エラーが発生しました: {e}")
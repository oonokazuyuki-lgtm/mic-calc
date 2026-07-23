import streamlit as st
import pandas as pd
import math
import datetime

st.set_page_config(page_title="マイク料金見積シミュレータ", page_icon="🎤", layout="wide")

st.title("🎤 マイク料金見積シミュレータ")
st.write("会場・宴席情報・利用時間・ご希望のマイク本数を入力すると、最適なプランの概算料金と内訳を算出します。")

# データ読み込み
@st.cache_data
def load_data():
    excel_file = 'マイク料金表.xlsx'
    xls = pd.ExcelFile(excel_file)
    data_dict = {}
    for sheet in xls.sheet_names:
        df = pd.read_excel(excel_file, sheet_name=sheet)
        df = df.fillna(0)
        data_dict[sheet] = df
    return data_dict

def safe_int(val):
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return 0

try:
    data = load_data()
    
    # 0. 宴席情報・基本情報の入力（上部）
    st.subheader("📝 宴席情報・基本情報")
    col_info1, col_info2 = st.columns(2)
    with col_info1:
        banquet_name = st.text_input("宴席名（手入力）", value="", placeholder="例：〇〇株式会社 様 ご利用")
    with col_info2:
        event_date = st.date_input("利用日付", value=datetime.date.today())
        
    st.markdown("---")
    
    # 1. 会場選択
    venues = list(data.keys())
    selected_venue = st.selectbox("📍 会場を選択してください", venues)
    
    df = data[selected_venue]
    
    # 選択した会場の基本マイク本数（基本プランの1行目）をデフォルト値として取得
    first_row = df.iloc[0]
    
    def get_base_qty(col_keyword):
        col = next((c for c in df.columns if col_keyword in str(c)), None)
        return safe_int(first_row[col]) if col else 0

    default_wired = get_base_qty("基本有線")
    default_wireless = get_base_qty("基本ワイヤレス")
    default_pin = get_base_qty("基本ピン")
    
    st.markdown("---")
    
    # 2. 利用時間選択（30分単位）
    st.subheader("⏰ ご利用時間を指定してください（幹事来館〜終了）")
    
    # 07:00 〜 23:00 までの30分刻みリスト作成
    time_options = []
    for h in range(7, 24):
        time_options.append(f"{h:02d}:00")
        if h < 23:
            time_options.append(f"{h:02d}:30")
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        start_time_str = st.selectbox("幹事来館時間", time_options, index=2, key="start_time") # デフォルト 08:00
    with col_t2:
        end_time_str = st.selectbox("終了時間", time_options, index=14, key="end_time")     # デフォルト 14:00
        
    start_h, start_m = map(int, start_time_str.split(":"))
    end_h, end_m = map(int, end_time_str.split(":"))
    
    start_val = start_h + start_m / 60.0
    end_val = end_h + end_m / 60.0
    
    use_hours = end_val - start_val
    
    if use_hours <= 0:
        st.warning("⚠️ 終了時間は開始時間より後の時間を選択してください。")
        use_hours = 0
        raw_extension_hours = 0
        extension_hours = 0
    else:
        st.info(f"💡 利用予定時間: **{use_hours:.1f} 時間**")
        raw_extension_hours = max(0.0, use_hours - 6.0)
        # 6時間を超えた端数時間を繰り上げ計算（例：0.5時間 ➔ 1時間）
        extension_hours = math.ceil(raw_extension_hours)
    
    st.markdown("---")
    
    # 3. マイク本数指定
    st.subheader("🎤 ご希望のマイク本数を指定してください")
    st.caption("※基本料金に含まれるマイク本数も含めた「全体の必要本数」をご指定ください。")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        req_wired = st.number_input(
            "有線マイク (本)", min_value=1, max_value=10, 
            value=max(1, default_wired), key=f"wired_{selected_venue}"
        )
    with col2:
        req_wireless = st.number_input(
            "ワイヤレスマイク (本)", min_value=0, max_value=10, 
            value=default_wireless, key=f"wireless_{selected_venue}"
        )
    with col3:
        req_pin = st.number_input(
            "ピンマイク (本)", min_value=0, max_value=10, 
            value=default_pin, key=f"pin_{selected_venue}"
        )
        
    st.markdown("---")
    
    # 列名の特定（『合計』列を優先して検索）
    wireless_col = next((c for c in df.columns if 'ワイ合計' in str(c)), None)
    pin_col = next((c for c in df.columns if 'ピン合計' in str(c)), None)
    wired_col = next((c for c in df.columns if '有線合計' in str(c)), None)
    
    # 有線合計列がない場合のみ基本有線列で代替
    if not wired_col:
        wired_col = next((c for c in df.columns if '基本有線' in str(c)), None)
    
    # 検索条件の作成
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
        
        # オペレーター料金の取得
        op_col = next((c for c in df.columns if 'オペレーター' in str(c)), None)
        op_price = safe_int(row[op_col]) if op_col else 0
        
        # 基本料金の延長単価判定（ボールルーム: 15,000円 / その他: 3,000円）
        is_ballroom = ("ボールルーム" in selected_venue)
        base_ext_unit_price = 15000 if is_ballroom else 3000
        base_ext_price = extension_hours * base_ext_unit_price
        
        # オペレーター延長単価（全会場一律 15,000円）
        op_ext_unit_price = 15000
        op_ext_price = extension_hours * op_ext_unit_price if op_price > 0 else 0
        
        # オペレーター料金（本体）がある場合は合計から除外
        calc_total_price = (raw_total_price - op_price) + base_ext_price
        
        if op_price > 0:
            st.success(f"### **概算合計金額: {calc_total_price:,} 円** (※オペレーター料金除く)")
        else:
            st.success(f"### **概算合計金額: {calc_total_price:,} 円**")
        
        # 連絡フラグの表示分岐（オペレーターの要不要で文章変更）
        if '連絡' in row and str(row['連絡']).strip() in ['〇', '○', '1']:
            if op_price > 0:
                st.warning("⚠️ この構成は音響オペレーターまたは追加機器の調整が必要です（連絡要）。")
            else:
                st.warning("⚠️ この構成は追加機器の調整が必要です（連絡要）。")
            
        st.write("#### 📋 料金内訳明細")
        
        detail_table = []
        cols = list(df.columns)
        
        # 基本料金列の位置を取得
        base_price_idx = next((i for i, c in enumerate(cols) if '基本料金' in str(c)), -1)
        
        if base_price_idx != -1:
            # 1. 基本料金
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
            
            # 基本料金の延長料金表示（繰り上げ後の時間数）
            if extension_hours > 0:
                detail_table.append({
                    "項目名": "会場基本料金 延長",
                    "備考": f"6時間超え分 (繰り上げ算定: {extension_hours}時間)",
                    "数量": f"{extension_hours} 時間",
                    "単価": f"{base_ext_unit_price:,} 円",
                    "小計": f"{base_ext_price:,} 円"
                })
            
            # 2. 追加・仮設マイクおよび機材・オペレーター
            for idx in range(base_price_idx + 1, len(cols)):
                col_name = str(cols[idx])
                clean_name = col_name.split('.')[0]
                
                if clean_name in ['合計', '連絡', 'ワイ合計', 'ピン合計', '有線合計']:
                    continue
                    
                subtotal = safe_int(row[col_name])
                if subtotal > 0:
                    qty = 1
                    unit_str = "式"
                    
                    # 前半の数量列から該当する数量を取得
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
                    
                    # オペレーターの場合は参考価格として表示
                    if 'オペレーター' in clean_name:
                        detail_table.append({
                            "項目名": clean_name,
                            "備考": "6時間まで (※参考価格/要確認)",
                            "数量": f"{qty} {unit_str}",
                            "単価": f"{unit_price:,} 円",
                            "小計": f"{subtotal:,} 円"
                        })
                        
                        # オペレーターの延長料金（発生時のみ参考表示）
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
                            "備考": "-",
                            "数量": f"{qty} {unit_str}",
                            "単価": f"{unit_price:,} 円",
                            "小計": f"{subtotal:,} 円"
                        })
                        
        if detail_table:
            st.table(pd.DataFrame(detail_table))
            
        # 4. 見積結果下部に宴席情報を表示
        display_banquet_name = banquet_name if banquet_name.strip() else "（未入力）"
        formatted_date = event_date.strftime("%Y年%m月%d日")
        
        st.info(f"📌 **宴席・基本情報サマリー**\n\n"
                f"- **宴席名:** {display_banquet_name}\n"
                f"- **利用日付:** {formatted_date}\n"
                f"- **会場名:** {selected_venue}\n"
                f"- **ご利用時間:** {start_time_str} 〜 {end_time_str} （{use_hours:.1f}時間）")
            
    else:
        st.error("指定されたマイク本数の組み合わせに該当するプランが見つかりませんでした。本数を調整してください。")
        
    with st.expander("📄 この会場の全パターン料金表を確認する"):
        st.dataframe(df)

except Exception as e:
    st.error(f"エラーが発生しました: {e}")
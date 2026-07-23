print_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <!-- html2pdf.js ライブラリの読み込み -->
                <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
                <style>
                    body {{ font-family: "Helvetica Neue", Arial, "Hiragino Kaku Gothic ProN", "Hiragino Sans", Meiryo, sans-serif; padding: 20px; color: #333; }}
                    #pdf-area {{ padding: 20px; background: #fff; width: 100%; box-sizing: border-box; }}
                    h2 {{ border-bottom: 2px solid #333; padding-bottom: 5px; margin-top: 0; font-size: 20px; }}
                    h3 {{ font-size: 16px; margin-top: 20px; margin-bottom: 10px; border-left: 4px solid #007bff; padding-left: 8px; }}
                    .summary {{ background: #f8f9fa; border: 1px solid #ddd; padding: 12px 15px; border-radius: 5px; margin-bottom: 15px; page-break-inside: avoid; }}
                    .summary p {{ margin: 4px 0; font-size: 13px; }}
                    .price-box {{ font-size: 18px; font-weight: bold; color: #1a5276; margin: 15px 0; padding: 10px; background: #eaf2f8; border-radius: 5px; page-break-inside: avoid; }}
                    
                    /* テーブルのレイアウト最適化 & 改ページ防止 */
                    table.print-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; table-layout: auto; page-break-inside: auto; }}
                    table.print-table tr {{ page-break-inside: avoid; page-break-after: auto; }}
                    table.print-table th, table.print-table td {{ border: 1px solid #ccc; padding: 6px 10px; text-align: left; font-size: 12px; white-space: normal; word-break: break-all; }}
                    table.print-table th {{ background-color: #f2f2f2; font-weight: bold; }}
                    
                    /* ボタンエリア */
                    .action-container {{ margin-top: 25px; display: flex; gap: 15px; align-items: flex-start; }}
                    .btn-print {{ padding: 10px 20px; font-size: 14px; font-weight: bold; cursor: pointer; background: #007bff; color: white; border: none; border-radius: 5px; }}
                    .btn-pdf {{ padding: 10px 20px; font-size: 14px; font-weight: bold; cursor: pointer; background: #28a745; color: white; border: none; border-radius: 5px; }}
                    .btn-note {{ font-size: 12px; color: #666; margin-top: 5px; }}
                    
                    @media print {{
                        .no-print {{ display: none !important; }}
                        body {{ padding: 0; }}
                        #pdf-area {{ padding: 0; }}
                    }}
                </style>
            </head>
            <body>
                <!-- PDF出力対象エリア -->
                <div id="pdf-area">
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
                </div>
                
                <div class="action-container no-print">
                    <div>
                        <button class="btn-print" onclick="window.print()">
                            🖨️ 印刷画面を開く
                        </button>
                        <div class="btn-note">※紙に印刷したい場合</div>
                    </div>
                    <div>
                        <button class="btn-pdf" onclick="downloadPDF()">
                            💾 PDFファイルを直接保存
                        </button>
                        <div class="btn-note">※ファイルとしてダウンロード保存する場合</div>
                    </div>
                </div>

                <script>
                    function downloadPDF() {{
                        const element = document.getElementById('pdf-area');
                        
                        // PDF生成オプション（改ページ制御とサイズ調整）
                        const opt = {{
                            margin:       [10, 10, 10, 10], // 上右下左の余白(mm)
                            filename:     '見積書_{display_banquet_name}.pdf',
                            image:        {{ type: 'jpeg', quality: 0.98 }},
                            html2canvas:  {{ scale: 2, useCORS: true, logging: false }},
                            jsPDF:        {{ unit: 'mm', format: 'a4', orientation: 'portrait' }},
                            pagebreak:    {{ mode: ['avoid-all', 'css', 'legacy'] }} // 要素の途中での途切れを防止
                        }};
                        
                        html2pdf().set(opt).from(element).save();
                    }}
                </script>
            </body>
            </html>
            """
            st.components.v1.html(print_html, height=600, scrolling=True)
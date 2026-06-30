import csv
import os
import urllib.parse
import math  
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler

CSV_FILE = "period_daily_data.csv"

def init_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["name", "date", "blood_flow", "symptoms", "sexual_activity", "contraception", "initial_cycle", "record_type"])

def get_daily_records(user_name):
    records = []
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if row and row[0].strip() == user_name.strip():
                    records.append({
                        "date": row[1],
                        "blood_flow": row[2],
                        "symptoms": row[3],
                        "sexual_activity": row[4],
                        "contraception": row[5],
                        "initial_cycle": row[6] if len(row) > 6 else "",
                        "record_type": row[7] if len(row) > 7 else "daily"
                    })
    records.sort(key=lambda x: x["date"])
    return records

def add_daily_record(user_name, date_str, blood_flow="沒有月經量", symptoms="無症狀", sexual_activity="否", contraception="無", initial_cycle="", record_type="daily"):
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([user_name.strip(), date_str, blood_flow, symptoms, sexual_activity, contraception, initial_cycle, record_type])

def analyze_health_data(records, default_cycle=30):
    if not records:
        return None
    
    user_cycle = default_cycle
    for r in records:
        if r["initial_cycle"] and r["initial_cycle"].strip():
            try:
                val = int(r["initial_cycle"].strip())
                if val > 0:
                    user_cycle = val  
            except ValueError:
                pass
            
    period_starts = []
    flow_dates = []
    for r in records:
        if r["blood_flow"] in ["量少", "量適中", "量多"]:
            flow_dates.append(datetime.strptime(r["date"], "%Y-%m-%d"))
            
    if flow_dates:
        period_starts.append(flow_dates[0])
        for i in range(1, len(flow_dates)):
            if (flow_dates[i] - flow_dates[i-1]).days > 10:
                period_starts.append(flow_dates[i])
                
    show_alert = False
    if len(period_starts) >= 2:
        anomaly_flags = []
        for i in range(1, len(period_starts)):
            current_start = period_starts[i]
            prev_start = period_starts[i-1]
            
            actual_days = (current_start - prev_start).days
            expected_date = prev_start + timedelta(days=user_cycle)
            deviation = abs((current_start - expected_date).days)
            
            if actual_days < 21 or actual_days > 35 or deviation > 7:
                anomaly_flags.append(True)
            else:
                anomaly_flags.append(False)
        
        if len(anomaly_flags) >= 5 and all(anomaly_flags[-5:]):
            show_alert = True
            
    last_start_date = period_starts[-1] if period_starts else None
    
    return {
        "user_cycle": user_cycle,
        "last_start_date": last_start_date,
        "show_alert": show_alert
    }

class SimplePeriodTracker(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed_url.query)

        user_name = params.get("user_name", [""])[0].strip()
        records = get_daily_records(user_name) if user_name else []
        analysis = analyze_health_data(records)

        symptom_list = ["頭痛", "肚子痛", "下背痛", "心情變化", "疲勞", "食慾改變", "噁心", "腹瀉"]
        alert_html = ""

        if analysis and analysis["show_alert"]:
            alert_html = """
            <div class="no-print" style="background-color: #FFF9F3; border: 2px solid #E8D3D1; color: #8A6562; padding: 15px; border-radius: 8px; margin-bottom: 25px; font-weight: bold; font-size: 0.95em; line-height: 1.5;">
                ❕ ❀ 溫馨健康風險提示：<br>
                系統偵測到您已連續 5 次以上生理期出現不規律或天數異常（週期過短、過長，或與預期日誤差超過 7 天）。<br>
                <span style="font-weight: normal; color: #666666;">長期的經期不規律可能與壓力、荷爾蒙失調或卵巢健康相關，建議您可以安排時間至婦產科諮詢專業醫師，並提供下方的歷史紀錄健康報告供醫生參考，好好照顧自己。</span>
            </div>
            """

        html = f"""
        <!DOCTYPE html>
        <html lang="zh-TW">
        <head>
            <meta charset="UTF-8">
            <title>❀ 個人生理期每日智慧健康系統</title>
            <style>
                body {{ font-family: 'Microsoft JhengHei', sans-serif; max-width: 750px; margin: 30px auto; padding: 20px; color: #4A4A4A; line-height: 1.6; background-color: #FFFDFE; }}
                .box {{ border: 1px solid #F4DDDF; padding: 20px; border-radius: 8px; background: #FCF5F7; margin-bottom: 20px; }}
                .welcome-box {{ border: 2px dashed #E8D3D1; background: #FCF5F7; }}
                input[type="text"], input[type="date"], input[type="number"], select, button {{ padding: 10px; margin: 8px 0; width: 100%; box-sizing: border-box; border: 1px solid #E8D3D1; border-radius: 4px; }}
                button {{ background-color: #F4DDDF; color: #5A4A4A; border: 1px solid #E8D3D1; font-weight: bold; cursor: pointer; transition: background 0.2s; }}
                button:hover {{ background-color: #E8D3D1; color: #5A4A4A; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 15px; background: white; }}
                th, td {{ border: 1px solid #F4DDDF; padding: 10px; text-align: left; font-size: 0.92em; }}
                th {{ background-color: #F4DDDF; color: #5A4A4A; }}
                .btn-pdf {{ background-color: #8AC4DE; color: white; border: none; font-size: 1.05em; padding: 12px; margin-top: 15px; }}
                .btn-pdf:hover {{ background-color: #6C9BD2; }}
                .form-group {{ margin-bottom: 15px; }}
                .checkbox-group {{ display: flex; flex-wrap: wrap; gap: 10px; margin: 8px 0; }}
                .checkbox-item {{ background: white; border: 1px solid #F4DDDF; padding: 6px 12px; border-radius: 20px; cursor: pointer; font-size: 0.9em; }}
                .checkbox-item input {{ margin-right: 5px; }}
                .sub-group {{ background: #FFFDFE; padding: 12px; border-radius: 6px; margin-top: 8px; display: none; border: 1px solid #F4DDDF; }}
                .calendar-tags {{ display: flex; flex-direction: column; gap: 8px; margin-top: 10px; }}
                .tag {{ padding: 10px; border-radius: 6px; font-weight: bold; }}
                .tag-prediction {{ background-color: #FCF5F7; color: #5A4A4A; border-left: 5px solid #9FD0DE; }}
                .tag-danger {{ background-color: #FCF5F7; color: #5A4A4A; border-left: 5px solid #F4DDDF; }}
                .tag-safe {{ background-color: #FCF5F7; color: #5A4A4A; border-left: 5px solid #8AC4DE; }}
                .text-highlight {{ color: #6C9BD2; font-weight: bold; }}
                .flow-conditional {{ display: none; }}
                
                /* SVG 圖表容器與基礎樣式 */
                .chart-container {{ width: 100%; background: white; padding: 15px; border-radius: 6px; border: 1px solid #F4DDDF; box-sizing: border-box; }}
                .legend-container {{ display: flex; gap: 20px; justify-content: center; margin-bottom: 10px; font-size: 0.85em; }}
                .legend-item {{ display: flex; align-items: center; gap: 5px; }}
                .legend-line {{ width: 25px; height: 3px; }}
                .legend-dot {{ width: 10px; height: 10px; border-radius: 50%; }}

                @media print {{ .no-print, form, button {{ display: none !important; }} }}
            </style>
            <script>
                function toggleSexActivity() {{
                    var hasSex = document.getElementById('has_sex_activity').value;
                    var contraDiv = document.getElementById('contraception_box');
                    contraDiv.style.display = (hasSex === 'yes') ? 'block' : 'none';
                }}
                
                function handleFirstTimeChange() {{
                    var isFirst = document.getElementById('is_first_menstruation').value;
                    var sectionNotFirst = document.getElementById('section_not_first');
                    var sectionIsFirst = document.getElementById('section_is_first');
                    
                    if (isFirst === 'yes') {{
                        sectionIsFirst.style.display = 'block';
                        sectionNotFirst.style.display = 'none';
                        document.getElementById('not_first_start').required = false;
                        document.getElementById('not_first_end').required = false;
                        document.getElementById('first_start').required = true;
                    }} else if (isFirst === 'no') {{
                        sectionIsFirst.style.display = 'none';
                        sectionNotFirst.style.display = 'block';
                        document.getElementById('not_first_start').required = true;
                        document.getElementById('not_first_end').required = true;
                        document.getElementById('first_start').required = false;
                    }} else {{
                        sectionIsFirst.style.display = 'none';
                        sectionNotFirst.style.display = 'none';
                    }}
                }}
            </script>
        </head>
        <body>

            <h2 class="no-print" style="color: #5A4A4A;">❀ 生理期每日隨手記與智慧推演系統</h2>
            {alert_html}

            <div class="box no-print">
                <form action="/" method="get">
                    <label>☛ 請輸入您的名字（用於儲存與找回歷史紀錄）：</label>
                    <input type="text" name="user_name" value="{user_name}" required placeholder="例如：Mary">
                    <button type="submit">確認名字 / 尋找紀錄</button>
                </form>
            </div>
        """

        if user_name:
            html += f"<h3>目前使用者：<span style=\"color:#6C9BD2;\">{user_name}</span></h3>"
            
            if not records:
                cycle_options = "".join([f'<option value="{i}" {"selected" if i==30 else ""}>{i} 天</option>' for i in range(10, 91)])
                
                html += f"""
                <div class="box welcome-box no-print">
                    <h3 style="color: #5A4A4A; margin-top: 0;">❀ 歡迎新朋友 {user_name}</h3>
                    <p>請先填寫基本初始資訊，建立您的專屬女性健康檔案：</p>
                    <form action="/add" method="get">
                        <input type="hidden" name="user_name" value="{user_name}">
                        <input type="hidden" name="is_new_user" value="yes">
                        
                        <div class="form-group">
                            <label><b>☛ 請問這是您人生中第一次生理期來潮（初經）嗎？</b></label>
                            <select id="is_first_menstruation" name="is_first_menstruation" onchange="handleFirstTimeChange()" required>
                                <option value="">-- 請選擇 --</option>
                                <option value="no">不是，我以前就來過了</option>
                                <option value="yes">是的，這是我的第一次（初經）</option>
                            </select>
                        </div>

                        <div id="section_not_first" class="flow-conditional">
                            <div class="form-group">
                                <label><b>📅 上一次生理期開始日期：</b></label>
                                <input type="date" id="not_first_start" name="not_first_start_date">
                            </div>
                            <div class="form-group">
                                <label><b>📅 上一次生理期結束日期（計算本次來潮天數）：</b></label>
                                <input type="date" id="not_first_end" name="not_first_end_date">
                            </div>
                            <div class="form-group">
                                <label><b>請問您的生理期平均週期大約是多少天？</b></label>
                                <select name="cycle_length">{cycle_options}</select>
                            </div>
                        </div>

                        <div id="section_is_first" class="flow-conditional">
                            <div class="form-group">
                                <label><b>📅 請問本次初經是在哪一天開始的？</b></label>
                                <input type="date" id="first_start" name="first_start_date">
                            </div>
                            <div class="form-group">
                                <label><b>預估平均週期天數：</b></label>
                                <select name="first_cycle_length">{cycle_options}</select>
                            </div>
                        </div>
                        
                        <button type="submit">建立檔案並開通天天紀錄功能</button>
                    </form>
                </div>
                """
            else:
                user_cycle = analysis["user_cycle"]
                last_start = analysis["last_start_date"]
                
                current_day_in_cycle = 1
                if last_start:
                    today_date = datetime.now().date()
                    days_passed = (today_date - last_start.date()).days
                    current_day_in_cycle = (days_passed % user_cycle) + 1 if days_passed >= 0 else 1
                    
                    next_start = last_start + timedelta(days=user_cycle)
                    window_start = next_start - timedelta(days=7)
                    window_end = next_start + timedelta(days=7)
                    ovulation_day = next_start - timedelta(days=14)
                    danger_start = ovulation_day - timedelta(days=5)
                    danger_end = ovulation_day + timedelta(days=4)
                    
                    panel_html = f"""
                    <div class="box">
                        <h4 style="margin-top:0; color:#5A4A4A;">📊 個人化智慧經期與波動預測面板</h4>
                        <p>最近一次生理期開始日：<b>{last_start.strftime('%Y-%m-%d')}</b>（您的設定週期：<span class="text-highlight">{user_cycle} 天</span>）</p>
                        <div class="calendar-tags">
                            <div class="tag tag-prediction">
                                📅 下次生理期預計抵達日：{next_start.strftime('%Y-%m-%d')} <br>
                                <span style="font-size:0.85em; font-weight:normal; color:#666;">(正常生理波動區間：{window_start.strftime('%Y-%m-%d')} ～ {window_end.strftime('%Y-%m-%d')} 前後 7 天內)</span>
                            </div>
                            <div class="tag tag-danger">
                                ❀ 排卵期（危險期）：{danger_start.strftime('%Y-%m-%d')} ～ {danger_end.strftime('%Y-%m-%d')}
                            </div>
                            <div class="tag tag-safe">
                                🛡️ 安全期：除了上述排卵期與經期以外的時間。
                            </div>
                        </div>
                    </div>
                    """
                else:
                    panel_html = """
                    <div class="box">
                        <h4 style="margin-top:0; color:#666;">📊 智慧分析準備中</h4>
                        <p>請持續在下方紀錄每日狀況，系統便能精準為您推算下一次生理期與排卵期。</p>
                    </div>
                    """
                
                html += panel_html
                
                # --- 動態原生 SVG 繪圖邏輯 ---
                W, H = 660, 240
                pad_L, pad_R, pad_T, pad_B = 40, 20, 20, 35
                graph_w = W - pad_L - pad_R
                graph_h = H - pad_T - pad_B
                
                ovulation_idx = user_cycle - 14
                est_points = []
                prog_points = []
                today_cx, today_cy = None, None
                
                for idx in range(user_cycle):
                    day = idx + 1
                    # 激素曲線公式計算
                    if day <= ovulation_idx:
                        val_est = 10 + (80 * (day / ovulation_idx)**2)
                        val_prog = 5
                    else:
                        val_est = 40 + 30 * math.sin((day - ovulation_idx) * 3.14159 / 14) if day <= ovulation_idx + 14 else 10
                        val_prog = 5 + 75 * math.sin((day - ovulation_idx) * 3.14159 / 14)
                    
                    x = pad_L + (idx / (user_cycle - 1)) * graph_w if user_cycle > 1 else pad_L
                    y_est = pad_T + graph_h - (val_est / 100) * graph_h
                    y_prog = pad_T + graph_h - (val_prog / 100) * graph_h
                    
                    est_points.append(f"{x},{y_est}")
                    prog_points.append(f"{x},{y_prog}")
                    
                    if day == current_day_in_cycle:
                        today_cx, today_cy = x, pad_T + graph_h - (95 / 100) * graph_h

                est_path = " ".join(est_points)
                prog_path = " ".join(prog_points)
                
                # 軸線與刻度 SVG 元素
                svg_elements = ""
                # Y 軸刻度 (0, 20, 40, 60, 80, 100)
                for i in range(0, 101, 20):
                    y_pos = pad_T + graph_h - (i / 100) * graph_h
                    svg_elements += f'<line x1="{pad_L}" y1="{y_pos}" x2="{W-pad_R}" y2="{y_pos}" stroke="#F0F0F0" stroke-width="1"/>'
                    svg_elements += f'<text x="{pad_L-8}" y="{y_pos+4}" font-size="10" fill="#888" text-anchor="end">{i}</text>'
                
                # X 軸刻度
                step = max(1, user_cycle // 10)
                for idx in range(0, user_cycle, step):
                    day = idx + 1
                    x_pos = pad_L + (idx / (user_cycle - 1)) * graph_w if user_cycle > 1 else pad_L
                    svg_elements += f'<line x1="{x_pos}" y1="{pad_T}" x2="{x_pos}" y2="{pad_T+graph_h}" stroke="#F0F0F0" stroke-width="1"/>'
                    svg_elements += f'<text x="{x_pos}" y="{pad_T+graph_h+15}" font-size="10" fill="#888" text-anchor="middle">{day}</text>'

                # 如果有當天位置，繪製提示大圓點
                today_dot_html = ""
                if today_cx is not None:
                    today_dot_html = f"""
                    <circle cx="{today_cx}" cy="{today_cy}" r="7" fill="#8AC4DE" />
                    <line x1="{today_cx}" y1="{pad_T}" x2="{today_cx}" y2="{pad_T+graph_h}" stroke="#8AC4DE" stroke-dasharray="4,4" stroke-width="1.5"/>
                    """

                html += f"""
                <div class="box">
                    <h4 style="margin-top:0; color:#5A4A4A;">📈 專屬體內激素規律動態變化圖 (免連網本地版)</h4>
                    <p style="font-size:0.85em; color:#666;">依據您設定的 {user_cycle} 天週期推演。您目前大處於週期的第 <span class="text-highlight">{current_day_in_cycle}</span> 天：</p>
                    
                    <div class="chart-container">
                        <div class="legend-container">
                            <div class="legend-item"><div class="legend-line" style="background: #6C9BD2;"></div>雌激素 (Estrogen)</div>
                            <div class="legend-item"><div class="legend-line" style="background: #E8D3D1;"></div>孕激素 (Progesterone)</div>
                            <div class="legend-item"><div class="legend-dot" style="background: #8AC4DE;"></div>您今天的位置 (Day {current_day_in_cycle})</div>
                        </div>
                        <svg viewBox="0 0 {W} {H}" width="100%" height="100%" style="overflow: visible;">
                            {svg_elements}
                            <line x1="{pad_L}" y1="{pad_T}" x2="{pad_L}" y2="{pad_T+graph_h}" stroke="#CCCCCC" stroke-width="1"/>
                            <line x1="{pad_L}" y1="{pad_T+graph_h}" x2="{W-pad_R}" y2="{pad_T+graph_h}" stroke="#CCCCCC" stroke-width="1"/>
                            <text x="{pad_L-25}" y="{pad_T-5}" font-size="9" fill="#666" font-weight="bold">濃度(%)</text>
                            <text x="{W-pad_R}" y="{pad_T+graph_h+30}" font-size="9" fill="#666" font-weight="bold" text-anchor="end">週期天數(Day)</text>
                            
                            <polyline points="{est_path}" fill="none" stroke="#6C9BD2" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                            <polyline points="{prog_path}" fill="none" stroke="#E8D3D1" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                            
                            {today_dot_html}
                        </svg>
                    </div>
                </div>
                """
                
                today_str = datetime.now().strftime('%Y-%m-%d')
                s_checkboxes = "".join([f'<label class="checkbox-item"><input type="checkbox" name="symptoms" value="{s}">{s}</label>' for s in symptom_list])
                
                html += f"""
                <div class="box no-print">
                    <h4 style="margin-top:0; color: #5A4A4A;">📝 記錄單日身體狀況（天天皆可紀錄）</h4>
                    <form action="/add" method="get">
                        <input type="hidden" name="user_name" value="{user_name}">
                        <input type="hidden" name="is_new_user" value="no">
                        
                        <div class="form-group">
                            <label><b>選擇欲紀錄的日期：</b></label>
                            <input type="date" name="record_date" value="{today_str}" required>
                        </div>
                        
                        <div class="form-group">
                            <label><b>☛ 1. 今日經血量（非生理期間請選沒有月經量）：</b></label>
                            <select name="blood_flow_level">
                                <option value="沒有月經量" selected>沒有月經量 (乾淨狀態)</option>
                                <option value="量少">量少</option>
                                <option value="量適中">量適中</option>
                                <option value="量多">量多</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label><b>☛ 2. 今日身體症狀：</b></label>
                            <div class="checkbox-group">{s_checkboxes}</div>
                        </div>
                        
                        <div class="form-group" style="border-top: 1px dashed #E8D3D1; padding-top: 10px;">
                            <label><b>☛ 3. 今天是否有發生性行為？</b></label>
                            <select id="has_sex_activity" name="has_sex_activity" onchange="toggleSexActivity()">
                                <option value="no" selected>否</option>
                                <option value="yes">是</option>
                            </select>
                            
                            <div id="contraception_box" class="sub-group">
                                <label><b>採取之避孕方式：</b></label>
                                <select name="contraception_method">
                                    <option value="保險套" selected>保險套 (預設)</option>
                                    <option value="事前藥物">事前藥物</option>
                                    <option value="事後藥物">事後藥物</option>
                                    <option value="貼片">貼片</option>
                                    <option value="注射式">注射式</option>
                                    <option value="植入式">植入式</option>
                                    <option value="無避孕措施">未採取任何避孕措施</option>
                                    <option value="其他">其他</option>
                                </select>
                            </div>
                        </div>
                        <button type="submit">儲存今日狀態</button>
                    </form>
                </div>

                <div class="box">
                    <h4 style="margin-top:0; color:#5A4A4A;">📄 每日健康日誌歷程牆</h4>
                    <table>
                        <tr>
                            <th>紀錄日期</th>
                            <th>月經血量</th>
                            <th>當日身體症狀</th>
                            <th>性行為</th>
                            <th>避孕措施</th>
                        </tr>
                """
                for r in reversed(records):
                    html += f"""
                    <tr>
                        <td><b>{r['date']}</b></td>
                        <td>{r['blood_flow']}</td>
                        <td><span style="color:#666666;">{r['symptoms']}</span></td>
                        <td>{r['sexual_activity']}</td>
                        <td><span class="text-highlight">{r['contraception']}</span></td>
                    </tr>
                    """
                html += """
                    </table>
                    <button class="btn-pdf no-print" onclick="window.print()">📄 匯出此畫面為健康 PDF 報告</button>
                </div>
                """

        html += "</body></html>"
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

class RouterServer(SimplePeriodTracker):
    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        if parsed_url.path == "/add":
            params = urllib.parse.parse_qs(parsed_url.query)
            user_name = params.get("user_name", [""])[0]
            is_new = params.get("is_new_user", ["no"])[0]
            
            if is_new == "yes":
                is_first = params.get("is_first_menstruation", ["no"])[0]
                if is_first == "yes":
                    date_str = params.get("first_start_date", [""])[0]
                    cycle_length = params.get("first_cycle_length", ["30"])[0]
                    add_daily_record(user_name, date_str, "量適中", "初經來潮第一天", "否", "無", cycle_length, "daily")
                else:
                    start_str = params.get("not_first_start_date", [""])[0]
                    end_str = params.get("not_first_end_date", [""])[0]
                    cycle_length = params.get("cycle_length", ["30"])[0]
                    
                    try:
                        d_start = datetime.strptime(start_str, "%Y-%m-%d")
                        d_end = datetime.strptime(end_str, "%Y-%m-%d")
                        delta_days = (d_end - d_start).days
                        
                        for i in range(delta_days + 1):
                            current_date_str = (d_start + timedelta(days=i)).strftime("%Y-%m-%d")
                            c_len = cycle_length if i == 0 else ""
                            add_daily_record(user_name, current_date_str, "量適中", "上一次歷史經期紀錄", "否", "無", c_len, "history")
                    except:
                        add_daily_record(user_name, start_str, "量適中", "上一次歷史經期紀錄", "否", "無", cycle_length, "history")
            else:
                date_str = params.get("record_date", [""])[0]
                blood_flow = params.get("blood_flow_level", ["沒有月經量"])[0]
                
                symptoms_arr = params.get("symptoms", [])
                symptoms_str = "、".join(symptoms_arr) if symptoms_arr else "無症狀"
                
                has_sex = params.get("has_sex_activity", ["no"])[0]
                sexual_activity_str = "否"
                contraception_str = "無"
                
                if has_sex == "yes":
                    sexual_activity_str = "有"
                    contraception_str = params.get("contraception_method", ["保險套"])[0]

                add_daily_record(user_name, date_str, blood_flow, symptoms_str, sexual_activity_str, contraception_str, "", "daily")

            self.send_response(303)
            self.send_header("Location", f"/?user_name={urllib.parse.quote(user_name)}")
            self.end_headers()
        else:
            super().do_GET()

if __name__ == "__main__":
    init_csv()
    port = 8000
    print(f"每日健康系統已在線！請打開瀏覽器：http://localhost:{port}")
    HTTPServer(("localhost", port), RouterServer).serve_forever()
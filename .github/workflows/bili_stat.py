import requests
import json
import os
from datetime import datetime

# ====== 配置区 ======
UID = "你的B站UID"  # 改成你的UID，比如 "12345678"
DATA_FILE = "../../bili_stats.json"   # 数据文件（根目录）
REPORT_FILE = "../../report.html"     # 报告文件（根目录）
# ===================

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": f"https://space.bilibili.com/{UID}"
}

def get_user_info():
    """获取用户基本信息（粉丝数等）"""
    url = f"https://api.bilibili.com/x/space/acc/info?mid={UID}"
    resp = requests.get(url, headers=HEADERS)
    data = resp.json()
    if data["code"] != 0:
        raise Exception(f"获取用户信息失败: {data['message']}")
    return {
        "name": data["data"]["name"],
        "fans": data["data"]["fans"],
        "following": data["data"]["following"],
        "face": data["data"]["face"]
    }

def get_user_stats():
    """获取用户数据统计（播放量、点赞数）"""
    url = f"https://api.bilibili.com/x/space/upstat?mid={UID}"
    resp = requests.get(url, headers=HEADERS)
    data = resp.json()
    if data["code"] != 0:
        raise Exception(f"获取统计数据失败: {data['message']}")
    return {
        "views": data["data"]["archive"]["view"],
        "likes": data["data"]["likes"]
    }

def load_history():
    """加载历史数据"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_history(history):
    """保存历史数据"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def calc_change(current, previous):
    """计算变化量"""
    if not previous:
        return {"views": 0, "likes": 0, "fans": 0}
    return {
        "views": current["views"] - previous["views"],
        "likes": current["likes"] - previous["likes"],
        "fans": current["fans"] - previous["fans"]
    }

def generate_html(history, user_info):
    """生成纯HTML报告，无JS库"""
    if not history:
        return
    
    latest = history[-1]
    total = len(history)
    
    # 计算历史最高
    max_views = max(h["views"] for h in history)
    max_likes = max(h["likes"] for h in history)
    max_fans = max(h["fans"] for h in history)
    
    # 生成表格行（倒序，最新的在上面）
    rows = ""
    for item in reversed(history):
        change = item.get("change", {"views": 0, "likes": 0, "fans": 0})
        
        def fmt_change(val):
            if val > 0:
                return f'<span style="color:#e74c3c;">▲ +{val:,}</span>'
            elif val < 0:
                return f'<span style="color:#27ae60;">▼ {val:,}</span>'
            else:
                return '<span style="color:#999;">— 0</span>'
        
        rows += f"""
        <tr>
            <td>{item['date']}</td>
            <td>{item['views']:,} {fmt_change(change['views'])}</td>
            <td>{item['likes']:,} {fmt_change(change['likes'])}</td>
            <td>{item['fans']:,} {fmt_change(change['fans'])}</td>
        </tr>"""
    
    # 生成简易柱状图（纯CSS，无JS）
    chart_bars = ""
    for item in history[-12:]:  # 最近12条
        h_views = int(item["views"] / max_views * 100) if max_views > 0 else 0
        h_fans = int(item["fans"] / max_fans * 100) if max_fans > 0 else 0
        chart_bars += f"""
        <div class="chart-group">
            <div class="chart-label">{item['date'][5:]}</div>
            <div class="chart-bars">
                <div class="bar bar-views" style="height:{h_views}%" title="播放量: {item['views']:,}"></div>
                <div class="bar bar-fans" style="height:{h_fans}%" title="粉丝数: {item['fans']:,}"></div>
            </div>
        </div>"""
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>B站数据统计报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #f5f7fa;
            color: #333;
            padding: 20px;
        }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        .header {{
            background: linear-gradient(135deg, #fb7299, #ff9eb5);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 24px;
            display: flex;
            align-items: center;
            gap: 20px;
        }}
        .avatar {{
            width: 80px;
            height: 80px;
            border-radius: 50%;
            border: 3px solid white;
            object-fit: cover;
        }}
        .header h1 {{ font-size: 24px; margin-bottom: 8px; }}
        .header p {{ opacity: 0.9; }}
        
        .cards {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }}
        .card {{
            background: white;
            padding: 24px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }}
        .card-label {{ color: #888; font-size: 14px; margin-bottom: 8px; }}
        .card-value {{ font-size: 28px; font-weight: bold; color: #333; }}
        .card-change {{ font-size: 13px; margin-top: 6px; }}
        .up {{ color: #e74c3c; }}
        .down {{ color: #27ae60; }}
        
        .section {{
            background: white;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }}
        .section-title {{
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 2px solid #f0f0f0;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid #f0f0f0;
        }}
        th {{
            background: #fafafa;
            font-weight: 600;
            color: #666;
            font-size: 14px;
        }}
        tr:hover {{ background: #fafafa; }}
        td {{ font-size: 14px; }}
        
        .chart-container {{
            display: flex;
            align-items: flex-end;
            justify-content: space-around;
            height: 250px;
            padding: 20px 0;
            border-bottom: 2px solid #eee;
        }}
        .chart-group {{
            display: flex;
            flex-direction: column;
            align-items: center;
            flex: 1;
            height: 100%;
        }}
        .chart-bars {{
            display: flex;
            align-items: flex-end;
            gap: 4px;
            height: 100%;
            flex: 1;
        }}
        .bar {{
            width: 20px;
            border-radius: 4px 4px 0 0;
            transition: height 0.3s;
        }}
        .bar-views {{ background: linear-gradient(to top, #fb7299, #ff9eb5); }}
        .bar-fans {{ background: linear-gradient(to top, #00a1d6, #6dd5ed); }}
        .chart-label {{ font-size: 12px; color: #888; margin-top: 8px; }}
        
        .legend {{
            display: flex;
            justify-content: center;
            gap: 24px;
            margin-top: 16px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 13px;
            color: #666;
        }}
        .legend-color {{
            width: 16px;
            height: 16px;
            border-radius: 4px;
        }}
        
        .footer {{
            text-align: center;
            color: #999;
            font-size: 13px;
            padding: 20px;
        }}
        
        @media (max-width: 768px) {{
            .cards {{ grid-template-columns: 1fr; }}
            .header {{ flex-direction: column; text-align: center; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <img src="{user_info['face']}" class="avatar" alt="头像">
            <div>
                <h1>{user_info['name']} · B站数据统计</h1>
                <p>更新时间：{latest['date']} | 共记录 {total} 次</p>
            </div>
        </div>
        
        <div class="cards">
            <div class="card">
                <div class="card-label">总播放量</div>
                <div class="card-value">{latest['views']:,}</div>
                <div class="card-change {'up' if latest['change']['views'] >= 0 else 'down'}">
                    较上次 {'+' if latest['change']['views'] >= 0 else ''}{latest['change']['views']:,}
                </div>
            </div>
            <div class="card">
                <div class="card-label">总点赞数</div>
                <div class="card-value">{latest['likes']:,}</div>
                <div class="card-change {'up' if latest['change']['likes'] >= 0 else 'down'}">
                    较上次 {'+' if latest['change']['likes'] >= 0 else ''}{latest['change']['likes']:,}
                </div>
            </div>
            <div class="card">
                <div class="card-label">粉丝数</div>
                <div class="card-value">{latest['fans']:,}</div>
                <div class="card-change {'up' if latest['change']['fans'] >= 0 else 'down'}">
                    较上次 {'+' if latest['change']['fans'] >= 0 else ''}{latest['change']['fans']:,}
                </div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">📈 数据趋势（最近12次）</div>
            <div class="chart-container">
                {chart_bars}
            </div>
            <div class="legend">
                <div class="legend-item">
                    <div class="legend-color" style="background: #fb7299;"></div>
                    <span>播放量</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #00a1d6;"></div>
                    <span>粉丝数</span>
                </div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">📊 历史数据明细</div>
            <table>
                <thead>
                    <tr>
                        <th>日期</th>
                        <th>播放量（变化）</th>
                        <th>点赞数（变化）</th>
                        <th>粉丝数（变化）</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            数据来源：B站公开API | 自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>"""
    
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

def main():
    print(f"开始获取 UID: {UID} 的数据...")
    
    # 获取当前数据
    user_info = get_user_info()
    stats = get_user_stats()
    
    current = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "views": stats["views"],
        "likes": stats["likes"],
        "fans": user_info["fans"]
    }
    
    print(f"粉丝数: {current['fans']:,}")
    print(f"播放量: {current['views']:,}")
    print(f"点赞数: {current['likes']:,}")
    
    # 加载历史数据
    history = load_history()
    
    # 检查今天是否已经记录过（同一天只记录一次）
    if history and history[-1]["date"] == current["date"]:
        print("今天已有记录，更新今日数据...")
        previous = history[-2] if len(history) >= 2 else None
        current["change"] = calc_change(current, previous)
        history[-1] = current
    else:
        # 计算变化量
        previous = history[-1] if history else None
        current["change"] = calc_change(current, previous)
        history.append(current)
        print(f"新增记录，共 {len(history)} 条")
    
    # 保存数据
    save_history(history)
    print(f"数据已保存到 {DATA_FILE}")
    
    # 生成HTML报告
    generate_html(history, user_info)
    print(f"报告已生成到 {REPORT_FILE}")
    print("✅ 完成！")

if __name__ == "__main__":
    main()

import requests
from bs4 import BeautifulSoup


from flask import Flask, render_template,request,make_response, jsonify



from datetime import datetime

import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

# 判斷是在 Vercel 還是本地
if os.path.exists('serviceAccountKey.json'):
    # 本地環境：讀取檔案
    cred = credentials.Certificate('serviceAccountKey.json')
else:
    # 雲端環境：從環境變數讀取 JSON 字串
    firebase_config = os.getenv('FIREBASE_CONFIG')
    cred_dict = json.loads(firebase_config)
    cred = credentials.Certificate(cred_dict)

firebase_admin.initialize_app(cred)


app = Flask(__name__)

@app.route("/")
def index():
    link = "<h1>歡迎來到陳芯霈的網站0514</h1><hr>"
    link += "<a href=/mis>課程</a><hr>"
    link += "<a href=/today>時間</a><hr>"
    link += "<a href=/me>關於我</a><hr>"
    link += "<a href=/welcome?u=芯霈&d=靜宜資管&c=資訊管理導論>get傳值</a><hr>"    
    link += "<a href=/account>POST傳值</a><hr>"
    link += "<a href=/math>次方與根號計算</a><hr>"
    link += "<br><a href=/read>讀取Firestore資料</a><br>"
    link += "<br><a href=/read3>讀取Firestore資料(關鍵字)</a><br>"
    link += "<br><a href=/read2>讀取Firestore資料(根據姓名關鍵字)</a><br>"
    link += "<br><a href='/spider'>執行爬蟲 (課程資料)</a><hr>"
    link += "<br><a href='/movie1'>爬蟲即將上映電影</a><hr>"
    link += "<br><a href='/spiderMovie'>爬取並更新電影資料</a><hr>"
    link += "<br><a href='/searchMovie'>搜尋資料庫中的電影</a><hr>"
    link += "<br><a href='/road1'>台中市十大肇事路口案件</a><hr>"
    link += "<br><a href='/road'>台中市十大肇事路口查詢</a><hr>"
    link += "<br><a href='/weather'>天氣預報查詢</a><hr>"
    link += "<br><a href='/rate'>本週新片</a><hr>"


    return link

@app.route("/webhook", methods=["POST"])
def webhook():
    req = request.get_json(force=True)
    action = req["queryResult"]["action"]
    
    if action == "rateChoice":
        rate = req["queryResult"]["parameters"]["rate"]
        
        db = firestore.client()
        collection_ref = db.collection("本週新片含分級")
        docs = collection_ref.where("rate", "==", rate).get()
        
        res = f"我是陳芯霈設計的機器人，為您找出的本週 {rate} 電影有：\n"
        found = False
        for doc in docs:
            found = True
            m = doc.to_dict()
            res += f"- {m.get('title')} (片長：{m.get('showLength')} 分)\n"
        
        if not found:
            res = f"抱歉，本週資料庫中沒有標記為 {rate} 的電影喔！"
            
        return make_response(jsonify({"fulfillmentText": res}))

    return make_response(jsonify({"fulfillmentText": "Webhook 運作正常，但未觸發特定動作。"}))


@app.route("/rate")
def rate():
    #本週新片
    url = "https://www.atmovies.com.tw/movie/new/"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    lastUpdate = sp.find(class_="smaller09").text[5:]
    print(lastUpdate)
    print()

    result=sp.select(".filmList")

    for x in result:
        title = x.find("a").text
        introduce = x.find("p").text

        movie_id = x.find("a").get("href").replace("/", "").replace("movie", "")
        hyperlink = "http://www.atmovies.com.tw/movie/" + movie_id
        picture = "https://www.atmovies.com.tw/photo101/" + movie_id + "/pm_" + movie_id + ".jpg"

        r = x.find(class_="runtime").find("img")
        rate = ""
        if r != None:
            rr = r.get("src").replace("/images/cer_", "").replace(".gif", "")
            if rr == "G":
                rate = "普遍級"
            elif rr == "P":
                rate = "保護級"
            elif rr == "F2":
                rate = "輔12級"
            elif rr == "F5":
                rate = "輔15級"
            else:
                rate = "限制級"

        t = x.find(class_="runtime").text

        t1 = t.find("片長")
        t2 = t.find("分")
        showLength = t[t1+3:t2]

        t1 = t.find("上映日期")
        t2 = t.find("上映廳數")
        showDate = t[t1+5:t2-8]

        doc = {
            "title": title,
            "introduce": introduce,
            "picture": picture,
            "hyperlink": hyperlink,
            "showDate": showDate,
            "showLength": int(showLength),
            "rate": rate,
            "lastUpdate": lastUpdate
        }

        db = firestore.client()
        doc_ref = db.collection("本週新片含分級").document(movie_id)
        doc_ref.set(doc)
    return "本週新片已爬蟲及存檔完畢，網站最近更新日期為：" + lastUpdate

@app.route("/weather", methods=["GET", "POST"])
def weather():
    result = ""
    city = request.values.get("city", "臺中市")
    city = city.replace("台", "臺")
    
    if request.method == "POST" or request.values.get("city"):
        token = "rdec-key-123-45678-011121314" # 請確保 token 正確
        url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization={token}&format=JSON&locationName={city}"
        
        try:
            data = requests.get(url, timeout=10)
            json_data = data.json()
            loc_data = json_data["records"]["location"][0]
            weather_state = loc_data["weatherElement"][0]["time"][0]["parameter"]["parameterName"]
            rain_rate = loc_data["weatherElement"][1]["time"][0]["parameter"]["parameterName"]
            result = f"<h3>{city} 目前天氣：{weather_state}，降雨機率：{rain_rate}%</h3>"
        except:
            result = "<p style='color:red;'>查無此縣市資料或 API Token 失效。</p>"

    html = f"""
    <h2>縣市天氣查詢</h2>
    <form action="/weather" method="get">
        請輸入縣市名稱：<input type="text" name="city" placeholder="例如：臺中市">
        <button type="submit">查詢</button>
    </form>
    {result}
    <br><a href="/">返回首頁</a>
    """
    return html

import time # 記得在程式最上方 import time

@app.route("/road", methods=["GET", "POST"])
def road():
    q = request.values.get("q")
    results = ""
    
    if q:
        url = "https://datacenter.taichung.gov.tw/swagger/OpenData/a1b899c0-511f-4e3d-b22b-814982a97e41"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Referer': 'https://datacenter.taichung.gov.tw/',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        max_retries = 3  # 最多重試 3 次
        for i in range(max_retries):
            try:
                # verify=False 跳過 SSL 檢查，有時能解決斷連問題
                # 使用 requests 直接連線
                response = requests.get(url, headers=headers, timeout=15, verify=False)
                response.encoding = 'utf-8'
                
                if response.status_code == 200:
                    json_data = response.json()
                    found = False
                    results = "<h3>查詢結果：</h3><table border='1' style='border-collapse: collapse; width:100%;'>"
                    results += "<tr style='background-color:#e6f3ff;'><th>路口名稱</th><th>件數</th><th>主要肇因</th></tr>"
                    
                    for item in json_data:
                        if q in item.get("路口名稱", ""):
                            found = True
                            results += f"<tr><td>{item['路口名稱']}</td><td>{item['總件數']}</td><td>{item['主要肇因']}</td></tr>"
                    results += "</table>"
                    
                    if not found:
                        results = f"<p style='color:orange;'>查無關於「{q}」的資料。</p>"
                    break # 成功抓到資料，跳出重試迴圈
                
            except Exception as e:
                if i < max_retries - 1:
                    time.sleep(1) # 失敗後等一秒再試
                    continue
                else:
                    results = f"<div style='color:red;'>連線失敗第 {i+1} 次：{str(e)}<br>目前政府伺服器拒絕您的 IP 連線，建議換個網路試試看。</div>"

    html = f"""
    <h1>台中市易肇事路口查詢(陳芯霈)</h1>
    <form action="/road" method="get">
        請輸入路名：<input type="text" name="q" value="{q if q else ''}">
        <button type="submit">查詢</button>
    </form>
    <hr>
    {results}
    <br><a href="/">返回首頁</a>
    """
    return html

@app.route("/road1", methods=["GET", "POST"])
def road1():
    # 建立網頁標題與基礎 HTML
    R = "<h1>十大肇事路口(113年10月)(陳芯霈)</h1><br>"
   
    import requests, json
    import urllib3
    from flask import request

    # 隱藏 SSL 安全警告（因為我們會使用 verify=False）
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    url = "https://datacenter.taichung.gov.tw/swagger/OpenData/a1b899c0-511f-4e3d-b22b-814982a97e41"
   
    # 模擬更完整的瀏覽器標頭
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json'
    }
   
    try:
        # verify=False 解決憑證問題, timeout=10 防止卡死
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        response.encoding = 'utf-8' # 確保中文不變亂碼
       
        # 轉換 JSON
        JsonData = response.json()
       
        # 從網址取得 q 參數，例如：/road?q=中科路
        Road_query = request.args.get("q", "")

        found = False
        for item in JsonData:
            # 判斷路口名稱是否包含搜尋關鍵字
            if Road_query in item.get("路口名稱", ""):
                # 注意：這裡使用 f-string 時，item['路口名稱'] 要用單引號，外面用雙引號
                R += f"<b>{item['路口名稱']}</b>，原因：{item['主要肇因']} <br>"
                found = True
       
        if not found:
            if Road_query == "":
                R += "<i>請在網址後加上 ?q=路名 來搜尋，或查看下方所有列表：</i><br><br>"
                # 如果沒搜關鍵字，也可以考慮顯示前幾筆或全部
                for item in JsonData[:10]: # 先顯示前10筆示範
                    R += f"{item['路口名稱']} <br>"
            else:
                R += f"抱歉，查無關於「{Road_query}」的相關資料！<br>"
    except Exception as e:
        R += f"<div style='color:red;'>連線錯誤：{str(e)}</div>"

    R += "<br><hr><a href='/'>回首頁</a>"
    return R


@app.route("/searchMovie", methods=["GET", "POST"])
def searchMovie():
    q = request.values.get("q")
    db = firestore.client()
    collection_ref = db.collection("即將上映電影")
    docs = collection_ref.get()

    # 標題與搜尋表單
    R = "<h1>資料庫電影查詢</h1>"
    
    # 這裡加入一個提示訊息，顯示目前是在查看資料庫資料
    if q:
        R += f"<p style='color:green;'><b>已完成「{q}」的關鍵字查詢：</b></p>"
    else:
        R += "<p style='color:blue;'><b>目前顯示資料庫內所有電影資料：</b></p>"

    R += f"""
    <form action="/searchMovie" method="get">
        <input type="text" name="q" placeholder="輸入片名關鍵字" value="{q if q else ''}">
        <button type="submit">搜尋</button>
    </form><hr>
    """

    # 建立表格標題
    R += "<table border='1' style='border-collapse: collapse; width:100%; text-align:center;'>"
    R += "<tr><th>編號</th><th>海報</th><th>片名</th><th>上映日期</th><th>介紹頁</th></tr>"

    found_count = 0
    for doc in docs:
        m = doc.to_dict()
        if not q or q in m.get("title", ""):
            found_count += 1
            R += f"""
            <tr>
                <td>{found_count}</td>
                <td><img src="{m.get('image')}" width="100"></td>
                <td>{m.get('title')}</td>
                <td>{m.get('release_date')}</td>
                <td><a href="{m.get('link')}" target="_blank">點我觀看</a></td>
            </tr>
            """
    
    R += "</table>"

    # 如果完全沒找到資料的顯示
    if found_count == 0:
        if q:
            R = f"<h1>查詢結果</h1><p>找不到關於「{q}」的電影。</p>"
        else:
            R = f"<h1>查詢結果</h1><p>資料庫目前空空如也，請先執行爬蟲存入資料。</p>"
    
    R += "<br><a href='/'>回首頁</a>"
    return R
@app.route("/spiderMovie")
def spiderMovie():
    url = "https://www.atmovies.com.tw/movie/next/"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    result = sp.select(".filmListAllX li")

    db = firestore.client()
    collection_ref = db.collection("即將上映電影")
    
    count = 0
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for item in result:
        try:
            # 擷取資料
            name = item.find("img").get("alt")
            link = "https://www.atmovies.com.tw" + item.find("a").get("href")
            img = "https://www.atmovies.com.tw" + item.find("img").get("src")
            # 抓取上映日期文字
            date_text = item.get_text().split("上映日期：")[-1].strip() if "上映日期：" in item.get_text() else "尚未公佈"
            
            # 寫入資料庫
            doc_data = {
                "title": name,
                "link": link,
                "image": img,
                "release_date": date_text,
                "update_time": now
            }
            # 使用 set (若片名相同會覆蓋更新，不重複建立)
            collection_ref.document(name).set(doc_data)
            count += 1
        except:
            continue

    return f"<h1>爬蟲任務完成</h1><p>最近更新日期：{now}</p><p>共爬取並存儲了 {count} 部電影資料。</p><br><a href='/'>回首頁</a>"

@app.route("/movie1")
def movie():
    q = request.args.get("q")

    url = "https://www.atmovies.com.tw/movie/next/"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    result = sp.select(".filmListAllX li")

    R = "<h1>即將上映電影查詢</h1>"
    R += f"""
    <form action="/movie1" method="get">
        <input type="text" name="q" placeholder="輸入片名關鍵字" value="{q if q else ''}">
        <button type="submit">搜尋</button>
    </form>
    <hr>
    """

    found_count = 0
    for item in result:
        try:
            alt_text = item.find("img").get("alt")
            
            if not q or q in alt_text:
                found_count += 1
                R += "電影名稱：" + alt_text + "<br>"
                R += "介紹連結：<a href='https://www.atmovies.com.tw" + item.find("a").get("href") + "'>點我觀看</a><br>"
                R += "<img src='https://www.atmovies.com.tw" + item.find("img").get("src") + "' width='150'><br><br>"
        except:
            continue

    if found_count == 0 and q:
        R += f"找不到關於「{q}」的電影。<br>"
    
    R += "<br><a href='/'>回首頁</a>"
    return R 

@app.route("/spider")
def spider():
    url = "https://www1.pu.edu.tw/~tcyang/course.html"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    
    sp = BeautifulSoup(Data.text, "html.parser")
    result = sp.select(".team-box a") 
    
    content = "<h2>子青老師課程爬蟲結果</h2>"
    content += "<table border='1'><tr><th>課程名稱</th><th>課程連結</th></tr>"
    
    for i in result:
        name = i.text
        link = i.get("href")
        content += f"<tr><td>{name}</td><td><a href='{link}' target='_blank'>{link}</a></td></tr>"
    
    content += "</table>"
    content += "<br><a href='/'>返回首頁</a>"
    
    return content
@app.route("/read2", methods=["GET", "POST"])
def read2():
    if request.method == "POST":
        keyword = request.form.get("keyword")
        db = firestore.client()
        collection_ref = db.collection("靜宜資管")
        docs = collection_ref.get()
        
        results = []
        for doc in docs:
            teacher = doc.to_dict()
            if "name" in teacher and keyword in teacher["name"]:
                results.append(teacher)
        
        return render_template("searchteacher.html", keyword=keyword, results=results)
    
    return render_template("searchteacher.html", keyword=None, results=None)
        
    return Result

@app.route("/read3")
def read3():
    Result = ""
    keyword = "楊"
    db = firestore.client()
    collection_ref = db.collection("靜宜資管")
    docs = collection_ref.get()
    for doc in docs:        
        teacher = doc.to_dict()
        if "name" in teacher and keyword in teacher["name"]:
            Result += f"姓名：{teacher.get('name')}，研究室：{teacher.get('lab')}，郵件：{teacher.get('mail')}<br>"
   
    if Result == "":
        Result = "抱歉查無此關鍵字姓名之老師資料"
   
    return Result + "<br><a href=/>返回首頁</a>"

@app.route("/read")
def read():
    Result = ""
    db = firestore.client()
    collection_ref = db.collection("靜宜資管")    
    docs = collection_ref.get()    
    
    data_list = []
    for doc in docs:
        data_list.append(doc.to_dict())
    
    sorted_data = sorted(data_list, key=lambda x: x.get('lab', 0), reverse=True)
    
    for item in sorted_data:
        Result += str(item) + "<br>"
        
    return Result

@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1><a href=/>返回首頁</a>"

@app.route("/today")
def today():
    now = datetime.now()
    return render_template("today.html", datetime = str(now))

@app.route("/me")
def me():
    return render_template("2026b.html")


@app.route("/welcome", methods=["GET"])
def welcome():
    user = request.values.get("u")
    d = request.values.get("d")
    c = request.values.get("c")
    return render_template("welcome.html",name = user,dep = d,course = c)

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form["user"]
        pwd = request.form["pwd"]
        result = "您輸入的帳號是：" + user + "; 密碼為：" + pwd 
        return result
    else:
        return render_template("account.html")

@app.route("/math", methods=["GET", "POST"])
def math():
    result = None
    if request.method == "POST":
        try:
            x = float(request.form.get("x"))
            y = float(request.form.get("y"))
            opt = request.form.get("opt")

            if opt == "∧":
                result = x ** y
            elif opt == "√":
                if y == 0:
                    result = "錯誤：數學上不能開 0 次方"
                else:
                    result = x ** (1/y)
            else:
                result = "請選擇正確的運算符號"
        except ValueError:
            result = "請輸入有效的數字"

    return render_template("math.html", result=result)






if __name__ == "__main__":
    app.run(debug=True)

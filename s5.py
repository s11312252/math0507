import requests
from bs4 import BeautifulSoup
url = "https://flask2026b-xcj1.vercel.app/me"
Data = requests.get(url)
Data.encoding = "utf-8"

print(Data.text)
sp = BeautifulSoup(Data.text, "html.parser")
result=sp.find("td iframe")
for item in result:
	print(item.get("src"))



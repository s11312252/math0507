import requests
from bs4 import BeautifulSoup
url = "https://flask2026b-xcj1.vercel.app/me"
Data = requests.get(url)
Data.encoding = "utf-8"

print(Data.text)
sp = BeautifulSoup(Data.text, "html.parser")
result=sp.select("td")
print(result)

for i in result:
	print(item)
	print()
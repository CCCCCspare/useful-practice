import requests
import time
from lxml import etree


def main():
    url = "https://movie.douban.com/top250"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0"
    }
    for i in range(0, 250, 25):
        params = {
            "start": i,
            "filter": "",
        }
        response = requests.get(url, headers=headers, params=params)
        page_text = response.text
        tree = etree.HTML(page_text)
        li_list = tree.xpath(
            '/html/body/div[3]/div[1]/div/div[1]/ol/li//div[@class="hd"]/a/span[1]/text()'
        )
        print(response.status_code)
        print("-----------------------------")
        print(li_list)
        print("-----------------------------")
        with open("./douban.txt", "a", encoding="utf-8") as f:
            for li in li_list:
                f.write(li + "\n")
        print(f"第{i//25 + 1}页爬取完成")
        time.sleep(1)


if __name__ == "__main__":
    main()

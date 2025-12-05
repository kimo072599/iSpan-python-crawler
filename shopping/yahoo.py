from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import os
import json

# 設定 Chrome 瀏覽器的選項
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized") # Chrome 瀏覽器在啟動時最大化視窗
options.add_argument("--incognito") # 無痕模式
options.add_argument("--disable-popup-blocking") # 停用 Chrome 的彈窗阻擋功能。

# 建立 Chrome 瀏覽器物件
driver = webdriver.Chrome(options=options)
driver.get("https://tw.buy.yahoo.com/")

def scroll_down_slowly():

    last_height = driver.execute_script("return window.scrollY")
    page_height = driver.execute_script("return document.body.scrollHeight")

    while last_height < page_height:
        # 滾動一步
        driver.execute_script(f"window.scrollBy(0, 400);")

        # 等待 lazy-load 元素載入
        time.sleep(0.3)

        # 更新目前高度與頁面總高度(總高度會因為載入變高)
        new_height = driver.execute_script("return window.scrollY")
        page_height = driver.execute_script("return document.body.scrollHeight")

        # 沒繼續滾動就代表到底了
        if new_height == last_height:
            break

        last_height = new_height

all_item_info = []
def get_item_info():
    print("正在取得該頁資訊...")
    item_list = driver.find_elements(By.CSS_SELECTOR, "ul.gridList > a")
    for item in item_list:
        try:
            item_name = item.find_element(By.CSS_SELECTOR,".sc-1drl28c-4 > span").text
        except Exception:
            item_name = "找不到商品名稱"
            with open("error_log.txt", "a", encoding="utf-8") as f:
                f.write(f"商品名稱缺失:{e}")
        try:
            item_pics = item.find_elements(By.CSS_SELECTOR,".swiper-wrapper img")
            item_img_url_list = []
            for item_img in item_pics:
                item_img_url = item_img.get_attribute("src")
                item_img_url_list.append(item_img_url)
        except Exception:
            item_img_url_list = "找不到圖片"
            with open("error_log.txt", "a", encoding="utf-8") as f:
                f.write(f"{item_name}:圖片:{e}")
        try:
            item_cost = item.find_element(By.CSS_SELECTOR,".sc-KLvxH.gYDCaI > span").text
        except Exception:
            item_cost = item.find_element(By.CSS_SELECTOR,".sc-gKcDdr.sc-jMupca.kwvRcF.gAgQoV").text
        except Exception as e:
            item_cost = "找不到商品價格"
            with open("error_log.txt", "a", encoding="utf-8") as f:
                f.write(f"{item_name}:價格:{e}")
        try:
            purchase_link = item.get_attribute("href")
        except Exception:
            purchase_link = "找不到購買連結"
            with open("error_log.txt", "a", encoding="utf-8") as f:
                f.write(f"{item_name}:連結:{e}")

        item_info = {
            "item_name" : item_name,
            "item_cost" : item_cost,
            "item_img_url_list" : item_img_url_list,
            "purchase_link" : purchase_link
        }
        all_item_info.append(item_info)

def get_all_info(search_product : str, pages : int, sort: str = "最相關"):
    input_box = driver.find_element(By.CSS_SELECTOR, "form input[type='search']")
    input_box.send_keys(Keys.CONTROL, "a")
    input_box.send_keys(Keys.DELETE)
    input_box.send_keys(search_product)
    driver.find_element(By.CSS_SELECTOR, "form button[type='submit']").click()
    print(f"正在搜索{search_product}")

    # 檢查是否有商品
    time.sleep(1)
    item_list = driver.find_elements(By.CSS_SELECTOR, "ul.gridList > a")
    if len(item_list) == 0:
        print("無此商品")
        log = {search_product:"無此商品"}
        if not os.path.exists("shopping/yahoo購物中心"):
            os.mkdir(f"shopping/yahoo購物中心")
        with open(f"shopping/yahoo購物中心/{search_product}資料.json", "w", encoding="utf-8") as f:
            json.dump(log, f, indent=4, ensure_ascii=False)
    else:
        # 排序方式
        newest = driver.find_elements(By.CSS_SELECTOR, ".SortBar_popup_1UvPW a")[0].get_attribute("href")
        higher_rating = driver.find_elements(By.CSS_SELECTOR, ".SortBar_popup_1UvPW a")[1].get_attribute("href")
        from_lowprice = driver.find_elements(By.CSS_SELECTOR, ".SortBar_sortBtns_RCto5 > a")[0].get_attribute("href")
        from_highprice = driver.find_elements(By.CSS_SELECTOR, ".SortBar_sortBtns_RCto5 > a")[1].get_attribute("href")
        most_hot_sale = driver.find_elements(By.CSS_SELECTOR, ".SortBar_sortBtns_RCto5 > a")[2].get_attribute("href")
        method = {
            "最相關" : None,
            "最新上架" : newest,
            "評價" : higher_rating,
            "價格低到高" : from_lowprice,
            "價格高到低" : from_highprice,
            "近期熱銷" : most_hot_sale
        }
        sort_method = method[sort]
        if sort_method != None:
            driver.get(sort_method)
            print(f"已以{sort}排序")

        # 查詢第一頁
        time.sleep(1)
        print("正在查詢第 1 頁")
        scroll_down_slowly()
        get_item_info()

        # 查詢後續頁
        for i in range(pages-1):
            page_numbers = driver.find_elements(By.CSS_SELECTOR, ".Pagination__numberContainer___2oWVw a")
            for page_number in page_numbers:
                if page_number.text == str(i+2):
                    page_number.click()
                    print(f"正在查詢第 {i+2} 頁")
                    time.sleep(1)
                    scroll_down_slowly()
                    get_item_info()

        if not os.path.exists("shopping/yahoo購物中心"):
            os.mkdir(f"shopping/yahoo購物中心")

        with open(f"shopping/yahoo購物中心/{search_product}資料.json", "w", encoding="utf-8") as f:
            json.dump(all_item_info, f, indent=4, ensure_ascii=False)
    

if __name__ == "__main__":
    # 第一個參數：欲查詢的商品名稱
    # 第二個參數：欲查詢的總頁數
    # 第三個參數：排序方式，預設為"最相關"，另可填入"最新上架"、"評價"、"價格低到高"、"價格高到低"、"近期熱銷"
    get_all_info("皮夾", 3, "最新上架")
    get_all_info("點滴", 3) # 實際上只有兩頁，填入超過的頁數不影響
    get_all_info("阿姆斯特朗旋風噴射阿姆斯特朗砲", 3) # 無此商品
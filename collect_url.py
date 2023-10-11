import json
import os.path as osp
import platform
import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.chrome.service import Service
import pickle


class CollectLinks:
    def __init__(self, no_gui=False, proxy=None):
        executable = ''

        if platform.system() == 'Windows':
            print('Detected OS : Windows')
            executable = 'window\chromedriver.exe'
        elif platform.system() == 'Linux':
            print('Detected OS : Linux')
            executable = 'linux\chromedriver'
        elif platform.system() == 'Darwin':
            print('Detected OS : Mac')
            executable = 'chromedriver_mac'
        else:
            raise OSError('Unknown OS Type')

        if not osp.exists(executable):
            raise FileNotFoundError(
                'Chromedriver file should be placed at {}'.format(executable))

        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        if no_gui:
            chrome_options.add_argument('--headless')
        if proxy:
            chrome_options.add_argument("--proxy-server={}".format(proxy))
        self.browser = webdriver.Chrome(
            service=Service(executable), options=chrome_options)

        browser_version = 'Failed to detect version'
        chromedriver_version = 'Failed to detect version'
        major_version_different = False

        if 'browserVersion' in self.browser.capabilities:
            browser_version = str(self.browser.capabilities['browserVersion'])

        if 'chrome' in self.browser.capabilities:
            if 'chromedriverVersion' in self.browser.capabilities['chrome']:
                chromedriver_version = str(
                    self.browser.capabilities['chrome']['chromedriverVersion']).split(' ')[0]

        if browser_version.split('.')[0] != chromedriver_version.split('.')[0]:
            major_version_different = True

        print('_________________________________')
        print('Current web-browser version:\t{}'.format(browser_version))
        print('Current chrome-driver version:\t{}'.format(chromedriver_version))
        if major_version_different:
            print('warning: Version different')
            print(
                'Download correct version at "http://chromedriver.chromium.org/downloads" and place in "./chromedriver"')
        print('_________________________________')

    def login_shopee(self):
        txtUser = self.browser.find_element(By.XPATH, "//input[@type='text']")
        txtUser.send_keys("")  # username

        txtPassword = self.browser.find_element(
            By.XPATH, "//input[@type='password']")
        txtPassword.send_keys("")  # password

        txtPassword.send_keys(Keys.ENTER)
        time.sleep(20)

    def extract_item_shopee(self, html_doc):
        list_item = []
        soup = BeautifulSoup(html_doc, 'html.parser')
        items = soup.find_all(
            class_="col-xs-2-4 shopee-search-item-result__item")
        for item in items:
            item_name = item.find_all(class_="APSFjk cB928k skSW9t")
            if item_name:
                item_info = {
                    "name": item_name[0].decode_contents().strip(),
                    "sold_per_month": 0,
                    "url": ""
                }
                item_quantity_sold = item.find_all(class_="QE5lnM _2pKDjP")
                item_link = item.find("a")["href"]
                if item_quantity_sold:
                    item_info["sold_per_month"] = item_quantity_sold[0].decode_contents(
                    ).strip()
                item_info["url"] = f"https://shopee.vn{item_link}"
                list_item.append(item_info)

        return list_item

    def shopee(self, url, count=0):
        if count == 0:
            self.browser.get(
                'https://shopee.vn/buyer/login?next=https%3A%2F%2Fshopee.vn%2F')
            self.login_shopee()
            self.browser.maximize_window()
            time.sleep(20)

        self.browser.get(url)

        time.sleep(20)

        print(f'Scrolling down')
        result = []

        number_pages = int(self.browser.find_element(
            By.XPATH, "//span[@class='shopee-mini-page-controller__total']").text)

        try:
            for pages in range(number_pages):
                print(f"Page {pages}")
                try:
                    elem = self.browser.find_element(By.TAG_NAME, "body")
                    for _ in range(8):
                        elem.send_keys(Keys.PAGE_DOWN)
                        time.sleep(1)

                    full_page_html = self.browser.page_source
                    with open("full_page_html.html", "w", encoding='utf-8') as file:
                        file.write(str(full_page_html))
                    items = self.extract_item_shopee(full_page_html)
                    result.extend(items)

                    time.sleep(1)

                except Exception as e:
                    print(e)
                    print("One page error occured")

                if pages != number_pages - 1:
                    elem.send_keys(Keys.HOME)
                    # elem.send_keys(Keys.PAGE_DOWN)
                    self.browser.find_element(
                        By.XPATH, "//button[@class='shopee-button-outline shopee-mini-page-controller__next-btn']").click()
                else:
                    break

                time.sleep(3)

        except Exception as es:
            print(es)

        alist = []
        with open("result/dien_thoai.json", 'r', encoding='utf-8') as file:
            try:
                data = json.load(file)
            except Exception as es:
                data = []
            alist.extend(data)
            alist.extend(result)

        with open("result/dien_thoai.json", 'w', encoding='utf-8') as file:
            json.dump(alist, file, ensure_ascii=False, indent=4)

        # self.browser.close()


if __name__ == '__main__':
    collect = CollectLinks(no_gui=False)
    brand_id = ['1147183', '1695294', '1695289',
                '1695285', '1695293', '1695303', '1189223',
                '1802107', '1146548', '3256181', '1695277',
                '1695351', '2340796', '1132161', '1146277',
                '1802344', '1695278', '1695342', '3819716', '1077919']

    count = 0
    for id in brand_id[5:]:
        url = f"https://shopee.vn/%C4%90i%E1%BB%87n-tho%E1%BA%A1i-cat.11036030.11036031?brands={id}&page=0&sortBy=sales"
        collect.shopee(url, count)
        print(f"Done {id}")
        count += 1

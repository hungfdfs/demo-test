
import time
import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

class FacebookCommentCrawler:
    def __init__(self, chrome_driver_path, cookies_file):
        self.chrome_driver_path = chrome_driver_path
        self.cookies_file = cookies_file
        self.driver = None
        self.comments_data = []

    def setup_driver(self):
        """Khởi động trình duyệt Selenium"""
        chrome_options = Options()
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")

        service = Service(self.chrome_driver_path)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def load_cookies(self):
        """Đăng nhập vào Facebook bằng cookies"""
        self.driver.get("https://www.facebook.com/")
        time.sleep(3)

        with open(self.cookies_file, "r") as f:
            cookies = json.load(f)
            for cookie in cookies:
                self.driver.add_cookie(cookie)

        self.driver.refresh()
        time.sleep(5)
        print("✅ Đăng nhập thành công!")

    def get_all_post_urls(self, page_id, max_posts=50):
        """Lấy danh sách bài viết từ fanpage"""
        post_urls = set()
        page_url = f"https://www.facebook.com/{page_id}"
        self.driver.get(page_url)
        time.sleep(5)

        last_height = self.driver.execute_script("return document.body.scrollHeight")

        while len(post_urls) < max_posts:
            try:
                posts = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/posts/')]")
                for post in posts:
                    try:
                        url = post.get_attribute("href").split("?")[0]
                        post_urls.add(url)
                    except:
                        continue
                
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break  # Đã cuộn đến cuối trang, không còn bài mới
                last_height = new_height

            except:
                print("🔄 Lỗi khi lấy bài viết, đang refresh lại...")
                self.driver.refresh()
                time.sleep(5)

            if len(post_urls) >= max_posts:
                break
        
        print(f"🔎 Lấy được {len(post_urls)} bài viết")
        return list(post_urls)

    def expand_all_comments(self):
        """Nhấn nút 'Xem thêm bình luận' để tải toàn bộ bình luận"""
        while True:
            try:
                more_comments_button = self.driver.find_element(By.XPATH, "//span[contains(text(), 'Xem thêm bình luận')]")
                self.driver.execute_script("arguments[0].click();", more_comments_button)
                time.sleep(3)
            except:
                break

    def get_comments_from_post(self, post_url):
        """Lấy tất cả bình luận từ bài viết"""
        self.driver.get(post_url)
        time.sleep(5)

        self.expand_all_comments()  # Tải hết bình luận trước khi lấy dữ liệu

        comments_elements = self.driver.find_elements(By.XPATH, "//div[contains(@aria-label, 'Bình luận')]")

        for comment in comments_elements:
            try:
                commenter_element = comment.find_element(By.XPATH, ".//a")
                commenter_name = commenter_element.text
                username = commenter_element.get_attribute("href").split("?")[0]

                comment_text_element = comment.find_elements(By.XPATH, ".//div[2]//span")
                comment_text = " ".join([c.text for c in comment_text_element if c.text.strip()])

                try:
                    reactions_element = comment.find_element(By.XPATH, ".//span[contains(@aria-label, 'lượt thích')]")
                    reactions_count = int(reactions_element.text) if reactions_element.text.isdigit() else 0
                except:
                    reactions_count = 0

                comment_date = "Không xác định"

                self.comments_data.append({
                    'username': username,
                    'commenter_name': commenter_name,
                    'post_url': post_url,
                    'comment_date': comment_date,
                    'comment_text': comment_text,
                    'comment_reactions': reactions_count
                })
            except:
                continue

        print(f"💬 Thu thập {len(comments_elements)} bình luận từ {post_url}")
    
    def crawl_fanpage(self, page_id, max_posts=200):
        """Crawl tất cả bình luận từ fanpage"""
        self.setup_driver()
        self.load_cookies()

        post_urls = self.get_all_post_urls(page_id, max_posts)

        for post_url in post_urls:
            self.get_comments_from_post(post_url)
            time.sleep(2)

        output_file = f"facebook_comments_{page_id}.xlsx"
        df = pd.DataFrame(self.comments_data)
        df.to_excel(output_file, index=False)

        print(f"✅ Crawl hoàn tất! Dữ liệu đã lưu vào {output_file}")
        self.driver.quit()

if __name__ == "__main__":
    chrome_driver_path = "F:/chromedriver-win64/chromedriver.exe"
    cookies_file = "cookies.json"
    page_id = "bistar.ecopark"

    crawler = FacebookCommentCrawler(chrome_driver_path, cookies_file)
    crawler.crawl_fanpage(page_id, max_posts=200)

 
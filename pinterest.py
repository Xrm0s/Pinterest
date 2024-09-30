import os
import time
import requests
import cv2
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException

class PinterestScraper:
    def __init__(self):
        self.image_urls = set()

    def setup_browser(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")  
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.set_page_load_timeout(60)  
        return driver

    def scroll_and_collect_images(self, driver, keyword, num_images, timeout=180):
        search_url = f"https://www.pinterest.com/search/pins/?q={keyword}&rs=typed"
        driver.get(search_url)

        start_time = time.time()
        while len(self.image_urls) < num_images:
            if time.time() - start_time > timeout:
                print("Timeout reached, stopping image collection.")
                break
            
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3) 

            images = driver.find_elements(By.TAG_NAME, "img")

            for img in images:
                try:
                    src = img.get_attribute('src')
                    if src and "https://i.pinimg.com" in src:
                        self.image_urls.add(src)
                except StaleElementReferenceException:
                    continue

            if len(self.image_urls) >= num_images:
                break

    def download_images(self, folder_name):
        if not os.path.exists(folder_name):
            os.mkdir(folder_name)

        for idx, url in enumerate(self.image_urls):
            response = requests.get(url, stream=True)
            img_arr = np.asarray(bytearray(response.content), dtype="uint8")
            image = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)

            if image is not None:
                file_path = os.path.join(folder_name, f"image_{idx}.jpg")
                cv2.imwrite(file_path, image)

    def start(self, keyword, num_images):
        driver = self.setup_browser()
        try:
            self.scroll_and_collect_images(driver, keyword, num_images)
        except TimeoutException:
            print(f"Page load timeout for keyword {keyword}")
        finally:
            driver.quit()

        print(f"Collected {len(self.image_urls)} images.")
        if self.image_urls:
            self.download_images(keyword)
        else:
            print("No images were found.")

if __name__ == "__main__":
    keyword = input("Enter the keyword to search: ")
    num_images = int(input("Enter the number of images to download: "))

    scraper = PinterestScraper()
    scraper.start(keyword, num_images)

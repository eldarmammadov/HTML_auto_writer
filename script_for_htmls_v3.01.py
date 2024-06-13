from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

camera_name_list = "DS-2CD2H23G2-IZS"

def setup_driver():
    options = Options()
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def navigate_to_site(driver):
    driver.get("https://www.hikvision.com")
    driver.maximize_window()
    time.sleep(10)

def accept_cookies(driver):
    try:
        accept_box = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "gdpr-button"))
        )
        accept_box.click()
        print('Accepted all cookies')
    except Exception as e:
        print("GDPR accept button was not interactable:", e)

def perform_search(driver, query):
    try:
        search_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "search"))
        )
        search_btn.click()
        print('Search button was clicked')

        search_box = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "headerSerachInput"))
        )
        search_box.send_keys(query)
        search_box.send_keys(Keys.ENTER)
        print('Entered text in search box')
    except Exception as e:
        print('Search process failed:', e)

def get_search_results(driver):
    try:
        filter_search_content = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "filter-search-content"))
        )
        print(filter_search_content.text)
        try:
            following_span = filter_search_content.find_element(By.XPATH, "following-sibling::span")
            result_text = following_span.text
        except:
            parent_element = filter_search_content.find_element(By.XPATH, "..")
            following_span = parent_element.find_element(By.XPATH, ".//span")
            result_text = following_span.text
        print(f'Result text: {result_text}')
        return result_text
    except Exception as e:
        print('Result not found:', e)
        return None

def process_result_text(result_text):
    try:
        result_text = int(result_text)
        return result_text != 0
    except ValueError as e:
        print('Result text is not an integer:', e)
        return False

def scrape_product_details(driver):
    filter_search_result_title = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.CLASS_NAME, "search-result-item-title"))
    )
    camera_link = filter_search_result_title.find_element(By.XPATH, "./a")
    camera_link.click()
    time.sleep(10)

    product_description_header = driver.find_element(By.CLASS_NAME, "prod_name")
    product_description_container = driver.find_element(By.CLASS_NAME, "product_description_item-list")
    tech_items_title = driver.find_element(By.CLASS_NAME, "tech-specs-items-title-wrap")
    tech_items_description = driver.find_element(By.CLASS_NAME, "tech-specs-items-description-wrap")

    return {
        "product_description_header": product_description_header,
        "product_description_container": product_description_container,
        "tech_items_title": tech_items_title,
        "tech_items_description": tech_items_description,
    }

def modify_html(camera_name_list, product_details):
    input_file_path = 'output.html'
    output_file_path = f'{camera_name_list}.html'

    with open(input_file_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')

    def update_list_section(soup, class_name, new_content):
        section = soup.find('ul', class_=class_name)
        if section:
            section.clear()
            new_items = BeautifulSoup(new_content.get_attribute('outerHTML'), 'html.parser')
            for item in new_items.contents:
                modify_item_classes(item)
                section.append(item)

    def modify_item_classes(item):
        class_modifications = {
            'tech-specs-items-description': 'slide',
            'tech-specs-items-description-list': 'specification_title',
            'tech-specs-items-description__title': 'left_title',
            'tech-specs-items-description__title-details': 'right_title title-left-alone'
        }
        for old_class, new_class in class_modifications.items():
            for tag in item.find_all(class_=old_class):
                tag['class'].extend(new_class.split())

    def update_header(soup, camera_name_list):
        header_div = soup.find('div', class_='name_of_camera_headers_left')
        if header_div:
            header_p = header_div.find('p')
            if header_p:
                header_p.string = camera_name_list

    def update_image(soup, camera_name_list):
        images_div = soup.find('div', class_='images_of_camera')
        if images_div:
            img_tag = images_div.find('img')
            if img_tag:
                img_tag['src'] = f"../../../img/ip_cameras/{camera_name_list}.png"

    # Update sections with the new content
    update_list_section(soup, 'prod_name', product_details['product_description_header'])
    update_list_section(soup, 'product_description_item-list', product_details['product_description_container'])
    update_list_section(soup, 'slide_navigation', product_details['tech_items_title'])
    update_list_section(soup, 'slides', product_details['tech_items_description'])

    # Update header and image
    update_header(soup, camera_name_list)
    update_image(soup, camera_name_list)

    with open(output_file_path, 'w', encoding='utf-8') as file:
        file.write(str(soup.prettify()))

    print(f'Outer HTML has been written to {output_file_path}')

def main():
    driver = setup_driver()
    try:
        navigate_to_site(driver)
        accept_cookies(driver)
        perform_search(driver, camera_name_list)
        time.sleep(10)
        result_text = get_search_results(driver)
        if result_text and process_result_text(result_text):
            product_details = scrape_product_details(driver)
            modify_html(camera_name_list, product_details)
        else:
            print('No results or invalid result text')
    finally:
        driver.quit()

if __name__ == "__main__":
    main()

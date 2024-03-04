import csv
import time
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support import expected_conditions as EC

def scrape_page(page_number, pincode_input, writer):
    products = []

    # Navigate to the search results page
    url = f"https://www.amazon.in/s?k=laptops&page={page_number}&pincode={pincode_input}"

    driver.get(url)
    
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, "laptops")))

    # Directly use the provided pincode
    pincode = pincode_input

    # Get the HTML content of the current page
    page_html = driver.page_source
    soup = BeautifulSoup(page_html, 'html.parser')

    # Extract product details
    product_name_class = 'a-size-medium a-color-base a-text-normal'
    product_elements = soup.find_all('span', class_=product_name_class)

    for product_element in product_elements:
        product_details = {}
        product_details['Product Name'] = product_element.get_text(strip=True)

        # Get the product URL
        product_url = product_element.find_parent('a')['href']

        # Navigate to the product details page
        driver.get(f"https://www.amazon.in{product_url}")
        time.sleep(2)

        # Parse the details page HTML
        details_page_html = driver.page_source
        details_soup = BeautifulSoup(details_page_html, 'html.parser')

        # Extract additional details
        product_details['SKU ID'] = details_soup.find('div', {'data-asin': True}).get('data-asin', '')
        product_details['Product Title'] = details_soup.find('span', {'id': 'productTitle'}).get_text(strip=True)
        product_details['Description'] = details_soup.find('meta', {'name': 'description'}).get('content', '')
        product_details['Category'] = details_soup.find('span', {'class': 'a-list-item'}).get_text(strip=True)
        mrp_price_element= details_soup.find('span', {'class': 'a-price a-text-price'})
        if mrp_price_element :
            mrp_price = mrp_price_element.get_text(strip=True)
            product_details['MRP'] = f"{mrp_price}"
        else:
            product_details['MRP'] = ''

        selling_price_element = details_soup.find('span', {'class': 'a-price-whole'})
        if selling_price_element:
            selling_price = selling_price_element.get_text(strip=True)
            product_details['Selling Price'] = f"₹{selling_price}"
        else:
            product_details['Selling Price'] = ''

        discount_element = details_soup.find('span', {'class': 'savingsPercentage'})
        product_details['Discount'] = discount_element.get_text(strip=True) if discount_element else ''

        weight_element = details_soup.find('td', {'class': 'a-size-base prodDetAttrValue'})
        product_details['Weight'] = weight_element.get_text(strip=True) if weight_element else ''

        product_details['Brand Name'] = details_soup.find('span', {'class': 'a-size-base po-break-word'}).get_text(strip=True)
        product_details['Image URL'] = details_soup.find('img', {'id': 'landingImage'}).get('src', '')

        specification_element = details_soup.find('div', {'id': 'feature-bullets'})
        if specification_element:
            laptop_specification = specification_element.find('ul', {'class': 'a-unordered-list'})
            product_details['Laptop Specification'] = laptop_specification.get_text(strip=True) if laptop_specification else ''

        # Add Pincode to product details
        product_details['Pincode'] = pincode

        delivery_info_element = details_soup.find('span', {'data-csa-c-type': 'element', 'data-csa-c-id': 'gnud5l-lv62wg-k4sdjh-q5q9pt'})
        if delivery_info_element:
            delivery_fee = delivery_info_element.get('data-csa-c-delivery-price', '')
            delivery_time = delivery_info_element.find('span', {'class': 'a-text-bold'}).get_text(strip=True)

            product_details['Delivery Fee'] = delivery_fee
            product_details['Estimated Delivery Time'] = delivery_time
        else:
            product_details['Delivery Fee'] = ''
            product_details['Estimated Delivery Time'] = ''

        products.append(product_details)

        writer.writerow(product_details)

    return products

if __name__ == "__main__":
    service = Service(executable_path="chromedriver")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(service=service)

    total_pages = 10  # Number of pages to scrape
    pincodes = ["560001", "110001"]  # pincodes

    for selected_pincode in pincodes:
        csv_file_path = f'amazon_laptops_data_{selected_pincode}.csv'
        fields = ["Product Name", "SKU ID", "Product Title", "Description", "Category", "MRP", "Selling Price", "Discount", "Weight", "Brand Name", "Image URL", "Laptop Specification", "Pincode", "Delivery Fee", "Estimated Delivery Time"]
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fields)

            # Write header
            writer.writeheader()

            with ThreadPoolExecutor(max_workers=10) as executor:
                all_products = list(executor.map(scrape_page, range(0, total_pages + 1), [selected_pincode] * (total_pages + 1), [writer] * (total_pages + 1)))

    driver.quit()
    print(f'Data exported to {csv_file_path}')


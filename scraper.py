import time
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Setup driver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

data = []

for page in range(1, 6):
    url = f"https://www.magicbricks.com/property-for-sale/residential-real-estate?cityName=Bhopal&page={page}"
    driver.get(url)
    time.sleep(6)

    properties = driver.find_elements(By.CLASS_NAME, "mb-srp__card")

    for prop in properties:
        try:
            title = prop.find_element(By.CLASS_NAME, "mb-srp__card--title").text
            price_text = prop.find_element(By.CLASS_NAME, "mb-srp__card__price").text
            area_info = prop.find_element(By.CLASS_NAME, "mb-srp__card__summary").text

            # 🔹 Extract BHK
            bhk_match = re.search(r'(\d+)\s*BHK', title)
            bhk = int(bhk_match.group(1)) if bhk_match else None

            # 🔹 Extract Price
            price_clean = price_text.replace("₹", "").split("\n")[1].strip()
            if "Lac" in price_clean:
                price = float(price_clean.replace("Lac", "")) * 100000
            elif "Cr" in price_clean:
                price = float(price_clean.replace("Cr", "")) * 10000000
            else:
                price = None

            # 🔹 Extract Area
            area_match = re.search(r'(\d+)', area_info)
            area = int(area_match.group(1)) if area_match else None

            # 🔹 Extract Location (from title)
            location = title.split("in")[-1].strip()

            # 🔹 Extract Status
            if "Ready to Move" in area_info:
                status = "Ready to Move"
            elif "Under Construction" in area_info:
                status = "Under Construction"
            else:
                status = "Unknown"

            data.append({
                "bhk": bhk,
                "price": price,
                "area": area,
                "location": location,
                "status": status
            })

        except:
            continue

    print(f"Page {page} scraped")

driver.quit()

# Create DataFrame
df = pd.DataFrame(data)

# Drop nulls
df = df.dropna()

# Save CSV
df.to_csv("clean_housing_data.csv", index=False)

print("✅ Clean dataset saved!")
print(df.head())
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Setup Chrome driver (UPDATED)
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

# Store all data
all_data = []

# Loop through multiple pages
for page in range(1, 6):  # scrape 5 pages
    url = f"https://www.magicbricks.com/property-for-sale/residential-real-estate?cityName=Bhopal&page={page}"
    
    driver.get(url)
    time.sleep(6)  # wait for page to fully load

    # Scroll down (IMPORTANT for dynamic loading)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)

    # Get all property cards
    properties = driver.find_elements(By.CLASS_NAME, "mb-srp__card")

    for prop in properties:
        try:
            # Title (contains BHK + location)
            title = prop.find_element(By.CLASS_NAME, "mb-srp__card--title").text
            
            # Price
            price = prop.find_element(By.CLASS_NAME, "mb-srp__card__price").text
            
            # Area / extra details
            try:
                area = prop.find_element(By.CLASS_NAME, "mb-srp__card__summary").text
            except:
                area = "NA"

            # Save data
            all_data.append({
                "title": title,
                "price": price,
                "area_info": area
            })

        except:
            continue

    print(f"✅ Page {page} scraped successfully")
    time.sleep(2)

# Close browser
driver.quit()

# Convert to DataFrame
df = pd.DataFrame(all_data)

# Save to CSV
df.to_csv("housing_data.csv", index=False)

print("\n🎉 Scraping Completed!")
print(f"Total records collected: {len(df)}")
print(df.head())
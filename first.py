
import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import mysql.connector

# MySQL Database connection function
def connect_db():
    return mysql.connector.connect(
        host='127.0.0.1',
        user='root',
        password='1234',
        database='redbus'
    )

# Function to create bus_data table if it doesn't exist
def create_table_if_not_exists(cursor):
    create_table_query = '''
    CREATE TABLE IF NOT EXISTS bus_data (
        id INT AUTO_INCREMENT PRIMARY KEY,
        bus_name VARCHAR(255),
        route VARCHAR(255),
        schedule VARCHAR(255),
        price VARCHAR(255),
        seat_availability VARCHAR(255)
    );
    '''
    cursor.execute(create_table_query)

# Function to scrape government bus data from Redbus
def scrape_government_buses(from_city_input, to_city_input):
    # Setup Chrome WebDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    # Add implicit wait
    driver.implicitly_wait(10)  # Global implicit wait for elements to appear

    # Navigate to Redbus
    driver.get('https://www.redbus.in')

    # Wait for the search elements to be available
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, 'src')))
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, 'dest')))

    # Fill in the search form
    from_city = driver.find_element(By.ID, 'src')
    from_city.clear()
    from_city.send_keys(from_city_input)

    to_city = driver.find_element(By.ID, 'dest')
    to_city.clear()
    to_city.send_keys(to_city_input)

    # Wait for the search button to be available and click it
    search_button = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='search_btn']")))
    search_button.click()

    # Wait for results to load
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//div[@class='bus-item']")))

    # Locate bus items
    buses = driver.find_elements(By.XPATH, "//div[@class='bus-item']")

    # Connect to MySQL
    db = connect_db()
    cursor = db.cursor()

    # Create the bus_data table if it doesn't exist
    create_table_if_not_exists(cursor)

    # List of government bus services to filter
    government_buses = [
        "MSRTC", "GSRTC", "PEPSU", "RSRTC", "UPSRTC", 
        "HRTC", "HPTDC", "APSRTC", "TSRTC", "KSRTC", 
        "TNSTC", "PRTC", "KTCL", "ASTC", "MTC", 
        "SBSTC", "West Bengal Transport Corporation", 
        "BSTDC", "BSRTC", "WBTC", "NBSTC"
    ]

    bus_data = []

    for bus in buses:
        try:
            # Extract bus details using XPath
            name = bus.find_element(By.XPATH, ".//div[@class='bus-name']").text
            if any(gov_bus in name for gov_bus in government_buses):
                route = bus.find_element(By.XPATH, ".//div[@class='route']").text
                schedule = bus.find_element(By.XPATH, ".//div[@class='schedule']").text
                price = bus.find_element(By.XPATH, ".//div[@class='fare']").text
                seat_availability = bus.find_element(By.XPATH, ".//div[@class='seat-availability']").text

                # Insert data into MySQL
                cursor.execute(
                    "INSERT INTO bus_data (bus_name, route, schedule, price, seat_availability) VALUES (%s, %s, %s, %s, %s)",
                    (name, route, schedule, price, seat_availability)
                )

                # Store data for display in Streamlit
                bus_data.append({
                    "Bus Name": name,
                    "Route": route,
                    "Schedule": schedule,
                    "Price": price,
                    "Seats": seat_availability
                })
        except Exception as e:
            st.write(f"Error extracting data for bus: {bus}. Error: {e}")

    # Commit changes and close the database connection
    db.commit()
    cursor.close()
    db.close()

    # Close the web driver
    driver.quit()

    return bus_data

# Streamlit app
st.title('Redbus Government Bus Scraper')

# User inputs for cities
from_city = st.text_input('Enter departure city')
to_city = st.text_input('Enter destination city')

if st.button('Search Buses'):
    if from_city and to_city:
        st.write(f'Scraping buses from {from_city} to {to_city}...')
        bus_data = scrape_government_buses(from_city, to_city)
        
        if bus_data:
            st.write('Bus data retrieved:')
            st.table(bus_data)
        else:
            st.write('No buses found.')
    else:
        st.write('Please enter both departure and destination cities.')

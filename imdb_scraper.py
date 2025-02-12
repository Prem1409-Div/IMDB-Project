import time
import pandas as pd
import re
import glob
import logging
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, TimeoutException
from sqlalchemy import create_engine, text
import pymysql

# Clear previous logs
open("imdb_scraper.log", "w").close()

# Configure Logging
logging.basicConfig(
    filename="imdb_scraper.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Database credentials
db_credentials = {
    "username": "root",
    "password": "Guvi%40003",
    "host": "localhost",
    "database": "imdb_db"
}

# MySQL table name
table_name = "movies"

def click_load_more(driver, wait):
    while True:
        try:
            more_button = wait.until(EC.element_to_be_clickable((By.XPATH, 
                '//*[@id="__next"]/main/div[2]/div[3]/section/section/div/section/section/div[2]/div/section/div[2]/div[2]/div[2]/div/span/button/span/span')))
            driver.execute_script("arguments[0].scrollIntoView();", more_button)
            time.sleep(1)
            try:
                more_button.click()
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", more_button)
            time.sleep(3)
        except (NoSuchElementException, TimeoutException):
            logging.info("No more 'Load More' button found. Proceeding to data extraction...")
            break

def convert_duration(duration):
    match = re.match(r"(?:(\d+)h)?\s*(?:(\d+)m)?", duration)
    hours = int(match.group(1)) if match and match.group(1) else 0
    minutes = int(match.group(2)) if match and match.group(2) else 0
    return hours * 60 + minutes

def clean_votes(vote_text):
    vote_text = vote_text.replace("K", "000").replace("M", "000000")
    vote_text = re.sub(r"[^\d]", "", vote_text)
    return int(vote_text) if vote_text.isdigit() and int(vote_text) > 0 else None

def clean_title(title):
    return re.sub(r"^\d+\.\s*", "", title)

def extract_movies(driver, genre):
    data = []
    movie_items = driver.find_elements(By.XPATH, 
        '//*[@id="__next"]/main/div[2]/div[3]/section/section/div/section/section/div[2]/div/section/div[2]/div[2]/ul/li')
    
    for movie in movie_items:
        try:
            title = movie.find_element(By.XPATH, './div/div/div/div[1]/div[2]/div[1]/a/h3').text
            title = clean_title(title)
        except NoSuchElementException:
            title = None
        
        try:
            rating = movie.find_element(By.XPATH, './div/div/div/div[1]/div[2]/span/div/span/span[1]').text
            rating = float(rating) if rating.replace('.', '', 1).isdigit() and float(rating) > 0 else None
        except NoSuchElementException:
             rating = None
        
        try:
            voting = movie.find_element(By.XPATH, './div/div/div/div[1]/div[2]/span/div/span/span[2]').text
            voting = clean_votes(voting)
        except NoSuchElementException:
            voting = None
        
        try:
            duration = movie.find_element(By.XPATH, './div/div/div/div[1]/div[2]/div[2]/span[2]').text
            duration = convert_duration(duration)
            if duration == 0:
               duration = None
        except NoSuchElementException:
            duration = None
        
        data.append([title, genre, rating, voting, duration])
    
    df = pd.DataFrame(data, columns=['Movie_Name', 'Genre', 'Ratings', 'Voting_Counts', 'Duration'])
    logging.info(f"Extracted {len(df)} movies in {genre} genre")
    return df

def scrape_imdb(genre, url):
    logging.info(f"Starting to scrape {genre} movies...")

    driver = webdriver.Chrome()
    driver.get(url)
    wait = WebDriverWait(driver, 15)

    click_load_more(driver, wait)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)

    df = extract_movies(driver, genre)

    csv_filename = f"imdb_{genre}_movies_2024.csv"
    df.to_csv(csv_filename, index=False)
    logging.info(f"Data saved to {csv_filename}")

    driver.quit()

def save_to_mysql(df, table_name):
    logging.info("Connecting to MySQL database...")

    try:
        engine = create_engine(f"mysql+pymysql://{db_credentials['username']}:{db_credentials['password']}@{db_credentials['host']}/{db_credentials['database']}", echo=True)
        
        # **Truncate table before inserting new data**
        with engine.begin() as connection:
            connection.execute(text(f"TRUNCATE TABLE {table_name}"))
            logging.info(f"Table {table_name} truncated successfully.")

        # **Insert data into MySQL**
        with engine.begin() as connection:
            df.to_sql(table_name, con=connection, if_exists='append', index=False)
        
        logging.info(f"Data successfully saved to MySQL table: {table_name}")

    except Exception as e:
        logging.error(f"Error inserting into MySQL: {e}")

def merge_csv_files():
    logging.info("Merging all CSV files...")
    all_files = glob.glob("imdb_*_movies_2024.csv")

    if not all_files:
        logging.warning("No CSV files found. Skipping merge.")
        return

    all_dfs = [pd.read_csv(file) for file in all_files]
    merged_df = pd.concat(all_dfs, ignore_index=True)

    if merged_df.empty:
        logging.warning("Merged DataFrame is empty. Skipping MySQL insertion.")
        return

    merged_df.insert(0, 'Serial_No', range(1, len(merged_df) + 1))

    merged_df["Movie_Name"] = merged_df["Movie_Name"].astype(str)
    merged_df["Genre"] = merged_df["Genre"].astype(str)
    merged_df["Ratings"] = pd.to_numeric(merged_df["Ratings"], errors='coerce')
    merged_df["Voting_Counts"] = pd.to_numeric(merged_df["Voting_Counts"], errors='coerce')
    merged_df["Duration"] = pd.to_numeric(merged_df["Duration"], errors='coerce')

    merged_df.dropna(inplace=True)

    merged_csv_filename = "imdb_merged_movies_2024.csv"
    merged_df.to_csv(merged_csv_filename, index=False)
    logging.info(f"Merged data saved to {merged_csv_filename}")

    save_to_mysql(merged_df, table_name)

def main():
    urls = {
        "Action":"https://www.imdb.com/search/title/?title_type=feature&release_date=2024-01-01,2024-12-31&genres=action",
        "Adventure": "https://www.imdb.com/search/title/?title_type=feature&release_date=2024-01-01,2024-12-31&genres=adventure",
        "Biography": "https://www.imdb.com/search/title/?title_type=feature&release_date=2024-01-01,2024-12-31&genres=biography",
        "Animation": "https://www.imdb.com/search/title/?title_type=feature&release_date=2024-01-01,2024-12-31&genres=animation",
        "Fantasy": "https://www.imdb.com/search/title/?title_type=feature&release_date=2024-01-01,2024-12-31&genres=fantasy"
    }

    for genre, url in urls.items():
        scrape_imdb(genre, url)

    merge_csv_files()
    logging.info("Scraping and merging complete.")

    # **Run Streamlit App Automatically**
    logging.info("Launching Streamlit Dashboard...")
    subprocess.Popen(["streamlit", "run", "Final Project Code/streamlit_dashboard.py"])
    logging.info("Streamlit App Started Successfully!")

if __name__ == "__main__":
    main()

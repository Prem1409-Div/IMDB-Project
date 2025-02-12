# IMDb Movie Scraper & Streamlit Dashboard

## Overview

This project scrapes IMDb movie data using Selenium, processes it with Pandas, stores it in MySQL, and visualizes insights with Streamlit.

## Features

- Scrapes movies from IMDb by genre
- Cleans and processes movie data
- Stores data in MySQL
- Interactive Streamlit dashboard for visualizations
- Filters for duration, ratings, votes, and genre

## Project Structure

```
IMDB Scraping & Visualization/
│   ├── imdb_scraper.py  # IMDb scraping script
│   ├── streamlit_dashboard.py  # Streamlit visualization
│── imdb_scraper.log  # Log file
│── requirements.txt  # Python dependencies
│── README.md  # Project documentation
```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/imdb-movie-analysis.git
   cd imdb-movie-analysis
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up MySQL database:
   - Create a database named `imdb_db`
   - Update database credentials in `imdb_scraper.py` and `streamlit_dashboard.py`

## Running the Project

1. Run the scraper:
   ```bash
   python IMDB\ Scraping\ &\ Visualization/imdb_scraper.py
   ```
2. Start the Streamlit dashboard:
   ```bash
   streamlit run IMDB\ Scraping\ &\ Visualization/streamlit_dashboard.py
   ```

## Notes

- Ensure MySQL is running before executing the scripts.
- Logs are stored in `imdb_scraper.log`.

## Thanks

Thank you for checking out this project! If you have any feedback or improvements, feel free to share. 😊


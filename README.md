# Stock Dashboard 📈

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://stock-dashboard-kunal.streamlit.app/)
[![Project Status: Active](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
![uptime](https://img.shields.io/badge/uptime-100%25-brightgreen)
[![Made With Love](https://img.shields.io/badge/Made%20With-Love-orange.svg)](https://github.com/kunal9960)

This project creates a comprehensive stock dashboard using Python and Streamlit which provides real-time data, performance charts, and key financial metrics to help users understand the behavior of various stocks.

<img src="https://github.com/kunal9960/stocks-dashboard/blob/master/Dashboard.png" width="800">


## Features

- Real-time stock data retrieval from Google Sheets.
- Watchlist with current prices, percentage changes, and sparklines.
- Period performance analysis with candlestick and volume charts.
- Stock performance comparison.


## Requirements

Install using  ```requirements.txt```
- Python 3.11 or more
- Streamlit
- Plotly
- Pandas
- Airbyte


## Setup

1. **Install required packages:**

   ```bash
   pip install streamlit plotly pandas airbyte
   ```
   
2. **Set up Google Sheets connection:**

- Create a Google Service Account and obtain the JSON key file.
- Share your Google Sheet with the service account email.
- Store the JSON key and spreadsheet ID in your Streamlit secrets.

3. **Create your Google Sheets structure:**

- A sheet named ticker with a column ticker listing the stock symbols and all the info you want to display.
- Sheets for each stock symbol containing historical data with columns: date, open, high, low, close, volume.

4. **Run the Streamlit app:**
   ```bash
   streamlit run main.py
   ```


## Usage

1. **Watchlist:**
Displays a list of stocks with current price, percentage change, and a sparkline showing recent price trends.

2. **Period Performance Analysis:**
Shows detailed performance analysis for selected stocks over different periods (Week, Month, Trimester, Year) with candlestick and volume charts.

3. **Stock Performance Comparison:**
Line chart comparing the performance of different stocks over a specified period.


## Contributing

Contributions are welcome! If you have any ideas for improvements or new features, feel free to fork the repository and submit a pull request. You can also open an issue to report bugs or suggest enhancements.


## Acknowledgments

Feel free to contact me if you need help with any of the projects :)

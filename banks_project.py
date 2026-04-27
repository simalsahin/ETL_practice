#importing libraries
from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
from datetime import datetime
import lxml
import sqlite3

url = 'https://web.archive.org/web/20230908091635/https://en.wikipedia.org/wiki/List_of_largest_banks'
exchange_rate_csv = 'https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/IBMSkillsNetwork-PY0221EN-Coursera/labs/v2/exchange_rate.csv'
table_attribs_extract = ["Name", "MC_USD_Billion"]
table_attribs_final = ["Name", "MC_USD_Billion", "MC_GBP_Billion", "MC_EUR_Billion", "MC_INR_Billion"]
output_csv_path = './Largest_banks_data.csv'
db_name = 'Banks.db'
table_name = 'Largest_banks'
log_file = 'code_log.txt'

def log_progress(message):
    timestamp_format = '%Y-%h-%d-%H:%M:%S' 
    now = datetime.now()
    timestamp = now.strftime(timestamp_format)
    with open("./code_log.txt", "a") as f:
        f.write(timestamp + ' : ' + message + '\n')


def extract(url, table_attribs):
    log_progress("Extraction process started")
    html_page = requests.get(url).text
    data = BeautifulSoup(html_page, 'lxml')
    
    df = pd.DataFrame(columns=table_attribs)
    
    tables = data.find_all('tbody')
    rows = tables[0].find_all('tr')

    for row in rows:
        col = row.find_all('td')
        if len(col) != 0:
            bank_name = col[1].get_text(strip=True)
            market_cap_str = col[2].get_text(strip=True).replace(',', '')
            market_cap = float(market_cap_str)
            
            new_row = {"Name": bank_name, "MC_USD_Billion": market_cap}
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            
    log_progress("Extraction process completed")
    return df

def transform(df, csv_path):
    log_progress("Transformation process started")
    exchange_rate_df = pd.read_csv(csv_path)    
    rates = exchange_rate_df.set_index('Currency').to_dict()['Rate']
   
    df['MC_GBP_Billion'] = [round(x * rates['GBP'], 2) for x in df['MC_USD_Billion']]
    df['MC_EUR_Billion'] = [round(x * rates['EUR'], 2) for x in df['MC_USD_Billion']]
    df['MC_INR_Billion'] = [round(x * rates['INR'], 2) for x in df['MC_USD_Billion']]
    
    log_progress("Transformation process completed")
    return df

def load_to_csv(df, output_path):
    log_progress("Loading to CSV started")
    df.to_csv(output_path, index=False)
    log_progress("Loading to CSV completed")

def load_to_db(df, sql_connection, table_name):
    log_progress("Loading to Database started")
    df.to_sql(table_name, sql_connection, if_exists='replace', index=False)
    log_progress("Loading to Database completed")

def run_query(query_statement, sql_connection):
    log_progress(f"Running query: {query_statement}")
    query_output = pd.read_sql(query_statement, sql_connection)
    print(f"Query: {query_statement}")
    print(query_output)
    print("-" * 30)

log_progress('Preliminaries complete. Initiating ETL process')

df = extract(url, table_attribs_extract)

df = transform(df, exchange_rate_csv)

load_to_csv(df, output_csv_path)

sql_connection = sqlite3.connect(db_name)
load_to_db(df, sql_connection, table_name)

run_query("SELECT Name, MC_GBP_Billion FROM Largest_banks", sql_connection)
run_query("SELECT Name, MC_EUR_Billion FROM Largest_banks", sql_connection)
run_query("SELECT Name, MC_INR_Billion FROM Largest_banks", sql_connection)

run_query("SELECT * FROM Largest_banks", sql_connection)
run_query("SELECT AVG(MC_GBP_Billion) FROM Largest_banks", sql_connection)
run_query("SELECT Name from Largest_banks LIMIT 5", sql_connection)

sql_connection.close()
log_progress('Server Connection closed. ETL process complete.')
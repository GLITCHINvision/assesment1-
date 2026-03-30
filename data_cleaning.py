import pandas as pd
import numpy as np
import sqlite3
import os



CAMPAIGN_FILE = "raw_data/Campaign_Raw.csv"
SHOPIFY_FILE = "raw_data/Raw_Shopify_Sales.csv"
DB_FILE = "growify_database.db"              # This is the SQL database we'll build!
REPORT_FILE = "data_quality_report.md"       # A cool text file logging all the junk we cleaned up

def load_data(filepath):
    
    print(f"Loading data from {filepath}...")
    try:
        
        return pd.read_csv(filepath, low_memory=False)
    except FileNotFoundError:
        print(f"Oops: Could not find {filepath}. Skipping it for now.")
        return None

def clean_string_column(series):
    
    return series.astype(str).str.lower().str.strip()

def clean_campaign_data(df, report_log):
    
    if df is None: return None
    report_log.append("\n### Campaign Data Cleaning (`Campaign_Raw.csv`)")
    
    
    initial_count = len(df)
    df = df.drop_duplicates()
    dupes = initial_count - len(df)
    if dupes > 0: 
        report_log.append(f"- **Duplicates**: Detected and threw out {dupes} duplicate rows.")
    

    col_map = {
        'Data Source name': 'Platform',
        'Date': 'Date',
        'Campaign Name': 'Campaign_Name',
        'Campaign Effective Status': 'Status',
        'Country Funnel': 'Region',
        'Amount Spent (INR)': 'Spend',
        'Impressions': 'Impressions',
        'Clicks (all)': 'Clicks',
        'Purchases': 'Conversions',
        'Purchases Conversion Value (INR)': 'Sales_Revenue'
    }
    
    
    present_cols = {k: v for k, v in col_map.items() if k in df.columns}
    df = df.rename(columns=present_cols)
    
    
    for req_col in col_map.values():
        if req_col not in df.columns:
            df[req_col] = np.nan
            
   
    string_cols = ['Platform', 'Region', 'Status']
    for col in string_cols:
        df[col] = clean_string_column(df[col])
        df[col] = df[col].replace('nan', np.nan)
        
   
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce', format='mixed')
    missing_dates = df['Date'].isna().sum()
    df = df.dropna(subset=['Date']) 
    if missing_dates > 0:
        report_log.append(f"- **Dates**: Fixed dates to YYYY-MM-DD. Tossed {missing_dates} unreadable ghost dates out.")
    
   
    num_cols = ['Spend', 'Impressions', 'Clicks', 'Conversions', 'Sales_Revenue']
    for col in num_cols:
        
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
       
        df[col] = np.where(df[col] < 0, 0.0, df[col])
        
 
    mask_spend = df['Spend'] == 0.0
    median_spend = df[~mask_spend].groupby('Platform')['Spend'].median()
    df['Spend'] = df.apply(lambda r: median_spend.get(r['Platform'], 0.0) if r['Spend'] == 0.0 else r['Spend'], axis=1)
    report_log.append("- **Imputation**: Found '0.0 Spend' rows and smartly plugged the gap by borrowing the platform's average (median) spend.")
    

    q1 = df['Spend'].quantile(0.25)
    q3 = df['Spend'].quantile(0.75)
    iqr = q3 - q1
    upper_bound = q3 + 3 * iqr  
    outliers = len(df[df['Spend'] > upper_bound])
    if outliers > 0:
        df.loc[df['Spend'] > upper_bound, 'Spend'] = upper_bound
        report_log.append(f"- **Outliers**: Found {outliers} insane typos in 'Spend'. Squashed them safely down to our max roof of {upper_bound:.2f}.")
        
    
    df['CTR'] = np.where(df['Impressions'] > 0, (df['Clicks'] / df['Impressions']) * 100, 0.0)
    df['CPM'] = np.where(df['Impressions'] > 0, (df['Spend'] / df['Impressions']) * 1000, 0.0)
    df['CPC'] = np.where(df['Clicks'] > 0, df['Spend'] / df['Clicks'], 0.0)
    df['ROI'] = np.where(df['Spend'] > 0, ((df['Sales_Revenue'] - df['Spend']) / df['Spend']) * 100, 0.0)
    report_log.append("- **Metrics**: Fully recalculated true CTR, CPM, CPC, and ROI to wipe away original Excel calculation flaws.")
    
    df['Campaign_ID'] = 'C_' + df['Campaign_Name'].fillna('UNK').astype(str).str.replace(r'[^a-zA-Z0-9]+', '_', regex=True).str.lower() + '_' + df['Platform'].astype(str).str.lower()
    df['date_id'] = df['Date'].dt.strftime('%Y%m%d').astype(int) 
    
    return df

def clean_shopify_data(df, report_log):
    
    if df is None: return None
    report_log.append("\n### Shopify Sales Cleaning (`Raw_Shopify_Sales.csv`)")
    
  
    initial_count = len(df)
    df = df.drop_duplicates()
    dupes = initial_count - len(df)
    if dupes > 0: 
        report_log.append(f"- **Duplicates**: Deleted {dupes} exact duplicate Shopify orders.")
    
    col_map = {
        'Order ID': 'Order_ID',
        'Date': 'Date',
        'Data Source name': 'Brand',
        'Billing Country': 'Region',
        'Total Sales (INR)': 'Total_Sales',
        'Orders': 'Orders'
    }
    
   
    present_cols = {k: v for k, v in col_map.items() if k in df.columns}
    df = df.rename(columns=present_cols)
    
    for req_col in col_map.values():
        if req_col not in df.columns:
            df[req_col] = np.nan
            
    
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce', format='mixed')
    missing_dates = df['Date'].isna().sum()
    df = df.dropna(subset=['Date'])
    if missing_dates > 0:
        report_log.append(f"- **Dates**: Tossed {missing_dates} unreadable or blank timestamps out the window.")
    

    df['date_id'] = df['Date'].dt.strftime('%Y%m%d').astype(int)
    

    for col in ['Brand', 'Region']:
        df[col] = clean_string_column(df[col])
        df[col] = df[col].replace('nan', np.nan)
        

    df['Total_Sales'] = pd.to_numeric(df['Total_Sales'], errors='coerce').fillna(0.0)
    df['Orders'] = pd.to_numeric(df['Orders'], errors='coerce').fillna(0.0)
    report_log.append("- **Formatting**: Scrubbed text out of numeric columns so Shopify sales sum up nicely without crashing.")
    
   
    missing_ids = df['Order_ID'].isna().sum()
    if missing_ids > 0:
        df['Order_ID'] = df['Order_ID'].fillna(pd.Series([f"O_MOCK_{i}" for i in range(len(df))], index=df.index))
    df['Order_ID'] = df['Order_ID'].astype(str)
    
    return df

def generate_db(camp_df, shopify_df):
    
    print(f"Stuffing clean data into the {DB_FILE} database...")
    conn = sqlite3.connect(DB_FILE)
    
   
    dates1 = camp_df['Date'] if camp_df is not None else pd.Series()
    dates2 = shopify_df['Date'] if shopify_df is not None else pd.Series()
    all_dates = pd.concat([dates1, dates2]).dropna().unique()
    
    date_df = pd.DataFrame({'full_date': pd.to_datetime(all_dates)})
    date_df['date_id'] = date_df['full_date'].dt.strftime('%Y%m%d').astype(int)
    
  
    date_df['week'] = date_df['full_date'].dt.isocalendar().week
    date_df['month'] = date_df['full_date'].dt.month
    date_df['quarter'] = date_df['full_date'].dt.quarter
    date_df['year'] = date_df['full_date'].dt.year
    date_df['full_date'] = date_df['full_date'].dt.strftime('%Y-%m-%d')
    date_df.to_sql('date_dim', conn, if_exists='replace', index=False)
    
    
    if camp_df is not None:
        camp_cols = ['Campaign_ID', 'Campaign_Name', 'Platform', 'Region', 'Status']
       
        camp_dim = camp_df[camp_cols].copy().drop_duplicates(subset=['Campaign_ID'])
        camp_dim['channel'] = 'Performance' 
        
        camp_dim = camp_dim.rename(columns={
            'Campaign_ID': 'campaign_id',
            'Campaign_Name': 'campaign_name',
            'Platform': 'platform',
            'Region': 'region',
            'Status': 'status'
        })
        camp_dim.to_sql('campaign_dim', conn, if_exists='replace', index=False)
        
        
        fact_cols = ['date_id', 'Campaign_ID', 'Spend', 'Impressions', 'Clicks', 'Conversions', 'Sales_Revenue', 'CTR', 'CPM', 'CPC', 'ROI']
        sales_fact = camp_df[fact_cols].copy()
        sales_fact = sales_fact.rename(columns={
            'Campaign_ID': 'campaign_id',
            'Spend': 'spend', 'Impressions': 'impressions', 'Clicks': 'clicks', 
            'Conversions': 'conversions', 'Sales_Revenue': 'sales_revenue',
            'CTR': 'ctr', 'CPM': 'cpm', 'CPC': 'cpc', 'ROI': 'roi'
        })
        
     
        sales_fact.reset_index(drop=True, inplace=True)
        sales_fact.index.name = 'fact_id'
        sales_fact.to_sql('sales_fact', conn, if_exists='replace', index=True)
        
   
    if shopify_df is not None:
        shop_cols = ['Order_ID', 'date_id', 'Brand', 'Region', 'Total_Sales', 'Orders']
        shop_fact = shopify_df[shop_cols].copy()
        shop_fact = shop_fact.rename(columns={
            'Order_ID': 'order_id',
            'Brand': 'brand', 'Region': 'region',
            'Total_Sales': 'total_sales', 'Orders': 'orders'
        })
        shop_fact.to_sql('shopify_orders_fact', conn, if_exists='replace', index=False)
        
    conn.commit()
    conn.close()

def main():
    print("Welcome to my Data Cleaning Robot! Firing it up...")
    report_log = []
    

    df_camp = load_data(CAMPAIGN_FILE)
    df_shop = load_data(SHOPIFY_FILE)
    

    df_camp_clean = clean_campaign_data(df_camp, report_log)
    df_shop_clean = clean_shopify_data(df_shop, report_log)
    
    
    with open(REPORT_FILE, "w") as f:
        f.write("# Data Quality & Cleaning Report\n\n")
        f.write("A super quick overview of exactly how much junk my automated pipeline threw out across BOTH files so that your BI dashboard is perfect.\n")
        for line in report_log:
            f.write(f"{line}\n")
    print(f"Just saved a log file so we remember what we cleaned: `{REPORT_FILE}`.")
    
    
    if df_camp_clean is not None or df_shop_clean is not None:
        generate_db(df_camp_clean, df_shop_clean)
        
    print("Data Cleaning is officially done! You can connect Power BI now!")

if __name__ == "__main__":
    main()

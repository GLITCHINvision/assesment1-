# Data Quality & Cleaning Report

A super quick overview of exactly how much junk my automated pipeline threw out across BOTH files so that your BI dashboard is perfect.

### Campaign Data Cleaning (`Campaign_Raw.csv`)
- **Duplicates**: Detected and threw out 310 duplicate rows.
- **Dates**: Fixed dates to YYYY-MM-DD. Tossed 654 unreadable ghost dates out.
- **Imputation**: Found '0.0 Spend' rows and smartly plugged the gap by borrowing the platform's average (median) spend.
- **Outliers**: Found 853 insane typos in 'Spend'. Squashed them safely down to our max roof of 3782.66.
- **Metrics**: Fully recalculated true CTR, CPM, CPC, and ROI to wipe away original Excel calculation flaws.

### Shopify Sales Cleaning (`Raw_Shopify_Sales.csv`)
- **Duplicates**: Deleted 21 exact duplicate Shopify orders.
- **Dates**: Tossed 481 unreadable or blank timestamps out the window.
- **Formatting**: Scrubbed text out of numeric columns so Shopify sales sum up nicely without crashing.

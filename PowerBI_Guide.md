# Power BI Connection & DAX Guide

## Step 1: Connecting your SQL "Single Source of Truth"
1. Open Power BI Desktop.
2. Select **Get Data** > **More** > **ODBC**.
3. Choose **SQLite3 Datasource** (If you don't have the SQLite ODBC driver installed on your machine, you must download `sqliteodbc.exe` online first). 
4. Point the Database Name string to your full path: `C:\Users\Hp\OneDrive\Desktop\growify assesment\growify_database.db`.
5. Check all three tables (`campaign_dim`, `date_dim`, `sales_fact`) and click **Load**.

## Step 2: The Data Model (Star Schema)
1. Go to the **Model View** (third icon on the left bar).
2. Drag `date_dim[date_id]` to `sales_fact[date_id]` (1-to-Many).
3. Drag `campaign_dim[campaign_id]` to `sales_fact[campaign_id]` (1-to-Many).
4. Right-click `date_dim`, click **Mark as Date Table** and select `full_date` as the date column.

## Step 3: DAX Measures
Create a new Table called "Key Measures" (Enter Data -> Load blank table) to store these cleanly. Right click and select **New Measure** for each:

```dax
Total Spend = SUM(sales_fact[Spend])

Total Sales = SUM(sales_fact[Sales_Revenue])

Total Conversions = SUM(sales_fact[Conversions])

ROI = 
DIVIDE(
    [Total Sales] - [Total Spend],
    [Total Spend],
    0
)

CTR % = 
DIVIDE(
    SUM(sales_fact[Clicks]),
    SUM(sales_fact[Impressions]),
    0
)

CPC = 
DIVIDE(
    [Total Spend],
    SUM(sales_fact[Clicks]),
    0
)

ROAS = 
DIVIDE(
    [Total Sales],
    [Total Spend],
    0
)

MoM Spend Change = 
VAR CurrentMonthSpend = [Total Spend]
VAR PreviousMonthSpend = CALCULATE([Total Spend], PREVIOUSMONTH('date_dim'[full_date]))
RETURN
DIVIDE(
    CurrentMonthSpend - PreviousMonthSpend,
    PreviousMonthSpend,
    BLANK()
)
```

## Step 4: The 3-Page Layout Requirements

### Page 1: Executive Summary
* **Slicer**: Date (`date_dim[full_date]`) + Brand Name/Platform (`campaign_dim[platform]`). Keep this synced across pages.
* **KPI Cards**: `Total Spend`, `Total Sales`, `ROI`, `CTR %`, `CPC`. 
* **Line Chart**: Spend vs Conversions Trend 
  * X-axis: `date_dim[month]` or `date_dim[full_date]` 
  * Y-axis: `Total Spend`
  * Secondary Y-axis: `Total Conversions`
* **Table**: Top 5 Campaigns 
  * Add Campaign Name, Spend, Conversions, ROAS. Sort by ROAS descending. (Top N Filter = 5).

### Page 2: Channel Breakdown
* **Bar Chart**: Performance by Platform.
  * X-axis: `campaign_dim[platform]`
  * Y-axis: `Total Sales`
* **Donut Chart**: Channel Mix.
  * Legend: `campaign_dim[channel]`
  * Values: `Total Spend`
* **Matrix Visual**: Region Breakdown.
  * Rows: `campaign_dim[region]`
  * Columns: `campaign_dim[channel]`
  * Values: `Total Conversions`

### Page 3: Audience Insights
* **Bar Chart**: Conversion Rate by Segment (Assuming Region or Platform as Segment proxy if Audience isn't provided).
* **Scatter Chart**: Spend vs. Conversions.
  * Details: `campaign_dim[campaign_name]`
  * X-axis: `Total Spend`
  * Y-axis: `Total Conversions`

Ensure to export to PDF when finalized via `File -> Export -> Export to PDF`.

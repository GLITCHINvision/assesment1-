
-- 1. Date Dimension Table (date_dim)

-- Think of this as the main calendar for the whole project.
-- It forces Power BI to line up all dates (months, years) perfectly.
CREATE TABLE IF NOT EXISTS date_dim (
    date_id INTEGER PRIMARY KEY,          -- Stored like 20260329 so the computer searches it super fast
    full_date DATE NOT NULL UNIQUE,       -- Standard YYYY-MM-DD
    week INTEGER NOT NULL,
    month INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    year INTEGER NOT NULL
);


-- 2. Campaign Dimension Table (campaign_dim)

-- This table just holds the "tags" or descriptions for our ad campaigns.
-- Instead of repeating "Facebook" 10,000 times in our math table, we just link to it here.
CREATE TABLE IF NOT EXISTS campaign_dim (
    campaign_id TEXT PRIMARY KEY,         -- The unique custom ID we generated in Python
    campaign_name TEXT,
    platform TEXT,                        -- Was it facebook? google?
    channel TEXT,                         -- Basically 'Performance' or 'Social'
    region TEXT,                          -- Where did it run?
    status TEXT                           -- Is it active or paused?
);


-- 3. Sales & Performance Fact Table (sales_fact)

-- The heart of the marketing data! This holds all the actual numbers (spend, clicks).
-- Every row here connects to a specific Date and a specific Campaign.
CREATE TABLE IF NOT EXISTS sales_fact (
    fact_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date_id INTEGER,
    campaign_id TEXT,
    
    -- The raw stats
    spend DECIMAL(10,2) DEFAULT 0.0,
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    sales_revenue DECIMAL(10,2) DEFAULT 0.0,
    
    -- The math stats we calculated in Python so Power BI doesn't have to work as hard
    ctr REAL DEFAULT 0.0,
    cpc DECIMAL(10,2) DEFAULT 0.0,
    cpm DECIMAL(10,2) DEFAULT 0.0,
    roi DECIMAL(10,2) DEFAULT 0.0,
    
    -- These keys are the super-glue tying it to the Calendar and Campaign tables
    FOREIGN KEY (date_id) REFERENCES date_dim(date_id),
    FOREIGN KEY (campaign_id) REFERENCES campaign_dim(campaign_id)
);


-- 4. Backend Sales Fact Table (shopify_orders_fact)

-- We can't perfectly map Shopify orders to Facebook ad campaigns, so they get their own table.
-- This holds the TRUE money we actually collected in the bank!
CREATE TABLE IF NOT EXISTS shopify_orders_fact (
    order_id TEXT PRIMARY KEY,
    date_id INTEGER,                      -- Glues the sale to our Calendar table
    brand TEXT,                           
    region TEXT,                          
    
    total_sales DECIMAL(10,2) DEFAULT 0.0,
    orders INTEGER DEFAULT 0,
    
    FOREIGN KEY (date_id) REFERENCES date_dim(date_id)
);


-- INDEXING

-- Indexes are like a book's table of contents. 
-- They make the AI tool instantly find data without scanning 15,000 rows slowly.

-- Speed up filtering by platform/region
CREATE INDEX IF NOT EXISTS idx_campaign_platform ON campaign_dim(platform);
CREATE INDEX IF NOT EXISTS idx_campaign_region ON campaign_dim(region);

-- Speed up calendar lookups
CREATE INDEX IF NOT EXISTS idx_sales_date ON sales_fact(date_id);
CREATE INDEX IF NOT EXISTS idx_sales_campaign ON sales_fact(campaign_id);

CREATE INDEX IF NOT EXISTS idx_shopify_date ON shopify_orders_fact(date_id);
CREATE INDEX IF NOT EXISTS idx_shopify_region ON shopify_orders_fact(region);



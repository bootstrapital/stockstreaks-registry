## StockStreaks Registry

The StockStreaks Registry is an open-source manifest of the active US equity universe. It provides a high-fidelity list of ticker symbols that meet specific institutional-grade liquidity and listing requirements. This registry serves as the foundational data layer for the [StockStreaks](https://stockstreaks.com) interday pattern app and other financial research applications.

---

### Core Principles

This project focuses on structural metadata rather than volatile pricing data. By isolating ticker status, exchange listing, and market capitalization tiers, the registry provides a stable infrastructure for applications that perform their own time-series analysis or real-time pricing lookups.

#### Selection Criteria

To be included in the active universe, a ticker must meet the following three requirements:

1. **Major Exchange Listing:** Tickers must be listed on the NYSE (NYQ), NASDAQ (NMS, NGM, NCM), or NYSE Arca (ASE, PCX).
2. **Liquidity Floor:** A minimum 10-day average daily volume of 500,000 shares. This ensures clean price action and statistical significance for technical analysis.
3. **Institutional Viability:** Only primary equities and ETFs are tracked; illiquid OTC stocks and administrative filing entities are excluded.

---

### Data Access

The registry is updated on the first Saturday of every month. The data is hosted via GitHub Pages and is accessible through the following branded endpoints:

* **Active Universe (JSON):** `https://registry.stockstreaks.com/data/active_tickers.json`
* **Active Universe (CSV):** `https://registry.stockstreaks.com/data/active_tickers.csv`
* **Change Log (JSON):** `https://registry.stockstreaks.com/data/changelog.json`

---

### Data Schema

The `active_tickers.json` file contains an array of objects representing the current liquid universe.

| Field | Type | Description |
| --- | --- | --- |
| ticker | String | The unique ticker symbol (e.g., AAPL, SE). |
| name | String | The short name of the company or fund. |
| sector | String | The GICS sector classification. |
| cap_tier | String | The market capitalization tier (Mega to Nano). |
| avg_volume | Integer | The 10-day average daily volume. |
| exchange | String | The Market Identifier Code (MIC) for the primary exchange. |

---

### Market Capitalization Tiers

The registry categorizes tickers based on the following standard industry brackets:

* **Mega-Cap:** Over $200 billion
* **Large-Cap:** $10 billion to $200 billion
* **Mid-Cap:** $2 billion to $10 billion
* **Small-Cap:** $250 million to $2 billion
* **Micro-Cap:** $50 million to $250 million
* **Nano-Cap:** Below $50 million

---

### Automation and Reliability

This registry is powered by Modal and GitHub Actions.

1. **Scheduling:** A GitHub Action triggers the update process on a monthly cadence (first Saturday).
2. **Parallel Processing:** The script utilizes Modal's serverless infrastructure to process the entire SEC ticker registry (10,000+ entries) in parallel, ensuring high throughput and fresh data.
3. **Change Tracking:** Every run calculates the "churn" (additions and removals) against the previous month's data. This history is preserved in `changelog.json`, providing a record of how the liquid universe evolves over time.
4. **Archiving:** Point-in-time snapshots are stored in the `/data/archive` directory for historical audit and research purposes.

---

#### Javascript Integration Example

The registry supports Cross-Origin Resource Sharing (CORS), allowing for direct integration into web applications.

```javascript
async function fetchUniverse() {
    const response = await fetch('https://registry.stockstreaks.com/data/active_tickers.json');
    const tickers = await response.json();
    return tickers.filter(t => t.cap_tier === "Large-Cap");
}

```

---

#### Python Integration Example

The following snippet demonstrates how to fetch the latest liquid universe directly from the registry and filter it using **Pandas**.

```python
import pandas as pd
import requests

def get_liquid_universe(tier="Large-Cap", sector=None):
    """
    Fetches the latest StockStreaks Registry and filters by cap tier and sector.
    """
    url = "https://registry.stockstreaks.com/data/active_tickers.json"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        df = pd.DataFrame(data)
        
        # Apply filters
        filtered_df = df[df['cap_tier'] == tier]
        if sector:
            filtered_df = filtered_df[filtered_df['sector'] == sector]
            
        return filtered_df
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching registry: {e}")
        return None

# Example: Get all Large-Cap Technology stocks
tech_stocks = get_liquid_universe(tier="Large-Cap", sector="Technology")
print(tech_stocks[['ticker', 'name', 'avg_volume']].head())

```

---

### Technical Disclaimer

The data provided in this registry is for informational and research purposes only. It is generated automatically from third-party sources (SEC and Yahoo Finance) and does not constitute financial advice. While the 500,000-share volume threshold is intended to ensure data quality, StockStreaks makes no guarantees regarding the accuracy or timeliness of the information. Users should verify all data before making investment decisions.

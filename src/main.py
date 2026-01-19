import modal
import pandas as pd
import requests
import json
import os
from datetime import datetime

# Modal Environment Setup
image = modal.Image.debian_slim().pip_install("pandas", "yfinance", "requests")
app = modal.App("stockstreaks-registry")

@app.function(image=image, timeout=1200)
def analyze_ticker_remote(symbol):
    import yfinance as yf
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # 500k Volume Filter + Major US Exchanges
        major_exchanges = ['NYQ', 'NMS', 'NGM', 'NCM', 'ASE', 'PCX']
        vol = info.get('averageVolume', 0)
        
        if info.get('exchange') in major_exchanges and vol >= 500000:
            m_cap = info.get('marketCap', 0)
            
            # Common Market Cap Tiers Logic
            if m_cap >= 200_000_000_000:
                tier = "Mega-Cap"
            elif m_cap >= 10_000_000_000:
                tier = "Large-Cap"
            elif m_cap >= 2_000_000_000:
                tier = "Mid-Cap"
            elif m_cap >= 250_000_000:
                tier = "Small-Cap"
            elif m_cap >= 50_000_000:
                tier = "Micro-Cap"
            else:
                tier = "Nano-Cap"

            return {
                "ticker": symbol,
                "name": info.get('shortName', 'N/A'),
                "sector": info.get('sector', 'N/A'),
                "cap_tier": tier,
                "avg_volume": vol,
                "exchange": info.get('exchange')
            }
    except:
        return None

@app.local_entrypoint()
def main():
    timestamp = datetime.now().strftime("%Y-%m-%d")
    os.makedirs("data/archive", exist_ok=True)

    # 1. Fetch SEC Master List
    headers = {'User-Agent': "StockStreaksRegistry/1.0 (contact@stockstreaks.com)"}
    res = requests.get("https://www.sec.gov/files/company_tickers.json", headers=headers)
    all_tickers = [v['ticker'] for k, v in res.json().items()]

    # 2. Parallel Processing via Modal
    print(f"[{timestamp}] Analyzing {len(all_tickers)} tickers...")
    results = [r for r in analyze_ticker_remote.map(all_tickers) if r]

    # 3. Load previous data for Churn calculation
    old_tickers = set()
    if os.path.exists("data/active_tickers.json"):
        with open("data/active_tickers.json", "r") as f:
            old_tickers = {item['ticker'] for item in json.load(f)}

    # 4. Calculate Churn (Additions and Removals)
    new_tickers = {item['ticker'] for item in results}
    added = sorted(list(new_tickers - old_tickers))
    removed = sorted(list(old_tickers - new_tickers))

    # 5. Update Changelog (JSON + CSV)
    changelog = []
    if os.path.exists("data/changelog.json"):
        with open("data/changelog.json", "r") as f:
            changelog = json.load(f)
    
    changelog.insert(0, {
        "date": timestamp,
        "added_count": len(added),
        "removed_count": len(removed),
        "added": added,
        "removed": removed
    })

    # 6. Save Structural Assets
    # Latest Assets for GitHub Pages
    with open("data/active_tickers.json", "w") as f:
        json.dump(results, f, indent=4)
    pd.DataFrame(results).to_csv("data/active_tickers.csv", index=False)
    
    # Changelog Assets
    with open("data/changelog.json", "w") as f:
        json.dump(changelog[:24], f, indent=4) # Store 24 months of history
    pd.DataFrame(changelog).to_csv("data/changelog.csv", index=False)

    # Historical Snapshot
    pd.DataFrame(results).to_csv(f"data/archive/universe_{timestamp}.csv", index=False)

    print(f"Update complete. Universe: {len(results)} | Added: {len(added)} | Removed: {len(removed)}")

    # Update Sitemap
    sitemap_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://registry.stockstreaks.com/</loc><lastmod>{timestamp}</lastmod><priority>1.0</priority></url>
  <url><loc>https://registry.stockstreaks.com/data/</loc><lastmod>{timestamp}</lastmod><priority>0.8</priority></url>
  <url><loc>https://registry.stockstreaks.com/data/active_tickers.json</loc><lastmod>{timestamp}</lastmod><priority>0.9</priority></url>
  <url><loc>https://registry.stockstreaks.com/data/changelog.json</loc><lastmod>{timestamp}</lastmod><priority>0.6</priority></url>
</urlset>"""
    with open("sitemap.xml", "w") as f:
        f.write(sitemap_content)

"""
Stock Universe for the Expanded Validation Experiment.

~200 NSE-listed stocks across Large, Mid, and Small Cap segments,
classified by sector.

IMPORTANT — SURVIVORSHIP BIAS DISCLAIMER:
This universe consists of stocks that are CURRENTLY listed and trading
on the NSE as of the universe construction date.  It therefore suffers
from survivorship bias: stocks that were delisted, merged, or otherwise
removed from the market between 2019 and 2025 are NOT included.

Consequences:
  1. Stocks that failed (went to zero, got delisted due to fraud or
     insolvency) are absent.  These would likely have produced losing
     trades or no trades (if they were in a persistent downtrend, the
     EMA-slope filter would have screened them out — but this cannot
     be assumed).
  2. Current index constituents are NOT the same as historical
     constituents.  A stock in today's Nifty 50 may have been a mid-cap
     in 2020.  Cap classifications here reflect approximate current
     market cap, not historical.
  3. This bias generally INFLATES backtest performance because the
     surviving stocks are, by definition, the ones that did not fail.

To properly address this, future work should use point-in-time
historical index constituent data (e.g., from NSE archives or
commercial data providers like CMIE Prowess / Bloomberg).
This is explicitly labelled as a LIMITATION of this experiment.

Selection methodology:
  - Stocks are selected based on current NSE listings, aiming for
    broad sector diversification.
  - NO selection was made based on whether a stock performs well or
    poorly under the Trend Pullback strategy.
  - The universe was defined INDEPENDENTLY of strategy results.
"""

# Each entry: (symbol, name, sector, cap)
# cap: "Large", "Mid", "Small"

STOCKS = [
    # =========================================================================
    #  LARGE CAP  (~55 stocks)
    # =========================================================================

    # --- Banking & Financial Services ---
    ("HDFCBANK.NS",   "HDFC Bank",                "Banking & Finance",     "Large"),
    ("ICICIBANK.NS",  "ICICI Bank",               "Banking & Finance",     "Large"),
    ("SBIN.NS",       "State Bank of India",       "Banking & Finance",     "Large"),
    ("KOTAKBANK.NS",  "Kotak Mahindra Bank",       "Banking & Finance",     "Large"),
    ("AXISBANK.NS",   "Axis Bank",                 "Banking & Finance",     "Large"),
    ("INDUSINDBK.NS", "IndusInd Bank",             "Banking & Finance",     "Large"),
    ("BAJFINANCE.NS", "Bajaj Finance",             "Banking & Finance",     "Large"),
    ("BAJAJFINSV.NS", "Bajaj Finserv",             "Banking & Finance",     "Large"),
    ("HDFCLIFE.NS",   "HDFC Life Insurance",       "Banking & Finance",     "Large"),
    ("SBILIFE.NS",    "SBI Life Insurance",         "Banking & Finance",     "Large"),

    # --- IT ---
    ("TCS.NS",        "Tata Consultancy Services", "IT",                    "Large"),
    ("INFY.NS",       "Infosys",                   "IT",                    "Large"),
    ("WIPRO.NS",      "Wipro",                     "IT",                    "Large"),
    ("HCLTECH.NS",    "HCL Technologies",          "IT",                    "Large"),
    ("TECHM.NS",      "Tech Mahindra",             "IT",                    "Large"),
    ("LTIM.NS",       "LTIMindtree",               "IT",                    "Large"),

    # --- Pharma & Healthcare ---
    ("SUNPHARMA.NS",  "Sun Pharmaceutical",         "Pharma & Healthcare",  "Large"),
    ("DRREDDY.NS",    "Dr Reddy's Laboratories",    "Pharma & Healthcare",  "Large"),
    ("CIPLA.NS",      "Cipla",                      "Pharma & Healthcare",  "Large"),
    ("DIVISLAB.NS",   "Divi's Laboratories",        "Pharma & Healthcare",  "Large"),
    ("APOLLOHOSP.NS", "Apollo Hospitals",            "Pharma & Healthcare",  "Large"),

    # --- Automobile ---
    ("TATAMOTORS.NS", "Tata Motors",               "Automobile",            "Large"),
    ("M&M.NS",        "Mahindra & Mahindra",       "Automobile",            "Large"),
    ("MARUTI.NS",     "Maruti Suzuki",             "Automobile",            "Large"),
    ("BAJAJ-AUTO.NS", "Bajaj Auto",                "Automobile",            "Large"),
    ("HEROMOTOCO.NS", "Hero MotoCorp",             "Automobile",            "Large"),
    ("EICHERMOT.NS",  "Eicher Motors",             "Automobile",            "Large"),

    # --- FMCG ---
    ("HINDUNILVR.NS", "Hindustan Unilever",        "FMCG",                  "Large"),
    ("ITC.NS",        "ITC",                       "FMCG",                  "Large"),
    ("NESTLEIND.NS",  "Nestle India",              "FMCG",                  "Large"),
    ("BRITANNIA.NS",  "Britannia Industries",      "FMCG",                  "Large"),
    ("DABUR.NS",      "Dabur India",               "FMCG",                  "Large"),
    ("GODREJCP.NS",   "Godrej Consumer Products",  "FMCG",                  "Large"),
    ("MARICO.NS",     "Marico",                    "FMCG",                  "Large"),
    ("COLPAL.NS",     "Colgate-Palmolive India",   "FMCG",                  "Large"),

    # --- Consumer Durables ---
    ("TITAN.NS",      "Titan Company",             "Consumer Durables",     "Large"),

    # --- Oil, Gas & Energy ---
    ("RELIANCE.NS",   "Reliance Industries",       "Oil & Gas",             "Large"),
    ("ONGC.NS",       "ONGC",                      "Oil & Gas",             "Large"),
    ("BPCL.NS",       "Bharat Petroleum",          "Oil & Gas",             "Large"),

    # --- Power ---
    ("NTPC.NS",       "NTPC",                      "Power",                 "Large"),
    ("POWERGRID.NS",  "Power Grid Corp",           "Power",                 "Large"),

    # --- Metals & Mining ---
    ("JSWSTEEL.NS",   "JSW Steel",                 "Metals & Mining",       "Large"),
    ("TATASTEEL.NS",  "Tata Steel",                "Metals & Mining",       "Large"),
    ("HINDALCO.NS",   "Hindalco Industries",       "Metals & Mining",       "Large"),
    ("COALINDIA.NS",  "Coal India",                "Metals & Mining",       "Large"),

    # --- Cement ---
    ("ULTRACEMCO.NS", "UltraTech Cement",          "Cement",                "Large"),
    ("GRASIM.NS",     "Grasim Industries",         "Cement",                "Large"),

    # --- Telecom ---
    ("BHARTIARTL.NS", "Bharti Airtel",             "Telecom",               "Large"),

    # --- Capital Goods ---
    ("LT.NS",         "Larsen & Toubro",           "Capital Goods",         "Large"),

    # --- Infrastructure ---
    ("ADANIPORTS.NS", "Adani Ports",               "Infrastructure",        "Large"),

    # --- Chemicals ---
    ("ASIANPAINT.NS", "Asian Paints",              "Chemicals",             "Large"),
    ("PIDILITIND.NS", "Pidilite Industries",       "Chemicals",             "Large"),

    # --- Diversified ---
    ("TATACONSUM.NS", "Tata Consumer Products",    "FMCG",                  "Large"),


    # =========================================================================
    #  MID CAP  (~100 stocks)
    # =========================================================================

    # --- Banking & Financial Services ---
    ("PNB.NS",         "Punjab National Bank",       "Banking & Finance",   "Mid"),
    ("BANKBARODA.NS",  "Bank of Baroda",             "Banking & Finance",   "Mid"),
    ("CANBK.NS",       "Canara Bank",                "Banking & Finance",   "Mid"),
    ("FEDERALBNK.NS",  "Federal Bank",               "Banking & Finance",   "Mid"),
    ("BANDHANBNK.NS",  "Bandhan Bank",               "Banking & Finance",   "Mid"),
    ("IDFCFIRSTB.NS",  "IDFC First Bank",            "Banking & Finance",   "Mid"),
    ("CHOLAFIN.NS",    "Cholamandalam Finance",       "Banking & Finance",   "Mid"),
    ("MUTHOOTFIN.NS",  "Muthoot Finance",            "Banking & Finance",   "Mid"),
    ("MANAPPURAM.NS",  "Manappuram Finance",          "Banking & Finance",   "Mid"),
    ("LICHSGFIN.NS",   "LIC Housing Finance",         "Banking & Finance",   "Mid"),
    ("MFSL.NS",        "Max Financial Services",      "Banking & Finance",   "Mid"),
    ("SBICARD.NS",     "SBI Cards",                   "Banking & Finance",   "Mid"),
    ("ICICIGI.NS",     "ICICI Lombard",               "Banking & Finance",   "Mid"),

    # --- IT ---
    ("PERSISTENT.NS",  "Persistent Systems",         "IT",                   "Mid"),
    ("COFORGE.NS",     "Coforge",                    "IT",                   "Mid"),
    ("MPHASIS.NS",     "Mphasis",                    "IT",                   "Mid"),
    ("LTTS.NS",        "L&T Technology Services",    "IT",                   "Mid"),
    ("TATAELXSI.NS",   "Tata Elxsi",                "IT",                   "Mid"),
    ("BSOFT.NS",       "Birlasoft",                  "IT",                   "Mid"),

    # --- Pharma & Healthcare ---
    ("LUPIN.NS",       "Lupin",                      "Pharma & Healthcare",  "Mid"),
    ("AUROPHARMA.NS",  "Aurobindo Pharma",           "Pharma & Healthcare",  "Mid"),
    ("TORNTPHARM.NS",  "Torrent Pharmaceuticals",    "Pharma & Healthcare",  "Mid"),
    ("ALKEM.NS",       "Alkem Laboratories",         "Pharma & Healthcare",  "Mid"),
    ("IPCALAB.NS",     "IPCA Laboratories",          "Pharma & Healthcare",  "Mid"),
    ("BIOCON.NS",      "Biocon",                     "Pharma & Healthcare",  "Mid"),
    ("GLENMARK.NS",    "Glenmark Pharmaceuticals",   "Pharma & Healthcare",  "Mid"),
    ("NATCOPHARM.NS",  "Natco Pharma",               "Pharma & Healthcare",  "Mid"),
    ("LALPATHLAB.NS",  "Dr Lal PathLabs",            "Pharma & Healthcare",  "Mid"),
    ("METROPOLIS.NS",  "Metropolis Healthcare",       "Pharma & Healthcare",  "Mid"),

    # --- Automobile & Auto Components ---
    ("ASHOKLEY.NS",    "Ashok Leyland",              "Automobile",           "Mid"),
    ("BALKRISIND.NS",  "Balkrishna Industries",      "Automobile",           "Mid"),
    ("MOTHERSON.NS",   "Samvardhana Motherson",      "Automobile",           "Mid"),
    ("BHARATFORG.NS",  "Bharat Forge",               "Automobile",           "Mid"),
    ("TVSMOTORS.NS",   "TVS Motor Company",          "Automobile",           "Mid"),
    ("EXIDEIND.NS",    "Exide Industries",           "Automobile",           "Mid"),
    ("TRENT.NS",       "Trent",                      "Consumer Durables",    "Mid"),

    # --- Consumer Durables & Retail ---
    ("VOLTAS.NS",      "Voltas",                     "Consumer Durables",    "Mid"),
    ("HAVELLS.NS",     "Havells India",              "Consumer Durables",    "Mid"),
    ("CROMPTON.NS",    "Crompton Greaves Consumer",  "Consumer Durables",    "Mid"),
    ("PAGEIND.NS",     "Page Industries",            "Consumer Durables",    "Mid"),
    ("INDHOTEL.NS",    "Indian Hotels",              "Consumer Durables",    "Mid"),
    ("WHIRLPOOL.NS",   "Whirlpool India",            "Consumer Durables",    "Mid"),
    ("DIXON.NS",       "Dixon Technologies",         "Consumer Durables",    "Mid"),

    # --- Chemicals ---
    ("SRF.NS",         "SRF",                        "Chemicals",            "Mid"),
    ("PIIND.NS",       "PI Industries",              "Chemicals",            "Mid"),
    ("AARTIIND.NS",    "Aarti Industries",           "Chemicals",            "Mid"),
    ("DEEPAKNTR.NS",   "Deepak Nitrite",             "Chemicals",            "Mid"),
    ("ATUL.NS",        "Atul",                       "Chemicals",            "Mid"),
    ("BERGEPAINT.NS",  "Berger Paints",              "Chemicals",            "Mid"),
    ("UPL.NS",         "UPL",                        "Chemicals",            "Mid"),

    # --- Cement ---
    ("ACC.NS",         "ACC",                        "Cement",               "Mid"),
    ("AMBUJACEM.NS",   "Ambuja Cements",             "Cement",               "Mid"),
    ("RAMCOCEM.NS",    "Ramco Cements",              "Cement",               "Mid"),
    ("SHREECEM.NS",    "Shree Cement",               "Cement",               "Mid"),
    ("DALBHARAT.NS",   "Dalmia Bharat",              "Cement",               "Mid"),

    # --- Capital Goods & Engineering ---
    ("ABB.NS",         "ABB India",                  "Capital Goods",        "Mid"),
    ("SIEMENS.NS",     "Siemens",                    "Capital Goods",        "Mid"),
    ("CUMMINSIND.NS",  "Cummins India",              "Capital Goods",        "Mid"),
    ("HONAUT.NS",      "Honeywell Automation",       "Capital Goods",        "Mid"),
    ("THERMAX.NS",     "Thermax",                    "Capital Goods",        "Mid"),
    ("BEL.NS",         "Bharat Electronics",         "Capital Goods",        "Mid"),
    ("HAL.NS",         "Hindustan Aeronautics",      "Capital Goods",        "Mid"),

    # --- Metals & Mining ---
    ("SAIL.NS",        "Steel Authority of India",   "Metals & Mining",      "Mid"),
    ("NMDC.NS",        "NMDC",                       "Metals & Mining",      "Mid"),
    ("VEDL.NS",        "Vedanta",                    "Metals & Mining",      "Mid"),
    ("NATIONALUM.NS",  "National Aluminium",         "Metals & Mining",      "Mid"),
    ("JINDALSTEL.NS",  "Jindal Steel & Power",       "Metals & Mining",      "Mid"),

    # --- Oil, Gas & Energy ---
    ("HINDPETRO.NS",   "Hindustan Petroleum",        "Oil & Gas",            "Mid"),
    ("IOC.NS",         "Indian Oil Corp",            "Oil & Gas",            "Mid"),
    ("PETRONET.NS",    "Petronet LNG",               "Oil & Gas",            "Mid"),
    ("GAIL.NS",        "GAIL India",                 "Oil & Gas",            "Mid"),

    # --- Real Estate ---
    ("DLF.NS",         "DLF",                        "Real Estate",          "Mid"),
    ("GODREJPROP.NS",  "Godrej Properties",          "Real Estate",          "Mid"),
    ("OBEROIRLTY.NS",  "Oberoi Realty",              "Real Estate",          "Mid"),
    ("PRESTIGE.NS",    "Prestige Estates",            "Real Estate",          "Mid"),
    ("PHOENIXLTD.NS",  "Phoenix Mills",               "Real Estate",          "Mid"),

    # --- Infrastructure & Logistics ---
    ("CONCOR.NS",      "Container Corp of India",    "Infrastructure",       "Mid"),
    ("IRCTC.NS",       "IRCTC",                      "Infrastructure",       "Mid"),

    # --- FMCG ---
    ("EMAMILTD.NS",    "Emami",                      "FMCG",                 "Mid"),
    ("VBL.NS",         "Varun Beverages",            "FMCG",                 "Mid"),
    ("JUBLFOOD.NS",    "Jubilant FoodWorks",         "FMCG",                 "Mid"),

    # --- Telecom / Media ---
    ("TATACOMM.NS",    "Tata Communications",        "Telecom",              "Mid"),


    # =========================================================================
    #  SMALL CAP  (~55 stocks)
    # =========================================================================

    # --- IT ---
    ("KPITTECH.NS",    "KPIT Technologies",          "IT",                   "Small"),
    ("HAPPSTMNDS.NS",  "Happiest Minds",             "IT",                   "Small"),
    ("ROUTE.NS",       "Route Mobile",               "IT",                   "Small"),
    ("MASTEK.NS",      "Mastek",                     "IT",                   "Small"),
    ("SONATSOFTW.NS",  "Sonata Software",            "IT",                   "Small"),

    # --- Pharma & Healthcare ---
    ("GRANULES.NS",    "Granules India",              "Pharma & Healthcare",  "Small"),
    ("LAURUSLABS.NS",  "Laurus Labs",                "Pharma & Healthcare",  "Small"),
    ("SYNGENE.NS",     "Syngene International",       "Pharma & Healthcare",  "Small"),
    ("SUVENPHAR.NS",   "Suven Pharmaceuticals",       "Pharma & Healthcare",  "Small"),
    ("ASTRAZEN.NS",    "AstraZeneca Pharma India",    "Pharma & Healthcare",  "Small"),

    # --- Chemicals ---
    ("FINEORG.NS",     "Fine Organic Industries",     "Chemicals",            "Small"),
    ("GALAXYSURF.NS",  "Galaxy Surfactants",          "Chemicals",            "Small"),
    ("BALAMINES.NS",   "Balaji Amines",               "Chemicals",            "Small"),
    ("SUDARSCHEM.NS",  "Sudarshan Chemical",           "Chemicals",            "Small"),
    ("CLEAN.NS",       "Clean Science & Technology",   "Chemicals",            "Small"),

    # --- Automobile & Auto Ancillary ---
    ("ENDURANCE.NS",   "Endurance Technologies",      "Automobile",           "Small"),
    ("SUNDRMFAST.NS",  "Sundram Fasteners",           "Automobile",           "Small"),
    ("TIINDIA.NS",     "Tube Investments",            "Automobile",           "Small"),

    # --- Banking & Finance ---
    ("CDSL.NS",        "Central Depository Services", "Banking & Finance",    "Small"),
    ("UJJIVANSFB.NS",  "Ujjivan Small Finance Bank",  "Banking & Finance",    "Small"),
    ("EQUITASBNK.NS",  "Equitas SFB",                 "Banking & Finance",    "Small"),
    ("RBLBANK.NS",     "RBL Bank",                    "Banking & Finance",    "Small"),
    ("CREDITACC.NS",   "CreditAccess Grameen",        "Banking & Finance",    "Small"),

    # --- Consumer Durables ---
    ("TTKPRESTIG.NS",  "TTK Prestige",               "Consumer Durables",    "Small"),
    ("RAJESHEXPO.NS",  "Rajesh Exports",             "Consumer Durables",    "Small"),
    ("RADICO.NS",      "Radico Khaitan",             "Consumer Durables",    "Small"),

    # --- Capital Goods & Engineering ---
    ("ELGIEQUIP.NS",   "Elgi Equipments",            "Capital Goods",        "Small"),
    ("GRINDWELL.NS",   "Grindwell Norton",           "Capital Goods",        "Small"),
    ("CARBORUNIV.NS",  "Carborundum Universal",      "Capital Goods",        "Small"),
    ("PRAJIND.NS",     "Praj Industries",            "Capital Goods",        "Small"),
    ("AFFLE.NS",       "Affle India",                "Capital Goods",        "Small"),

    # --- Infrastructure & Logistics ---
    ("BLUEDART.NS",    "Blue Dart Express",           "Infrastructure",       "Small"),
    ("APLAPOLLO.NS",   "APL Apollo Tubes",            "Infrastructure",       "Small"),
    ("ASTRAL.NS",      "Astral",                      "Infrastructure",       "Small"),

    # --- Metals ---
    ("RATNAMANI.NS",   "Ratnamani Metals",            "Metals & Mining",      "Small"),
    ("HLEGLAS.NS",     "HLE Glascoat",                "Metals & Mining",      "Small"),

    # --- Media / Digital ---
    ("PVRINOX.NS",     "PVR INOX",                   "Media",                "Small"),

    # --- Textiles ---
    ("RAYMOND.NS",     "Raymond",                     "Textiles",             "Small"),
    ("ARVIND.NS",      "Arvind",                      "Textiles",             "Small"),

    # --- Power ---
    ("TATAPOWER.NS",   "Tata Power",                  "Power",               "Small"),
    ("NHPC.NS",        "NHPC",                        "Power",               "Small"),
    ("SJVN.NS",        "SJVN",                        "Power",               "Small"),

    # --- Real Estate ---
    ("BRIGADE.NS",     "Brigade Enterprises",          "Real Estate",         "Small"),
    ("SOBHA.NS",       "Sobha",                        "Real Estate",         "Small"),

    # --- Cement ---
    ("JKCEMENT.NS",    "JK Cement",                   "Cement",              "Small"),
    ("JKLAKSHMI.NS",   "JK Lakshmi Cement",           "Cement",              "Small"),

    # --- FMCG ---
    ("ZYDUSWELL.NS",   "Zydus Wellness",              "FMCG",                "Small"),

    # --- Oil & Gas ---
    ("GSPL.NS",        "Gujarat State Petronet",       "Oil & Gas",           "Small"),
    ("MRPL.NS",        "MRPL",                         "Oil & Gas",           "Small"),
]


def get_universe():
    """Return the full universe as a list of dicts."""
    return [
        {"symbol": s, "name": n, "sector": sec, "cap": c}
        for s, n, sec, c in STOCKS
    ]


def get_universe_by_cap():
    """Return dict keyed by cap category."""
    result = {"Large": [], "Mid": [], "Small": []}
    for entry in get_universe():
        result[entry["cap"]].append(entry)
    return result


def get_universe_by_sector():
    """Return dict keyed by sector."""
    result = {}
    for entry in get_universe():
        result.setdefault(entry["sector"], []).append(entry)
    return result


def summary():
    """Print universe summary."""
    u = get_universe()
    by_cap = get_universe_by_cap()
    by_sec = get_universe_by_sector()
    print(f"Total stocks: {len(u)}")
    for cap, stocks in by_cap.items():
        print(f"  {cap} Cap: {len(stocks)}")
    print(f"Sectors: {len(by_sec)}")
    for sec, stocks in sorted(by_sec.items(), key=lambda x: -len(x[1])):
        print(f"  {sec}: {len(stocks)}")


if __name__ == "__main__":
    summary()

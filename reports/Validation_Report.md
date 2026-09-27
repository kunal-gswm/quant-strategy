# Expanded Universe Validation Report

## 1. Executive Summary
Tested the Trend Pullback strategy across 179 stocks over the 2020-2025 period (warm-up from 2019).
Total trades: 221, Wins: 103, Win rate: 46.61%
Net P&L: ₹71,285.61

## 2. Dataset
Universe: 179 stocks from NSE (Large, Mid, Small caps).
Period: 2020-01-01 to 2025-12-31.
Data Source: Yahoo Finance. **Limitation**: Suffers from survivorship bias as only currently active stocks were included.

## 3. Strategy
EMA50 slope positive, Close > EMA50, RSI(14) crosses above 40. Stop: 1.5 ATR, Target: 2R.

## 4. Backtest Results
| Symbol        | Name                        | Cap   | Sector              |   Trades |   Wins |   Losses |   Win Rate |    Net PnL |   Profit Factor |   Expectancy |       Avg R |
|:--------------|:----------------------------|:------|:--------------------|---------:|-------:|---------:|-----------:|-----------:|----------------:|-------------:|------------:|
| HDFCBANK.NS   | HDFC Bank                   | Large | Banking & Finance   |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| ICICIBANK.NS  | ICICI Bank                  | Large | Banking & Finance   |        4 |      3 |        1 |   0.75     |  4641.31   |        5.36794  |    1160.33   |   1.16786   |
| SBIN.NS       | State Bank of India         | Large | Banking & Finance   |        3 |      1 |        2 |   0.333333 |  -221.904  |        0.89476  |     -73.9678 |  -0.0723438 |
| KOTAKBANK.NS  | Kotak Mahindra Bank         | Large | Banking & Finance   |        1 |      0 |        1 |   0        | -1080.69   |        0        |   -1080.69   |  -1.08475   |
| AXISBANK.NS   | Axis Bank                   | Large | Banking & Finance   |        1 |      0 |        1 |   0        | -1022.58   |        0        |   -1022.58   |  -1.0573    |
| INDUSINDBK.NS | IndusInd Bank               | Large | Banking & Finance   |        1 |      0 |        1 |   0        | -1027.15   |        0        |   -1027.15   |  -1.06473   |
| BAJFINANCE.NS | Bajaj Finance               | Large | Banking & Finance   |        2 |      0 |        2 |   0        | -2103.22   |        0        |   -1051.61   |  -1.05854   |
| BAJAJFINSV.NS | Bajaj Finserv               | Large | Banking & Finance   |        3 |      2 |        1 |   0.666667 |  2711.95   |        3.52709  |     903.983  |   0.935463  |
| HDFCLIFE.NS   | HDFC Life Insurance         | Large | Banking & Finance   |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| SBILIFE.NS    | SBI Life Insurance          | Large | Banking & Finance   |        2 |      1 |        1 |   0.5      |   813.575  |        1.76442  |     406.788  |   0.420441  |
| TCS.NS        | Tata Consultancy Services   | Large | IT                  |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| INFY.NS       | Infosys                     | Large | IT                  |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| WIPRO.NS      | Wipro                       | Large | IT                  |        3 |      1 |        2 |   0.333333 |  -218.979  |        0.896846 |     -72.993  |  -0.0737866 |
| HCLTECH.NS    | HCL Technologies            | Large | IT                  |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| TECHM.NS      | Tech Mahindra               | Large | IT                  |        2 |      1 |        1 |   0.5      |   873.36   |        1.84386  |     436.68   |   0.426299  |
| SUNPHARMA.NS  | Sun Pharmaceutical          | Large | Pharma & Healthcare |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| DRREDDY.NS    | Dr Reddy's Laboratories     | Large | Pharma & Healthcare |        3 |      2 |        1 |   0.666667 |  2803.82   |        3.73558  |     934.605  |   0.928276  |
| CIPLA.NS      | Cipla                       | Large | Pharma & Healthcare |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| DIVISLAB.NS   | Divi's Laboratories         | Large | Pharma & Healthcare |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| APOLLOHOSP.NS | Apollo Hospitals            | Large | Pharma & Healthcare |        1 |      1 |        0 |   1        |  1677.07   |      inf        |    1677.07   |   1.911     |
| M&M.NS        | Mahindra & Mahindra         | Large | Automobile          |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| MARUTI.NS     | Maruti Suzuki               | Large | Automobile          |        1 |      0 |        1 |   0        |  -542.295  |        0        |    -542.295  |  -1.06329   |
| BAJAJ-AUTO.NS | Bajaj Auto                  | Large | Automobile          |        2 |      0 |        2 |   0        | -1948.09   |        0        |    -974.044  |  -1.06388   |
| HEROMOTOCO.NS | Hero MotoCorp               | Large | Automobile          |        2 |      1 |        1 |   0.5      |   578.97   |        1.56053  |     289.485  |   0.417451  |
| EICHERMOT.NS  | Eicher Motors               | Large | Automobile          |        1 |      1 |        0 |   1        |  1536.13   |      inf        |    1536.13   |   1.90553   |
| HINDUNILVR.NS | Hindustan Unilever          | Large | FMCG                |        2 |      0 |        2 |   0        | -2092.94   |        0        |   -1046.47   |  -1.09292   |
| ITC.NS        | ITC                         | Large | FMCG                |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| NESTLEIND.NS  | Nestle India                | Large | FMCG                |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| BRITANNIA.NS  | Britannia Industries        | Large | FMCG                |        3 |      0 |        3 |   0        | -3079.99   |        0        |   -1026.66   |  -1.09278   |
| DABUR.NS      | Dabur India                 | Large | FMCG                |        4 |      2 |        2 |   0.5      |  1681.27   |        1.79121  |     420.318  |   0.423912  |
| GODREJCP.NS   | Godrej Consumer Products    | Large | FMCG                |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| MARICO.NS     | Marico                      | Large | FMCG                |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| COLPAL.NS     | Colgate-Palmolive India     | Large | FMCG                |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| TITAN.NS      | Titan Company               | Large | Consumer Durables   |        2 |      1 |        1 |   0.5      |   843.847  |        1.83003  |     421.924  |   0.418289  |
| RELIANCE.NS   | Reliance Industries         | Large | Oil & Gas           |        1 |      0 |        1 |   0        | -1042.52   |        0        |   -1042.52   |  -1.0754    |
| ONGC.NS       | ONGC                        | Large | Oil & Gas           |        2 |      1 |        1 |   0.5      |   857.434  |        1.81424  |     428.717  |   0.427659  |
| BPCL.NS       | Bharat Petroleum            | Large | Oil & Gas           |        1 |      0 |        1 |   0        | -1106.95   |        0        |   -1106.95   |  -1.10729   |
| NTPC.NS       | NTPC                        | Large | Power               |        3 |      0 |        3 |   0        | -3187.27   |        0        |   -1062.42   |  -1.06332   |
| POWERGRID.NS  | Power Grid Corp             | Large | Power               |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| JSWSTEEL.NS   | JSW Steel                   | Large | Metals & Mining     |        1 |      1 |        0 |   1        |  1935.4    |      inf        |    1935.4    |   1.948     |
| TATASTEEL.NS  | Tata Steel                  | Large | Metals & Mining     |        2 |      1 |        1 |   0.5      |   877.495  |        1.81347  |     438.747  |   0.437527  |
| HINDALCO.NS   | Hindalco Industries         | Large | Metals & Mining     |        3 |      1 |        2 |   0.333333 |  -170.27   |        0.918913 |     -56.7565 |  -0.064602  |
| COALINDIA.NS  | Coal India                  | Large | Metals & Mining     |        2 |      1 |        1 |   0.5      |   895.205  |        1.85873  |     447.603  |   0.448802  |
| ULTRACEMCO.NS | UltraTech Cement            | Large | Cement              |        1 |      1 |        0 |   1        |  1512.39   |      inf        |    1512.39   |   1.92068   |
| GRASIM.NS     | Grasim Industries           | Large | Cement              |        1 |      0 |        1 |   0        |  -994.689  |        0        |    -994.689  |  -1.07516   |
| BHARTIARTL.NS | Bharti Airtel               | Large | Telecom             |        2 |      1 |        1 |   0.5      |   740.271  |        1.67123  |     370.136  |   0.387819  |
| LT.NS         | Larsen & Toubro             | Large | Capital Goods       |        1 |      1 |        0 |   1        |  1791.57   |      inf        |    1791.57   |   1.89915   |
| ADANIPORTS.NS | Adani Ports                 | Large | Infrastructure      |        3 |      2 |        1 |   0.666667 |  2646.78   |        3.48954  |     882.259  |   0.932384  |
| ASIANPAINT.NS | Asian Paints                | Large | Chemicals           |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| PIDILITIND.NS | Pidilite Industries         | Large | Chemicals           |        2 |      1 |        1 |   0.5      |   766.309  |        1.71618  |     383.154  |   0.416562  |
| TATACONSUM.NS | Tata Consumer Products      | Large | FMCG                |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| PNB.NS        | Punjab National Bank        | Mid   | Banking & Finance   |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| BANKBARODA.NS | Bank of Baroda              | Mid   | Banking & Finance   |        1 |      0 |        1 |   0        | -1063.74   |        0        |   -1063.74   |  -1.06636   |
| CANBK.NS      | Canara Bank                 | Mid   | Banking & Finance   |        2 |      0 |        2 |   0        | -2112.3    |        0        |   -1056.15   |  -1.05828   |
| FEDERALBNK.NS | Federal Bank                | Mid   | Banking & Finance   |        2 |      2 |        0 |   1        |  3871.62   |      inf        |    1935.81   |   1.94334   |
| BANDHANBNK.NS | Bandhan Bank                | Mid   | Banking & Finance   |        1 |      0 |        1 |   0        | -1033.3    |        0        |   -1033.3    |  -1.04296   |
| IDFCFIRSTB.NS | IDFC First Bank             | Mid   | Banking & Finance   |        1 |      0 |        1 |   0        | -1033.45   |        0        |   -1033.45   |  -1.03492   |
| CHOLAFIN.NS   | Cholamandalam Finance       | Mid   | Banking & Finance   |        3 |      1 |        2 |   0.333333 |  -213.648  |        0.898484 |     -71.2161 |  -0.0580946 |
| MUTHOOTFIN.NS | Muthoot Finance             | Mid   | Banking & Finance   |        2 |      0 |        2 |   0        | -2038.88   |        0        |   -1019.44   |  -1.06501   |
| MANAPPURAM.NS | Manappuram Finance          | Mid   | Banking & Finance   |        1 |      1 |        0 |   1        |  1948.35   |      inf        |    1948.35   |   1.9618    |
| LICHSGFIN.NS  | LIC Housing Finance         | Mid   | Banking & Finance   |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| MFSL.NS       | Max Financial Services      | Mid   | Banking & Finance   |        4 |      2 |        2 |   0.5      |  1745.61   |        1.8315   |     436.404  |   0.441505  |
| SBICARD.NS    | SBI Cards                   | Mid   | Banking & Finance   |        1 |      1 |        0 |   1        |  1917.78   |      inf        |    1917.78   |   1.93705   |
| ICICIGI.NS    | ICICI Lombard               | Mid   | Banking & Finance   |        1 |      0 |        1 |   0        | -1043.89   |        0        |   -1043.89   |  -1.08078   |
| PERSISTENT.NS | Persistent Systems          | Mid   | IT                  |        1 |      0 |        1 |   0        |  -984.555  |        0        |    -984.555  |  -1.05147   |
| COFORGE.NS    | Coforge                     | Mid   | IT                  |        1 |      0 |        1 |   0        | -1038.79   |        0        |   -1038.79   |  -1.0397    |
| MPHASIS.NS    | Mphasis                     | Mid   | IT                  |        1 |      1 |        0 |   1        |  1800.23   |      inf        |    1800.23   |   1.93526   |
| LTTS.NS       | L&T Technology Services     | Mid   | IT                  |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| TATAELXSI.NS  | Tata Elxsi                  | Mid   | IT                  |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| BSOFT.NS      | Birlasoft                   | Mid   | IT                  |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| LUPIN.NS      | Lupin                       | Mid   | Pharma & Healthcare |        1 |      0 |        1 |   0        | -1064.67   |        0        |   -1064.67   |  -1.0672    |
| AUROPHARMA.NS | Aurobindo Pharma            | Mid   | Pharma & Healthcare |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| TORNTPHARM.NS | Torrent Pharmaceuticals     | Mid   | Pharma & Healthcare |        3 |      3 |        0 |   1        |  5498.94   |      inf        |    1832.98   |   1.92963   |
| ALKEM.NS      | Alkem Laboratories          | Mid   | Pharma & Healthcare |        1 |      0 |        1 |   0        |  -977.289  |        0        |    -977.289  |  -1.0711    |
| IPCALAB.NS    | IPCA Laboratories           | Mid   | Pharma & Healthcare |        1 |      1 |        0 |   1        |  1855.95   |      inf        |    1855.95   |   1.94336   |
| BIOCON.NS     | Biocon                      | Mid   | Pharma & Healthcare |        1 |      0 |        1 |   0        | -1041.12   |        0        |   -1041.12   |  -1.04302   |
| GLENMARK.NS   | Glenmark Pharmaceuticals    | Mid   | Pharma & Healthcare |        1 |      1 |        0 |   1        |  1903.85   |      inf        |    1903.85   |   1.93276   |
| NATCOPHARM.NS | Natco Pharma                | Mid   | Pharma & Healthcare |        1 |      0 |        1 |   0        | -1047.73   |        0        |   -1047.73   |  -1.04912   |
| LALPATHLAB.NS | Dr Lal PathLabs             | Mid   | Pharma & Healthcare |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| METROPOLIS.NS | Metropolis Healthcare       | Mid   | Pharma & Healthcare |        1 |      0 |        1 |   0        | -1045.62   |        0        |   -1045.62   |  -1.05089   |
| ASHOKLEY.NS   | Ashok Leyland               | Mid   | Automobile          |        1 |      0 |        1 |   0        | -1070.19   |        0        |   -1070.19   |  -1.07248   |
| BALKRISIND.NS | Balkrishna Industries       | Mid   | Automobile          |        3 |      3 |        0 |   1        |  5576.06   |      inf        |    1858.69   |   1.94132   |
| MOTHERSON.NS  | Samvardhana Motherson       | Mid   | Automobile          |        2 |      2 |        0 |   1        |  3886.89   |      inf        |    1943.45   |   1.95119   |
| BHARATFORG.NS | Bharat Forge                | Mid   | Automobile          |        1 |      0 |        1 |   0        | -1058.87   |        0        |   -1058.87   |  -1.06058   |
| EXIDEIND.NS   | Exide Industries            | Mid   | Automobile          |        2 |      0 |        2 |   0        | -2135.68   |        0        |   -1067.84   |  -1.07265   |
| TRENT.NS      | Trent                       | Mid   | Consumer Durables   |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| VOLTAS.NS     | Voltas                      | Mid   | Consumer Durables   |        1 |      1 |        0 |   1        |  1812.47   |      inf        |    1812.47   |   1.942     |
| HAVELLS.NS    | Havells India               | Mid   | Consumer Durables   |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| CROMPTON.NS   | Crompton Greaves Consumer   | Mid   | Consumer Durables   |        1 |      0 |        1 |   0        | -1038.4    |        0        |   -1038.4    |  -1.04008   |
| PAGEIND.NS    | Page Industries             | Mid   | Consumer Durables   |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| INDHOTEL.NS   | Indian Hotels               | Mid   | Consumer Durables   |        1 |      0 |        1 |   0        | -1049.09   |        0        |   -1049.09   |  -1.06222   |
| WHIRLPOOL.NS  | Whirlpool India             | Mid   | Consumer Durables   |        1 |      0 |        1 |   0        |  -992.584  |        0        |    -992.584  |  -1.05913   |
| DIXON.NS      | Dixon Technologies          | Mid   | Consumer Durables   |        2 |      2 |        0 |   1        |  3120.12   |      inf        |    1560.06   |   1.9448    |
| SRF.NS        | SRF                         | Mid   | Chemicals           |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| PIIND.NS      | PI Industries               | Mid   | Chemicals           |        4 |      2 |        2 |   0.5      |  1551.54   |        1.73453  |     387.886  |   0.435765  |
| AARTIIND.NS   | Aarti Industries            | Mid   | Chemicals           |        2 |      2 |        0 |   1        |  3782.46   |      inf        |    1891.23   |   1.94078   |
| DEEPAKNTR.NS  | Deepak Nitrite              | Mid   | Chemicals           |        1 |      0 |        1 |   0        | -1034.65   |        0        |   -1034.65   |  -1.05581   |
| ATUL.NS       | Atul                        | Mid   | Chemicals           |        1 |      1 |        0 |   1        |  1449.39   |      inf        |    1449.39   |   1.90298   |
| BERGEPAINT.NS | Berger Paints               | Mid   | Chemicals           |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| UPL.NS        | UPL                         | Mid   | Chemicals           |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| ACC.NS        | ACC                         | Mid   | Cement              |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| AMBUJACEM.NS  | Ambuja Cements              | Mid   | Cement              |        2 |      2 |        0 |   1        |  3838.23   |      inf        |    1919.12   |   1.9436    |
| RAMCOCEM.NS   | Ramco Cements               | Mid   | Cement              |        1 |      0 |        1 |   0        | -1048.31   |        0        |   -1048.31   |  -1.07835   |
| SHREECEM.NS   | Shree Cement                | Mid   | Cement              |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| DALBHARAT.NS  | Dalmia Bharat               | Mid   | Cement              |        2 |      1 |        1 |   0.5      |   855.304  |        1.88271  |     427.652  |   0.450689  |
| ABB.NS        | ABB India                   | Mid   | Capital Goods       |        1 |      0 |        1 |   0        |  -938.761  |        0        |    -938.761  |  -1.05218   |
| SIEMENS.NS    | Siemens                     | Mid   | Capital Goods       |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| CUMMINSIND.NS | Cummins India               | Mid   | Capital Goods       |        1 |      1 |        0 |   1        |  1913.29   |      inf        |    1913.29   |   1.95967   |
| HONAUT.NS     | Honeywell Automation        | Mid   | Capital Goods       |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| THERMAX.NS    | Thermax                     | Mid   | Capital Goods       |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| BEL.NS        | Bharat Electronics          | Mid   | Capital Goods       |        3 |      2 |        1 |   0.666667 |  2838.39   |        3.72422  |     946.129  |   0.948661  |
| HAL.NS        | Hindustan Aeronautics       | Mid   | Capital Goods       |        2 |      1 |        1 |   0.5      |   971.076  |        2.01833  |     485.538  |   0.452951  |
| SAIL.NS       | Steel Authority of India    | Mid   | Metals & Mining     |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| NMDC.NS       | NMDC                        | Mid   | Metals & Mining     |        1 |      1 |        0 |   1        |  1934.7    |      inf        |    1934.7    |   1.93683   |
| VEDL.NS       | Vedanta                     | Mid   | Metals & Mining     |        2 |      1 |        1 |   0.5      |   815.642  |        1.73713  |     407.821  |   0.414222  |
| NATIONALUM.NS | National Aluminium          | Mid   | Metals & Mining     |        1 |      0 |        1 |   0        | -1028.42   |        0        |   -1028.42   |  -1.03034   |
| JINDALSTEL.NS | Jindal Steel & Power        | Mid   | Metals & Mining     |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| HINDPETRO.NS  | Hindustan Petroleum         | Mid   | Oil & Gas           |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| IOC.NS        | Indian Oil Corp             | Mid   | Oil & Gas           |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| PETRONET.NS   | Petronet LNG                | Mid   | Oil & Gas           |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| GAIL.NS       | GAIL India                  | Mid   | Oil & Gas           |        1 |      1 |        0 |   1        |  1946.5    |      inf        |    1946.5    |   1.95093   |
| DLF.NS        | DLF                         | Mid   | Real Estate         |        3 |      1 |        2 |   0.333333 |  -124.091  |        0.939907 |     -41.3636 |  -0.0483615 |
| GODREJPROP.NS | Godrej Properties           | Mid   | Real Estate         |        2 |      0 |        2 |   0        | -2061.72   |        0        |   -1030.86   |  -1.04466   |
| OBEROIRLTY.NS | Oberoi Realty               | Mid   | Real Estate         |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| PRESTIGE.NS   | Prestige Estates            | Mid   | Real Estate         |        3 |      1 |        2 |   0.333333 |  -124.444  |        0.938363 |     -41.4813 |  -0.0449286 |
| PHOENIXLTD.NS | Phoenix Mills               | Mid   | Real Estate         |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| CONCOR.NS     | Container Corp of India     | Mid   | Infrastructure      |        2 |      0 |        2 |   0        | -2122.08   |        0        |   -1061.04   |  -1.07223   |
| IRCTC.NS      | IRCTC                       | Mid   | Infrastructure      |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| EMAMILTD.NS   | Emami                       | Mid   | FMCG                |        2 |      2 |        0 |   1        |  3887.49   |      inf        |    1943.74   |   1.95272   |
| VBL.NS        | Varun Beverages             | Mid   | FMCG                |        1 |      1 |        0 |   1        |  1916.22   |      inf        |    1916.22   |   1.93459   |
| JUBLFOOD.NS   | Jubilant FoodWorks          | Mid   | FMCG                |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| TATACOMM.NS   | Tata Communications         | Mid   | Telecom             |        3 |      2 |        1 |   0.666667 |  2823      |        3.74203  |     941.001  |   0.960576  |
| KPITTECH.NS   | KPIT Technologies           | Small | IT                  |        2 |      2 |        0 |   1        |  3827.77   |      inf        |    1913.89   |   1.95097   |
| HAPPSTMNDS.NS | Happiest Minds              | Small | IT                  |        1 |      0 |        1 |   0        | -1047.24   |        0        |   -1047.24   |  -1.05335   |
| ROUTE.NS      | Route Mobile                | Small | IT                  |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| MASTEK.NS     | Mastek                      | Small | IT                  |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| SONATSOFTW.NS | Sonata Software             | Small | IT                  |        2 |      2 |        0 |   1        |  3881.57   |      inf        |    1940.78   |   1.94926   |
| GRANULES.NS   | Granules India              | Small | Pharma & Healthcare |        1 |      1 |        0 |   1        |  1916.47   |      inf        |    1916.47   |   1.9244    |
| LAURUSLABS.NS | Laurus Labs                 | Small | Pharma & Healthcare |        4 |      2 |        2 |   0.5      |  1734.21   |        1.84342  |     433.553  |   0.449988  |
| SYNGENE.NS    | Syngene International       | Small | Pharma & Healthcare |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| ASTRAZEN.NS   | AstraZeneca Pharma India    | Small | Pharma & Healthcare |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| FINEORG.NS    | Fine Organic Industries     | Small | Chemicals           |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| GALAXYSURF.NS | Galaxy Surfactants          | Small | Chemicals           |        1 |      0 |        1 |   0        | -1067.77   |        0        |   -1067.77   |  -1.06864   |
| BALAMINES.NS  | Balaji Amines               | Small | Chemicals           |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| SUDARSCHEM.NS | Sudarshan Chemical          | Small | Chemicals           |        1 |      1 |        0 |   1        |  1896.46   |      inf        |    1896.46   |   1.94258   |
| CLEAN.NS      | Clean Science & Technology  | Small | Chemicals           |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| ENDURANCE.NS  | Endurance Technologies      | Small | Automobile          |        1 |      0 |        1 |   0        |  -998.691  |        0        |    -998.691  |  -1.05091   |
| SUNDRMFAST.NS | Sundram Fasteners           | Small | Automobile          |        3 |      2 |        1 |   0.666667 |  2787.34   |        3.7464   |     929.113  |   0.951051  |
| TIINDIA.NS    | Tube Investments            | Small | Automobile          |        4 |      2 |        2 |   0.5      |  1875.19   |        2.00002  |     468.797  |   0.452575  |
| CDSL.NS       | Central Depository Services | Small | Banking & Finance   |        2 |      1 |        1 |   0.5      |   958.836  |        1.99658  |     479.418  |   0.459026  |
| UJJIVANSFB.NS | Ujjivan Small Finance Bank  | Small | Banking & Finance   |        1 |      0 |        1 |   0        | -1028.35   |        0        |   -1028.35   |  -1.03024   |
| EQUITASBNK.NS | Equitas SFB                 | Small | Banking & Finance   |        2 |      1 |        1 |   0.5      |   924.524  |        1.88617  |     462.262  |   0.460322  |
| RBLBANK.NS    | RBL Bank                    | Small | Banking & Finance   |        2 |      1 |        1 |   0.5      |   885.951  |        1.83109  |     442.976  |   0.445623  |
| CREDITACC.NS  | CreditAccess Grameen        | Small | Banking & Finance   |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| TTKPRESTIG.NS | TTK Prestige                | Small | Consumer Durables   |        1 |      0 |        1 |   0        | -1016.38   |        0        |   -1016.38   |  -1.05872   |
| RAJESHEXPO.NS | Rajesh Exports              | Small | Consumer Durables   |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| RADICO.NS     | Radico Khaitan              | Small | Consumer Durables   |        1 |      1 |        0 |   1        |  1516.95   |      inf        |    1516.95   |   1.54771   |
| ELGIEQUIP.NS  | Elgi Equipments             | Small | Capital Goods       |        2 |      1 |        1 |   0.5      |   952.88   |        1.95274  |     476.44   |   0.471595  |
| GRINDWELL.NS  | Grindwell Norton            | Small | Capital Goods       |        2 |      0 |        2 |   0        | -2029.18   |        0        |   -1014.59   |  -1.04897   |
| CARBORUNIV.NS | Carborundum Universal       | Small | Capital Goods       |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| PRAJIND.NS    | Praj Industries             | Small | Capital Goods       |        1 |      1 |        0 |   1        |  1951.7    |      inf        |    1951.7    |   1.95187   |
| AFFLE.NS      | Affle India                 | Small | Capital Goods       |        4 |      2 |        2 |   0.5      |  1785.81   |        1.8911   |     446.452  |   0.4517    |
| BLUEDART.NS   | Blue Dart Express           | Small | Infrastructure      |        3 |      2 |        1 |   0.666667 |  2543.48   |        3.88138  |     847.827  |   0.93748   |
| APLAPOLLO.NS  | APL Apollo Tubes            | Small | Infrastructure      |        3 |      1 |        2 |   0.333333 |  -181.448  |        0.911362 |     -60.4827 |  -0.058992  |
| ASTRAL.NS     | Astral                      | Small | Infrastructure      |        2 |      1 |        1 |   0.5      |   938.094  |        1.98387  |     469.047  |   0.445168  |
| RATNAMANI.NS  | Ratnamani Metals            | Small | Metals & Mining     |        3 |      1 |        2 |   0.333333 |  -237.138  |        0.880061 |     -79.0461 |  -0.0482032 |
| HLEGLAS.NS    | HLE Glascoat                | Small | Metals & Mining     |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| PVRINOX.NS    | PVR INOX                    | Small | Media               |        5 |      2 |        3 |   0.4      |   677.77   |        1.21552  |     135.554  |   0.134198  |
| RAYMOND.NS    | Raymond                     | Small | Textiles            |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| ARVIND.NS     | Arvind                      | Small | Textiles            |        1 |      0 |        1 |   0        | -1021.67   |        0        |   -1021.67   |  -1.0256    |
| TATAPOWER.NS  | Tata Power                  | Small | Power               |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| NHPC.NS       | NHPC                        | Small | Power               |        3 |      1 |        2 |   0.333333 |  -142.889  |        0.932271 |     -47.6296 |  -0.0469289 |
| SJVN.NS       | SJVN                        | Small | Power               |        1 |      1 |        0 |   1        |  1956.4    |      inf        |    1956.4    |   1.97383   |
| BRIGADE.NS    | Brigade Enterprises         | Small | Real Estate         |        1 |      1 |        0 |   1        |  1946.86   |      inf        |    1946.86   |   1.96439   |
| SOBHA.NS      | Sobha                       | Small | Real Estate         |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| JKCEMENT.NS   | JK Cement                   | Small | Cement              |        3 |      1 |        2 |   0.333333 |   -88.5825 |        0.954327 |     -29.5275 |  -0.0600654 |
| JKLAKSHMI.NS  | JK Lakshmi Cement           | Small | Cement              |        1 |      0 |        1 |   0        | -1025.85   |        0        |   -1025.85   |  -1.04184   |
| ZYDUSWELL.NS  | Zydus Wellness              | Small | FMCG                |        0 |      0 |        0 | nan        |     0      |      nan        |     nan      | nan         |
| MRPL.NS       | MRPL                        | Small | Oil & Gas           |        1 |      1 |        0 |   1        |  1973.1    |      inf        |    1973.1    |   1.97499   |

## 5. Market Cap Analysis
| cap   |   Trades |   Net_PnL |
|:------|---------:|----------:|
| Large |       68 |   10344.6 |
| Mid   |       88 |   33894.8 |
| Small |       65 |   27046.2 |

## 6. Sector Analysis
| sector              |   Trades |   Net_PnL |
|:--------------------|---------:|----------:|
| Automobile          |       23 |  8486.77  |
| Banking & Finance   |       43 |  5396.41  |
| Capital Goods       |       17 |  9236.77  |
| Cement              |       11 |  3048.49  |
| Chemicals           |       12 |  7343.73  |
| Consumer Durables   |       10 |  3196.94  |
| FMCG                |       12 |  2312.05  |
| IT                  |       13 |  7093.37  |
| Infrastructure      |       13 |  3824.82  |
| Media               |        5 |   677.77  |
| Metals & Mining     |       15 |  5022.62  |
| Oil & Gas           |        6 |  2627.56  |
| Pharma & Healthcare |       19 | 12213.9   |
| Power               |        7 | -1373.76  |
| Real Estate         |        9 |  -363.395 |
| Telecom             |        5 |  3563.27  |
| Textiles            |        1 | -1021.67  |

## 7. Regime Analysis
| trend_regime   |   Trades |   Net_PnL |
|:---------------|---------:|----------:|
| BEAR           |        4 |  4775.61  |
| BULL           |      180 | 66202.5   |
| SIDEWAYS       |       37 |   307.473 |

## 8. Statistical Analysis
- Win Rate 95% CI: 40.14% to 53.19%
- Mean R Bootstrap 95% CI: 0.13 to 0.54
- Expectancy Bootstrap 95% CI: ₹129.45 to ₹516.85

## 9. Monte Carlo Simulation (10,000 runs)
- Median Max Drawdown: ₹9,821.53
- 95th Percentile Max Drawdown: ₹16,976.74

## 10. Execution Audit
Checked: Stops/targets are calculated correctly from actual entry fill price, not signal close. Slippage and costs applied correctly.

## 11. Robustness & Limitations
Trades per stock per year: 0.21 - Extremely selective.
Top 3 trades contribution: 8.3%.
P&L without top 3 winners remains positive: True

## 12. Research Decision
**Promising but unconfirmed**. The strategy exhibits positive expectancy and a solid risk/reward distribution (Avg Win > Avg Loss), but trade frequency is exceptionally low and the universe suffers from survivorship bias.
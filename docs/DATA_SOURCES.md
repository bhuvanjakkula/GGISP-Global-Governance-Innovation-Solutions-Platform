# GGISP Platform: Official Multilateral Data Sources Specification

GGISP Platform v0.2 integrates official macroeconomic and trade data from three premier multilateral institutions: the **World Bank**, the **International Monetary Fund (IMF)**, and the **World Trade Organization (WTO)**.

---

## 1. World Bank Open Data & Indicators API

- **Base URL:** `http://api.worldbank.org/v2`
- **Authentication:** Public / No API key required
- **Format:** JSON
- **Key Indicators Integrated:**
  - `NY.GDP.MKTP.KD.ZG`: Real GDP Growth (annual %)
  - `GC.DOD.TOTL.GD.ZS`: Central Government Debt (% of GDP)
  - `DT.DOD.DECT.CD`: Total External Debt Stock (Current USD)
  - `DT.TDS.DECT.EX.ZS`: Debt Service (% of exports of goods, services & primary income)
  - `FP.CPI.TOTL.ZG`: Inflation, Consumer Prices (annual %)
  - `BN.CAB.XOKA.GD.ZS`: Current Account Balance (% of GDP)
  - `NE.EXP.GNFS.ZS`: Exports of Goods & Services (% of GDP)
  - `NE.IMP.GNFS.ZS`: Imports of Goods & Services (% of GDP)

---

## 2. International Monetary Fund (IMF)

- **Source:** IMF World Economic Outlook (WEO) & Article IV Consultations
- **Key Indicators Integrated:**
  - `GGXWDG_NGDP`: General Government Gross Debt (% of GDP)
  - `GGXCNL_NGDP`: General Government Net Lending/Borrowing (% of GDP)
  - `PCPIPCH`: Inflation, Average Consumer Prices (annual %)
  - `BCA_NGDPD`: Current Account Balance (% of GDP)
  - `DSA_RISK`: Joint IMF-World Bank Debt Sustainability Framework Risk Rating (Low, Moderate, High, In Debt Distress)
  - `IMF_PROGRAM_STATUS`: Extended Fund Facility (EFF), Extended Credit Facility (ECF), or Post-Financing Surveillance

---

## 3. World Trade Organization (WTO)

- **Source:** WTO World Tariff Profiles & WTO Timeseries API
- **Key Indicators Integrated:**
  - `MERCHANDISE_EXPORTS`: Total Merchandise Exports (Million USD)
  - `MERCHANDISE_IMPORTS`: Total Merchandise Imports (Million USD)
  - `MFN_APPLIED_TARIFF`: Simple Average Effectively Applied MFN Tariff (%)
  - `AGRICULTURAL_TARIFF`: Agricultural Products Applied Tariff Rate (%)
  - `NON_AGRI_TARIFF`: Non-Agricultural Products Tariff Rate (%)
  - `TRADE_OPENNESS`: Trade-to-GDP Ratio (%)
  - `TOP_SECTORS`: Major export commodities and supply chain categories

---

## 4. Fallback Architecture & Data Provenance

All live queries are executed with timeouts. When operating offline or in network-restricted environments, GGISP seamlessly serves authenticated benchmark indicator snapshots for sovereign economies (Kenya, Ghana, Sri Lanka, Argentina, Zambia, Vietnam, India, etc.). Every record is labeled with source citations and stored in the SQLite cache `external_indicators_cache`.

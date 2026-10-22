"""Unified Official Data Service integrating World Bank, IMF, and WTO."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ggisp.db import db
from ggisp.external_data.imf import IMFClient
from ggisp.external_data.world_bank import WorldBankClient
from ggisp.external_data.wto import WTOClient

logger = logging.getLogger(__name__)


class OfficialDataService:
    """Service to fetch, cache, and harmonize official data from World Bank, IMF, and WTO."""

    def __init__(self):
        self.world_bank = WorldBankClient()
        self.imf = IMFClient()
        self.wto = WTOClient()

    def get_unified_macro_profile(self, country_code: str) -> Dict[str, Any]:
        """Fetch and harmonize official indicators from World Bank, IMF, and WTO.
        Caches indicators in SQLite for fast reproducible simulations.
        """
        code = country_code.upper().strip()

        wb_profile = self.world_bank.get_country_summary(code)
        imf_profile = self.imf.get_country_fiscal_profile(code)
        wto_profile = self.wto.get_trade_profile(code)

        # Cache key indicators in SQLite
        try:
            with db() as con:
                con.execute("""
                    INSERT OR REPLACE INTO external_indicators_cache
                    (provider, country_code, indicator_code, indicator_name, year, value, unit)
                    VALUES
                    ('world_bank', ?, 'NY.GDP.MKTP.KD.ZG', 'GDP Growth', ?, ?, '%'),
                    ('world_bank', ?, 'GC.DOD.TOTL.GD.ZS', 'Government Debt', ?, ?, '% of GDP'),
                    ('imf', ?, 'GGXWDG_NGDP', 'Gross Debt', ?, ?, '% of GDP'),
                    ('imf', ?, 'GGXCNL_NGDP', 'Primary Balance', ?, ?, '% of GDP'),
                    ('wto', ?, 'MFN_TARIFF', 'Average MFN Tariff', ?, ?, '%')
                """, (
                    code, 2023, wb_profile.get("gdp_growth_percent"),
                    code, 2023, wb_profile.get("govt_debt_percent_gdp"),
                    code, imf_profile.get("year", 2024), imf_profile.get("gross_debt_percent_gdp"),
                    code, imf_profile.get("year", 2024), imf_profile.get("primary_balance_percent_gdp"),
                    code, wto_profile.get("year", 2023), wto_profile.get("simple_average_mfn_tariff_percent"),
                ))
        except Exception as e:
            logger.warning("Cache write failed: %s", e)

        # Harmonized calibrated baseline model inputs
        nominal_gdp_growth = (
            (1.0 + wb_profile["gdp_growth_percent"] / 100.0)
            * (1.0 + wb_profile["inflation_percent"] / 100.0)
            - 1.0
        ) * 100.0

        return {
            "country_code": code,
            "country_name": wb_profile["country_name"],
            "world_bank": wb_profile,
            "imf": imf_profile,
            "wto": wto_profile,
            "calibrated_model_defaults": {
                "initial_debt_percent_gdp": round(imf_profile["gross_debt_percent_gdp"], 2),
                "interest_rate_percent": round(imf_profile["effective_interest_rate_percent"], 2),
                "real_gdp_growth_percent": round(wb_profile["gdp_growth_percent"], 2),
                "inflation_percent": round(wb_profile["inflation_percent"], 2),
                "nominal_gdp_growth_percent": round(nominal_gdp_growth, 2),
                "primary_surplus_percent_gdp": round(imf_profile["primary_balance_percent_gdp"], 2),
                "foreign_debt_share_percent": 60.0,
                "base_exports_million_usd": round(wto_profile["merchandise_exports_million_usd"], 1),
                "base_tariff_percent": round(wto_profile["simple_average_mfn_tariff_percent"], 2),
            },
            "provenance": {
                "world_bank_source": wb_profile["source_citation"],
                "imf_source": imf_profile["source_citation"],
                "wto_source": wto_profile["source_citation"],
                "is_multilateral_official": True,
            }
        }

    def list_supported_countries(self) -> List[Dict[str, str]]:
        return [
            {"code": "KEN", "name": "Kenya", "region": "Sub-Saharan Africa"},
            {"code": "GHA", "name": "Ghana", "region": "West Africa"},
            {"code": "LKA", "name": "Sri Lanka", "region": "South Asia"},
            {"code": "ARG", "name": "Argentina", "region": "Latin America"},
            {"code": "ZMB", "name": "Zambia", "region": "Southern Africa"},
            {"code": "VNM", "name": "Vietnam", "region": "East Asia & Pacific"},
            {"code": "IND", "name": "India", "region": "South Asia"},
        ]

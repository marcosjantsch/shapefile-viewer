# -*- coding: utf-8 -*-
"""
config_urls.py — mapeia ANO -> URL do CSV.

Edite este arquivo e substitua as URLs de exemplo pelas URLs reais.
"""
import logging

logger = logging.getLogger(__name__)

CSV_URLS = {
    # Exemplos (troque por URLs reais):

    2000: "https://storage.googleapis.com/dadosclima/resumo_2000.csv",
    2009: "https://1drv.ms/x/c/8b88b81c064543d3/IQDLb7qydahpSbj24F33KOu2AbJv0e6TQx7Br6mckZYpab0?e=tyLkRy",
    2010: "https://1drv.ms/x/c/8b88b81c064543d3/IQDsxDFoo_gVQo8DkT663SaWATMtMOkj13qArrhsSs6rrIo?e=g1emf7",
    2011: "https://1drv.ms/x/c/8b88b81c064543d3/IQD_9qo0bqWXQr4XGQTN9btXAWCJWVrZmfv7Xuh3psKU8aM?e=vCGlWP",
    2012: "https://1drv.ms/x/c/8b88b81c064543d3/IQDfsPxnEqUDRrj9Edt6pLzOAfuf14v0lU4dwZqcNXrRvpI?e=3R7i9g",
    2013: "https://1drv.ms/x/c/8b88b81c064543d3/IQDA5vnCEMHDSJ_aghcsavk2AQoadKMRUABwH12KyKtZtJQ?e=5wWyr3",
    2014: "https://1drv.ms/x/c/8b88b81c064543d3/IQDVh_hXFzFgQaPhApPbqSqxATF460BAy6Zo2GmCfj6HU1c?e=x2jK55",
    2015: "https://1drv.ms/x/c/8b88b81c064543d3/IQCe-KA1yaJvRJjpwRNwEiKpAW3DIdp-E-iJVszNUPQ17R0?e=7kWYty",
    2016: "https://1drv.ms/x/c/8b88b81c064543d3/IQB2WSawbF2uQplLXeMRyPVEAcR2NFZC9zSRWeSLWDk3Wy4?e=Ts8dmF",
    2017: "https://1drv.ms/x/c/8b88b81c064543d3/IQCTtVB6SE_QRaXSArx1y4sNAVi1QLGjLRHsqGsIfECmFnc?e=f59PSB",
    2018: "https://1drv.ms/x/c/8b88b81c064543d3/IQCbkeT9FLuDT5srYJjueEcqAS3AFEvTK9-x8uXa4-H8F9Y?e=Ic6gcN",
    2019: "https://1drv.ms/x/c/8b88b81c064543d3/IQB391jNTNy1SarVNJyy_KD-AZ_XNxLyb9wUhhHMq76t3HY?e=dklP9A",
    2020: "https://1drv.ms/x/c/8b88b81c064543d3/IQB86FxjYCJARJxdho5CPR0oAa4W0L-qCEfIH5iEK8HrhrM?e=LX0hCS",
    2021: "https://1drv.ms/x/c/8b88b81c064543d3/IQD7_Hw6ob0wTYj3MY9nvjbRAfEPmamcUB0OvpfuyB6dYDE?e=Fu4JEp",
    2022: "https://1drv.ms/x/c/8b88b81c064543d3/IQC0UOfqmhKZS5Tg8n2LdoZ6AdeQnGzvQg1XKhxNbdk0lyU?e=Ia3tuU",
    2023: "https://1drv.ms/x/c/8b88b81c064543d3/IQBgV_Z6JB-XQZipw76c2mKQAQxloSWLKSrGP5aysU5v2Iw?e=rLio8f",
    2024: "https://1drv.ms/x/c/8b88b81c064543d3/IQBZmghrro3XQ6Bz8XWUu0WHAeHdEDXYqiUXN5IxOahSqLI?e=fPIepi",
    2025: "https://1drv.ms/x/c/8b88b81c064543d3/IQCibj9FcWOCQbswiNQl1MtcAfD2EyiGYsNHqhYrtAAcuAc?e=7Yevej",
    2026: "https://1drv.ms/x/c/8b88b81c064543d3/IQBWvTBVEXTVQKP288zxC9NNARd2kJMHFWecmteIaitSDoM?e=dQVahL",
    }

def load_urls():
    logger.info("URLs de CSV carregadas de config_urls.py.")
    return CSV_URLS

def get_url_by_year(urls_dict, year: int):
    return urls_dict.get(int(year))

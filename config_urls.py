# -*- coding: utf-8 -*-
"""
config_urls.py — mapeia ANO -> URL do CSV.

Edite este arquivo e substitua as URLs de exemplo pelas URLs reais.
"""
import logging

logger = logging.getLogger(__name__)

CSV_URLS = {
    # Exemplos (troque por URLs reais):


    2000: "https://storage.cloud.google.com/dadosclima/resumo_2000.csv",
    2001: "https://storage.cloud.google.com/dadosclima/resumo_2001.csv",
    2002: "https://storage.cloud.google.com/dadosclima/resumo_2002.csv",
    2003: "https://storage.cloud.google.com/dadosclima/resumo_2003.csv",
    2004: "https://storage.cloud.google.com/dadosclima/resumo_2004.csv",
    2005: "https://storage.cloud.google.com/dadosclima/resumo_2005.csv",
    2006: "https://storage.cloud.google.com/dadosclima/resumo_2006.csv",
    2007: "https://storage.cloud.google.com/dadosclima/resumo_2007.csv",
    2008: "https://storage.cloud.google.com/dadosclima/resumo_2008.csv",
    2009: "https://storage.cloud.google.com/dadosclima/resumo_2009.csv",
    2010: "https://storage.cloud.google.com/dadosclima/resumo_2010.csv",
    2011: "https://storage.cloud.google.com/dadosclima/resumo_2011.csv",
    2012: "https://storage.cloud.google.com/dadosclima/resumo_2012.csv",
    2013: "https://storage.cloud.google.com/dadosclima/resumo_2013.csv",
    2014: "https://storage.cloud.google.com/dadosclima/resumo_2014.csv",
    2015: "https://storage.cloud.google.com/dadosclima/resumo_2015.csv",
    2016: "https://storage.cloud.google.com/dadosclima/resumo_2016.csv",
    2017: "https://storage.cloud.google.com/dadosclima/resumo_2017.csv",
    2018: "https://storage.cloud.google.com/dadosclima/resumo_2018.csv",
    2019: "https://storage.cloud.google.com/dadosclima/resumo_2019.csv",
    2020: "https://storage.cloud.google.com/dadosclima/resumo_2020.csv",
    2021: "https://storage.cloud.google.com/dadosclima/resumo_2021.csv",
    2022: "https://storage.cloud.google.com/dadosclima/resumo_2022.csv",
    2023: "https://storage.cloud.google.com/dadosclima/resumo_2023.csv",
    2024: "https://storage.googleapis.com/dadosclima/resumo_2024.csv",
    2025: "https://storage.cloud.google.com/dadosclima/resumo_2025.csv",
    2026: "https://storage.cloud.google.com/dadosclima/resumo_2026.csv",
    }

def load_urls():
    logger.info("URLs de CSV carregadas de config_urls.py.")
    return CSV_URLS

def get_url_by_year(urls_dict, year: int):
    return urls_dict.get(int(year))

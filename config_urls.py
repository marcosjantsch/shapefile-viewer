# -*- coding: utf-8 -*-
"""
config_urls.py — mapeia ANO -> URL do CSV.

Edite este arquivo e substitua as URLs de exemplo pelas URLs reais.
"""
import logging

logger = logging.getLogger(__name__)

CSV_URLS = {
    # Exemplos (troque por URLs reais):
    2023: "https://1drv.ms/x/c/8b88b81c064543d3/IQASP70qtOUER43nSlVhRnyBAfwNm9Ftc3BMNi9akvMfJ4M?e=IDftjU",
    2024: "https://1drv.ms/x/c/8b88b81c064543d3/IQBRY9FjSoiYTbqQBlaf7ow9ARAhVOTqupUR70uECefpMs8?e=bHnkZu",
    2025: "https://1drv.ms/x/c/8b88b81c064543d3/IQDEpcmoHOHLSYwHj8uo99hqAVYedbu5TwWoMlLZX1MwYNI?e=pQqOig",
    }

def load_urls():
    logger.info("URLs de CSV carregadas de config_urls.py.")
    return CSV_URLS

def get_url_by_year(urls_dict, year: int):
    return urls_dict.get(int(year))

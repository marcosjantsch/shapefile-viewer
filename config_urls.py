# -*- coding: utf-8 -*-
"""
config_urls.py — mapeia ANO -> URL do CSV.

Edite este arquivo e substitua as URLs de exemplo pelas URLs reais.
"""
import logging

logger = logging.getLogger(__name__)

CSV_URLS = {
    # Exemplos (troque por URLs reais):
    2010: "",
    2011: "",
    2012: "",
    2013: "https://1drv.ms/x/c/8b88b81c064543d3/IQCoP83W-FYER5KQu8DBuTTaAWacNQ23ZuxXLpHH_-NMqZ4?e=rdeZd5",
    2014: "",
    2015: "https://1drv.ms/x/c/8b88b81c064543d3/IQBomFaAecYAQL4Nsbj0Rzr0AaWsk2ixz4heNKF9Lu3r8ug?e=Xy7VGU",
    2016: "https://1drv.ms/x/c/8b88b81c064543d3/IQAq1c_k3axXRLWxLt8SQu3BARRlXjhe-6rHVYqaGUqoWXQ?e=ic1tLV",
    2017: "https://1drv.ms/x/c/8b88b81c064543d3/IQDc3zffIXaSRpGrWZ01szLrAY_uynjSzFZBwOn8TmRoBgw?e=OHUat0",
    2018: "https://1drv.ms/x/c/8b88b81c064543d3/IQBS7Tn8RT-wSphRRctnk360AX9-hRShvBHFNumXwT_v-ms?e=hOmMM7",
    2019: "https://1drv.ms/x/c/8b88b81c064543d3/IQAcbjTDEi04T4wVyRXUpD23AUinaaHENIyzFPFzGTid61Q?e=jz4roh",
    2020: "https://1drv.ms/x/c/8b88b81c064543d3/IQDY095rujPVT7AYeGFZRS0nASKL043IU_XNnPiXfP3rPX0?e=IQMbqu",
    2021: "https://1drv.ms/x/c/8b88b81c064543d3/IQDSHMP3TVnPQJ31tZI6-cjbAf9G3uglIzVlcLBOR7U-rok?e=aMc8UW",
    2022: "https://1drv.ms/x/c/8b88b81c064543d3/IQB7ufC0vxdtTbx2IWljufoMAXn9BT07BTaml3pvDIw59Zw?e=SwZndk",
    2023: "https://1drv.ms/x/c/8b88b81c064543d3/IQASP70qtOUER43nSlVhRnyBAfwNm9Ftc3BMNi9akvMfJ4M?e=gxf0iQ",
    2024: "https://1drv.ms/x/c/8b88b81c064543d3/IQBRY9FjSoiYTbqQBlaf7ow9ARAhVOTqupUR70uECefpMs8?e=crUVdI",
    2025: "https://1drv.ms/x/c/8b88b81c064543d3/IQDEpcmoHOHLSYwHj8uo99hqAVYedbu5TwWoMlLZX1MwYNI?e=mNJvcU",
    }

def load_urls():
    logger.info("URLs de CSV carregadas de config_urls.py.")
    return CSV_URLS

def get_url_by_year(urls_dict, year: int):
    return urls_dict.get(int(year))


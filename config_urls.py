# -*- coding: utf-8 -*-
"""
config_urls.py — mapeia ANO -> URL do CSV.

Edite este arquivo e substitua as URLs de exemplo pelas URLs reais.
"""
import logging

logger = logging.getLogger(__name__)

CSV_URLS = {
    # Exemplos (troque por URLs reais):


    2000: "https://1drv.ms/x/c/8b88b81c064543d3/IQALpk90k3cYQKdrdAuH__AoATR4TCXaxvZUQinW1QQ7wHs?e=SZWRjU",
    2001: "https://1drv.ms/x/c/8b88b81c064543d3/IQCLCANPrAUiS4M0zgxm7e9kAWhdyAqaZzFg15CddDnZYxA?e=s0VxSl",
    2002: "https://1drv.ms/x/c/8b88b81c064543d3/IQC7fiYAUiARTJFS4x99OJboAaSU_HJ0zzNn2VNtGXSzyZ4?e=xaciqI",
    2003: "https://1drv.ms/x/c/8b88b81c064543d3/IQBkEiTPSsaUT6_4NJPmjWZnAb3dW0EEkvzIdcxLkPfccOY?e=hcFHeB",
    2004: "https://1drv.ms/x/c/8b88b81c064543d3/IQAPba108BCZRJ8WufotnbMpAWaOlE30dYKSSHKHrF1bvH4?e=NFpN1m",
    2005: "https://1drv.ms/x/c/8b88b81c064543d3/IQD7fdKR0QFkSIXo_BrKho7cAQ-FFOzTbnOC2tLXwTTETGM?e=eYuy1f",
    2006: "https://1drv.ms/x/c/8b88b81c064543d3/IQBTw116eGGjTp5TpQ1_3TJMAQ-xKEDhCgB9pxSLVcrUlD4?e=c6J5M1",
    2007: "https://1drv.ms/x/c/8b88b81c064543d3/IQC2c9c9QDDlQ4Z0aEvI7R5BARN8NehByLo1w_LXfVDZtrI?e=gOOkLy",
    2008: "https://1drv.ms/x/c/8b88b81c064543d3/IQC6xGycEs0tRZhoAMtqpm-qAa68_IwtSLRE7DenwEE2pYM?e=T6xQGr",
    2009: "https://1drv.ms/x/c/8b88b81c064543d3/IQDTnegXH4msTovA0d3PTpa_ASGA8Gve4T_YjSccLhFHdJw?e=FUfsdN",
    2010: "https://1drv.ms/x/c/8b88b81c064543d3/IQCAZEcubosvTauvEfcUdd6UAYyNQ-tqjBWc0jKSaXicbAc?e=ZAgkZT",
    2011: "https://1drv.ms/x/c/8b88b81c064543d3/IQBu6_wcOZTiQbq4OnDGZzRcAc_tKmxRR3bHCMnTUee8YIo?e=uFUFLU",
    2012: "https://1drv.ms/x/c/8b88b81c064543d3/IQCGGfgYAdd8QYyZvf5mS8NXASetzv6F2gN8tr60eTYuSo0?e=VVMux6",
    2013: "https://1drv.ms/x/c/8b88b81c064543d3/IQDsfv2o-g8mRI3aEp9D9HLzAZBF9EQTumeyDiinHLi3y-Q?e=eq3CGE",
    2014: "https://1drv.ms/x/c/8b88b81c064543d3/IQDqRkihtemZR47aKEU26rL9AZT_1V9JBbOljwJN4xsCAJc?e=GQarhS",
    2015: "https://1drv.ms/x/c/8b88b81c064543d3/IQD620di07mkRajGG1jTuZqUAVUfHXUG5lO0BC9vdGqHVik?e=FXZIzg",
    2016: "https://1drv.ms/x/c/8b88b81c064543d3/IQCb-4x8myUfTbX-A1yZHCn0ARomUJK7EThDxxjfQOnJqlc?e=mtpUww",
    2017: "https://1drv.ms/x/c/8b88b81c064543d3/IQCDbsRyya78R5pWhWEPFlKFAW0uZow8w4BFk0ixyYziOps?e=JOGgWM",
    2018: "https://1drv.ms/x/c/8b88b81c064543d3/IQDbuBlxYoBCQYmY2DoOkb0-AWAB3Z2oSGLgOfew55GMLCg?e=tuMvdx",
    2019: "https://1drv.ms/x/c/8b88b81c064543d3/IQAx0B_IXcHXRpIDChAtDNGRARxq30zDgRlUKBx2BW8IdUc?e=wVhx3M",
    2020: "https://1drv.ms/x/c/8b88b81c064543d3/IQDBqE13VQCNT5M0WRmXEujmASZbsxZE9JsCRM7k0a0hk5Q?e=5grnhg",
    2021: "https://1drv.ms/x/c/8b88b81c064543d3/IQD-2fTO6W4OT7gE-eJiimzjAdF8f14yRYA1n5gdvi-TS0E?e=ELkUNc",
    2022: "https://1drv.ms/x/c/8b88b81c064543d3/IQDafzJf58uLQpmoqK24eRa1ARQCTUau0Fj3iOaRtYF_aCs?e=n15QkN",
    2023: "https://1drv.ms/x/c/8b88b81c064543d3/IQDWcPwbuXuUR7nm-jw1wRBdAXVFx7BNigLM5Cw9LOCmjyA?e=PzuC7G",
    2024: "https://1drv.ms/x/c/8b88b81c064543d3/IQDIjt0hG_ROQ4hlJxcN_4EeAXv4g8395dWy5QKRbBRf1oY?e=Yk5tGZ",
    2025: "https://1drv.ms/x/c/8b88b81c064543d3/IQCfLJmZjRKLTpX_XjvQkZ-eARNbhqjei04FShweX-0vyq4?e=DfC364",
    2026: "https://1drv.ms/x/c/8b88b81c064543d3/IQAfTBS5PxeyR7Pk5npqZUwtATEtkzMShAzIk3ZmX82D6XU?e=Fvc8Z6",
    }

def load_urls():
    logger.info("URLs de CSV carregadas de config_urls.py.")
    return CSV_URLS

def get_url_by_year(urls_dict, year: int):
    return urls_dict.get(int(year))

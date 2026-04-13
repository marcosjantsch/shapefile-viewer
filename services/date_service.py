# services/date_service.py
import pandas as pd


def parse_date_safe(series: pd.Series) -> pd.Series:
    """
    Converte uma série de datas para datetime de forma robusta.
    
    Prioridade:
    1. Formato padrão do banco: YYYY/MM/DD
    2. Fallback automático (caso venha outro formato inesperado)

    Retorna:
        pd.Series datetime (ou NaT em caso de erro)
    """

    if series is None:
        return series

    s = series.astype(str).str.strip()

    # 1. TENTATIVA PRINCIPAL — formato padrão do banco
    dt = pd.to_datetime(s, format="%Y/%m/%d", errors="coerce")

    # 2. FALLBACK — para casos fora do padrão
    mask_invalid = dt.isna()

    if mask_invalid.any():
        dt_fallback = pd.to_datetime(
            s[mask_invalid],
            errors="coerce",
            infer_datetime_format=True,
        )
        dt.loc[mask_invalid] = dt_fallback

    return dt


def enrich_date_columns(df: pd.DataFrame, col: str = "DATA") -> pd.DataFrame:
    """
    Padroniza e cria colunas derivadas de data.

    Gera:
        - DATA (datetime)
        - ANO
        - MES (numérico)
        - MES_NOME (pt-BR)
        - MES_ANO (YYYY-MM)
    """

    if col not in df.columns:
        return df

    df = df.copy()

    df[col] = parse_date_safe(df[col])
    df = df.dropna(subset=[col])

    meses_pt = {
        1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
        7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"
    }

    df["ANO"] = df[col].dt.year
    df["MES"] = df[col].dt.month
    df["MES_NOME"] = df[col].dt.month.map(meses_pt)
    df["MES_ANO"] = df[col].dt.strftime("%Y-%m")

    return df


def format_date_display(df: pd.DataFrame, col: str = "DATA") -> pd.DataFrame:
    """
    Apenas para exibição — NÃO usar antes de cálculos.
    """

    if col in df.columns:
        df[col] = df[col].dt.strftime("%d-%m-%Y")

    return df
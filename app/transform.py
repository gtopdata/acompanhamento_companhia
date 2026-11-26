'''imports'''
import pandas as pd


def group_data(
    df: pd.DataFrame,
    coluna_agrupar: str
) -> pd.DataFrame:
    '''agrupa'''
    colunas_metricas = [
        "Venda"
    ]
    return (
        df.groupby(coluna_agrupar)[colunas_metricas]
        .sum()
        .reset_index()
        .sort_values(by="Venda", ascending=False)
    )

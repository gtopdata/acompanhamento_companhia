'''calculo das metricas do relatorio a partir da base fato_gestao_diaria_loja

Flags da base:
    FlagMes=0, FlagDia=0 -> acumulado do ano
    FlagMes=1, FlagDia=0 -> acumulado do mes atual
    FlagMes=1, FlagDia=1 -> dia anterior
'''
from dataclasses import dataclass, field
from datetime import date

import pandas as pd

from app.unidades import UNIDADES

COL_UNIDADE = "%IdUnidade"

PERIODOS = {
    "dia": (1, 1),
    "mes": (1, 0),
    "ano": (0, 0),
}


def _div(a, b):
    '''divisao segura: None quando denominador e zero/ausente'''
    if b is None or pd.isna(b) or b == 0 or a is None or pd.isna(a):
        return None
    return a / b


@dataclass
class Indicadores:
    venda: float = 0.0
    meta: float = 0.0
    margem_valor: float = 0.0
    meta_margem_valor: float = 0.0
    cupons: float = 0.0
    venda_ano_anterior: float | None = None

    @property
    def tem_meta(self) -> bool:
        return self.meta > 0

    @property
    def atingimento(self):
        return _div(self.venda, self.meta)

    @property
    def saldo(self):
        return self.venda - self.meta if self.tem_meta else None

    @property
    def margem(self):
        return _div(self.margem_valor, self.venda)

    @property
    def meta_margem(self):
        return _div(self.meta_margem_valor, self.meta)

    @property
    def desvio_margem(self):
        if self.margem is None or self.meta_margem is None:
            return None
        return self.margem - self.meta_margem

    @property
    def ticket(self):
        return _div(self.venda, self.cupons)

    @property
    def vs_ano_anterior(self):
        r = _div(self.venda, self.venda_ano_anterior)
        return None if r is None else r - 1


@dataclass
class Periodo:
    nome: str
    total: Indicadores
    unidades: list = field(default_factory=list)  # [(codigo, nome, Indicadores)]


def _indicadores(linhas: pd.DataFrame, linhas_ant: pd.DataFrame) -> Indicadores:
    venda_ant = linhas_ant["Venda"].sum() if len(linhas_ant) else None
    return Indicadores(
        venda=float(linhas["Venda"].sum()),
        meta=float(linhas["Meta Venda"].sum()),
        margem_valor=float(linhas["Margem"].sum()),
        meta_margem_valor=float(linhas["Meta Margem"].sum()),
        cupons=float(linhas["Qtde. Dcto"].sum()),
        venda_ano_anterior=None if venda_ant is None else float(venda_ant),
    )


def calcular_periodo(df: pd.DataFrame, nome: str, ano: int) -> Periodo:
    flag_mes, flag_dia = PERIODOS[nome]
    base = df[
        (df["FlagMes"] == flag_mes)
        & (df["FlagDia"] == flag_dia)
        & (df[COL_UNIDADE].isin(UNIDADES))
    ]
    atual = base[base["Ano"] == ano]
    anterior = base[base["Ano"] == ano - 1]

    unidades = []
    for codigo, nome_unidade in UNIDADES.items():
        ind = _indicadores(
            atual[atual[COL_UNIDADE] == codigo],
            anterior[anterior[COL_UNIDADE] == codigo],
        )
        unidades.append((codigo, nome_unidade, ind))

    return Periodo(nome=nome, total=_indicadores(atual, anterior), unidades=unidades)


def calcular_relatorio(df: pd.DataFrame, data_ref: date) -> dict[str, Periodo]:
    return {nome: calcular_periodo(df, nome, data_ref.year) for nome in PERIODOS}

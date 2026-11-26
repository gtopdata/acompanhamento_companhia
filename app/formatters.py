'''formatadores de exibicao (padrao brasileiro)'''
import math


def _br(valor: float, casas: int = 2) -> str:
    texto = f"{abs(valor):,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def _sinal(valor: float, mostrar_mais: bool) -> str:
    if valor < 0:
        return "-"
    return "+" if mostrar_mais else ""


def vazio(valor) -> bool:
    return valor is None or (isinstance(valor, float) and math.isnan(valor))


def formatar_moeda(valor: float) -> str:
    '''R$ 1.083.087.206,00'''
    return f"{'-' if valor < 0 else ''}R$ {_br(valor)}"


def inteiro(valor: float) -> str:
    '''1.028.754 (sem sinal de mais; negativo com "-")'''
    if vazio(valor):
        return "-"
    return f"{'-' if round(valor) < 0 else ''}{_br(round(valor), 0)}"


def saldo(valor: float) -> str:
    '''+2.645 / -16.726'''
    if vazio(valor):
        return "-"
    return f"{_sinal(round(valor), True)}{_br(round(valor), 0)}"


def moeda_compacta(valor: float, mostrar_mais: bool = False) -> str:
    '''R$ 2,14 mi | R$ 15,8 mil | -R$ 3,47 mi'''
    if vazio(valor):
        return "-"
    s = _sinal(valor, mostrar_mais)
    a = abs(valor)
    if a >= 1_000_000:
        return f"{s}R$ {_br(a / 1_000_000)} mi"
    if a >= 1_000:
        return f"{s}R$ {_br(a / 1_000, 1)} mil"
    return f"{s}R$ {_br(a, 0)}"


def percentual(valor: float, mostrar_mais: bool = False) -> str:
    '''Recebe fracao (0.9927) -> 99,27%'''
    if vazio(valor):
        return "-"
    return f"{_sinal(valor, mostrar_mais)}{_br(valor * 100)}%"


def pontos_percentuais(valor: float) -> str:
    '''Recebe fracao (-0.0059) -> -0,59 p.p.'''
    if vazio(valor):
        return "-"
    return f"{_sinal(valor, True)}{_br(valor * 100)} p.p."


def ticket(valor: float) -> str:
    if vazio(valor):
        return "-"
    return f"R$ {_br(valor)}"

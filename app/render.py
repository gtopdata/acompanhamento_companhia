"""monta o contexto das paginas e gera o PDF (Jinja2 + Chromium via Playwright)"""
import os
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app import formatters as f
from app.metrics import Indicadores, Periodo

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
MESES = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]

# Largura x altura da pagina em px (mesma proporcao da proposta)
PAGE_W, PAGE_H = 1308, 924


def _tom(valor, limite=0.0):
    """classe de cor: positivo (verde) / negativo (vermelho) / neutro"""
    if valor is None:
        return ""
    return "pos" if valor >= limite else "neg"


def _sinal_tom(valor):
    return _tom(valor, 0.0)


def _ating_tom(valor):
    return _tom(valor, 1.0)


def _compacta_mi(valor):
    """R$ 82,60 mi (sempre em milhoes, como na proposta)"""
    if f.vazio(valor):
        return "-"
    return f"R$ {f._br(valor / 1_000_000)} mi"


def _extra_meta_margem(t: Indicadores) -> str:
    if t.meta_margem is None:
        return ""
    return f"Meta de margem: {f.percentual(t.meta_margem)} | Desvio: {f.pontos_percentuais(t.desvio_margem)}"


# ---------------------------------------------------------------- pagina 1
def _cartao_resumo(titulo, datas, classe, p: Periodo, extra: str, extra_tom: str = ""):
    t: Indicadores = p.total
    return {
        "titulo": titulo,
        "datas": datas,
        "classe": classe,
        "venda_compacta": _compacta_mi(t.venda),
        "venda_exata": f"R$ {f.inteiro(t.venda)}",
        "meta_label": "Meta do dia" if p.nome == "dia" else "Meta acumulada até a data",
        "meta": f"R$ {f.inteiro(t.meta)}",
        "ating": f.percentual(t.atingimento),
        "ating_tom": _ating_tom(t.atingimento),
        "saldo": f.moeda_compacta(t.saldo, mostrar_mais=True),
        "saldo_tom": _sinal_tom(t.saldo),
        "margem": f.percentual(t.margem),
        "cupons": f.inteiro(t.cupons) if t.cupons else "-",
        "ticket": f.ticket(t.ticket),
        "vs": f.percentual(t.vs_ano_anterior, mostrar_mais=True),
        "vs_tom": _sinal_tom(t.vs_ano_anterior),
        "extra": extra,
        "extra_tom": extra_tom,
    }


def pagina_resumo(rel, data_ref: date, com_departamentos: bool) -> dict:
    dia, mes, ano = rel["dia"], rel["mes"], rel["ano"]
    d = data_ref.strftime("%d/%m/%Y")
    cartoes = [
        _cartao_resumo("DIA ANTERIOR", d, "azul", dia, ""),
        _cartao_resumo(
            "ACUMULADO DO MÊS", f"01/{data_ref:%m} a {d}", "verde-agua", mes,
            _extra_meta_margem(mes.total), _sinal_tom(mes.total.desvio_margem),
        ),
        _cartao_resumo(
            "ACUMULADO DO ANO", f"01/01 a {d}", "roxo", ano,
            "Margem anual conforme o arquivo de origem.",
        ),
    ]
    destino = "unidades na pág. 2"
    if com_departamentos:
        destino += " e departamentos na pág. 3"
    return {
        "tipo": "resumo",
        "titulo": "Gestão do dia, mês e ano",
        "subtitulo": "Três horizontes de gestão | Metas e resultados sempre comparados dentro do mesmo período",
        "acento": "azul",
        "cartoes": cartoes,
        "foco": f"Onde ficou o desvio de ontem? Consulte {destino}.",
        # A base so tem uma coluna de meta; a meta total do periodo ainda nao esta disponivel
        "meta_total_mes": "n/d",
        "falta_mes": "n/d",
        "meta_total_ano": "n/d",
        "falta_ano": "n/d",
    }


# --------------------------------------------------------- paginas de unidades
def _c(texto, cls=""):
    return {"t": texto, "c": cls}


def _cartoes_unidades(p: Periodo):
    com_meta = [(cod, nome, i) for cod, nome, i in p.unidades if i.tem_meta]
    abaixo = [x for x in com_meta if x[2].saldo < 0]
    pior = min(com_meta, key=lambda x: x[2].saldo, default=None)
    melhor = max(com_meta, key=lambda x: x[2].saldo, default=None)
    cartoes = [
        {"rotulo": "ABAIXO DA META DE VENDAS", "valor": f"{len(abaixo)} de {len(com_meta)} unidades",
         "tom": "neg", "sub": "Recorte de unidades com meta"},
    ]
    if pior and pior[2].saldo < 0:
        cartoes.append({"rotulo": "MAIOR DÉFICIT", "valor": f.moeda_compacta(pior[2].saldo),
                        "tom": "neg", "sub": f"{pior[0]} - {pior[1]}"})
    else:
        cartoes.append({"rotulo": "MAIOR DÉFICIT", "valor": "Nenhum", "tom": "pos", "sub": "Todas na meta"})
    if melhor and melhor[2].saldo > 0:
        cartoes.append({"rotulo": "MAIOR SUPERÁVIT", "valor": f.moeda_compacta(melhor[2].saldo, True),
                        "tom": "pos", "sub": f"{melhor[0]} - {melhor[1]}"})
    else:
        cartoes.append({"rotulo": "MAIOR SUPERÁVIT", "valor": "Nenhum", "tom": "neg", "sub": "Nenhuma acima da meta"})
    return cartoes


def pagina_unidades(p: Periodo, data_ref: date) -> dict:
    d = data_ref.strftime("%d/%m/%Y")
    cfg = {
        "dia": dict(titulo="Dia anterior | Unidades", acento="azul", sub=d,
                    meta="Meta R$", venda="Venda R$"),
        "mes": dict(titulo="Acumulado do mês | Unidades", acento="verde-agua", sub=f"01/{data_ref:%m} a {d}",
                    meta="Meta acum. R$", venda="Venda acum. R$"),
        "ano": dict(titulo="Acumulado do ano | Unidades", acento="roxo", sub=f"01/01 a {d}",
                    meta="Meta acum. R$", venda="Venda acum. R$"),
    }[p.nome]

    if p.nome == "dia":
        colunas = [cfg["meta"], cfg["venda"], "Ating.", "Saldo R$", "Margem", "Cupons", "Ticket R$"]
    elif p.nome == "mes":
        colunas = [cfg["meta"], cfg["venda"], "Ating.", "Saldo R$", "Margem", "Desvio marg.", "vs. 2025"]
    else:
        colunas = [cfg["meta"], cfg["venda"], "Ating.", "Saldo R$", "Margem", "vs. 2025", "Ticket R$"]

    linhas = []
    for cod, nome, i in p.unidades:
        base = [
            _c(f.inteiro(i.meta)),
            _c(f.inteiro(i.venda)),
            _c(f.percentual(i.atingimento), "b " + _ating_tom(i.atingimento)),
            _c(f.saldo(i.saldo), "b " + _sinal_tom(i.saldo)),
            _c(f.percentual(i.margem)),
        ]
        vs = _c(f.percentual(i.vs_ano_anterior, True), _sinal_tom(i.vs_ano_anterior))
        tk = _c(f.ticket(i.ticket))
        cupons = _c(f.inteiro(i.cupons))
        if p.nome == "dia":
            extra = [cupons, tk]
        elif p.nome == "mes":
            extra = [_c(f.pontos_percentuais(i.desvio_margem), _sinal_tom(i.desvio_margem)), vs]
        else:
            extra = [vs, tk]
        linhas.append({"unidade": f"{cod} - {nome}", "celulas": base + extra})

    nota1 = "Ordem fixa por código da unidade para facilitar a comparação entre dia, mês e ano. Saldo = venda - meta do período."
    nota2 = {
        "dia": "Meta zero: atingimento e saldo não calculados. Cupons e ticket preservados conforme o escopo de origem.",
        "mes": 'Desvio de margem = margem realizada - meta de margem, em pontos percentuais. "-" indica meta ou base não disponível.',
        "ano": "Atingimento anual calculado sobre a meta acumulada até a data de referência.",
    }[p.nome]

    return {
        "tipo": "unidades",
        "titulo": cfg["titulo"],
        "subtitulo": f"{cfg['sub']} | Venda das unidades conforme a origem; linhas de pré-venda fora desta tabela",
        "acento": cfg["acento"],
        "cartoes": _cartoes_unidades(p),
        "colunas": colunas,
        "linhas": linhas,
        "notas": [nota1, nota2],
    }


# ------------------------------------------------------------------- render
def montar_paginas(rel, data_ref: date) -> list[dict]:
    # Paginas de departamentos entram aqui quando a base existir
    paginas = [
        pagina_resumo(rel, data_ref, com_departamentos=False),
        pagina_unidades(rel["dia"], data_ref),
        pagina_unidades(rel["mes"], data_ref),
        pagina_unidades(rel["ano"], data_ref),
    ]
    for n, pg in enumerate(paginas, 1):
        pg["num"] = f"{n:02d} / {len(paginas):02d}"
    return paginas


def renderizar_html(rel, data_ref: date) -> str:
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html"]),
    )
    return env.get_template("report.html").render(
        paginas=montar_paginas(rel, data_ref),
        data_cabecalho=f"{data_ref.day:02d} {MESES[data_ref.month - 1]} {data_ref.year}",
        data_ref=data_ref.strftime("%d/%m/%Y"),
        page_w=PAGE_W,
        page_h=PAGE_H,
    )


def gerar_pdf(html: str, destino: Path) -> Path:
    """Renderiza o HTML em PDF.

    Local (Windows): usa o Edge instalado (PLAYWRIGHT_CHANNEL=msedge, padrao).
    Docker: defina PLAYWRIGHT_CHANNEL= (vazio) para usar o Chromium do Playwright.
    """
    from playwright.sync_api import sync_playwright

    canal = os.environ.get("PLAYWRIGHT_CHANNEL", "msedge" if os.name == "nt" else "") or None
    destino.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel=canal)
        page = browser.new_page()
        page.set_content(html, wait_until="load")
        page.pdf(
            path=str(destino),
            width=f"{PAGE_W}px",
            height=f"{PAGE_H}px",
            print_background=True,
            prefer_css_page_size=True,
        )
        browser.close()
    return destino

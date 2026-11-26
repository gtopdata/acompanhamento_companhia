"""gera o relatorio diario de gestao em PDF"""
import argparse
from datetime import date, datetime, timedelta

from app import config
from app import extract
from app import metrics
from app import render


def main():
    parser = argparse.ArgumentParser(description="Gera o PDF de gestão do dia, mês e ano")
    parser.add_argument(
        "--data",
        help="Data de referência (dia anterior) no formato DD/MM/AAAA. Padrão: ontem.",
    )
    args = parser.parse_args()

    data_ref = (
        datetime.strptime(args.data, "%d/%m/%Y").date()
        if args.data
        else date.today() - timedelta(days=1)
    )

    df = extract.load_data(config.INPUT_DIR / "fato_gestao_diaria_loja.parquet")
    rel = metrics.calcular_relatorio(df, data_ref)
    html = render.renderizar_html(rel, data_ref)

    (config.OUTPUT_DIR / "relatorio.html").write_text(html, encoding="utf-8")
    pdf = render.gerar_pdf(html, config.OUTPUT_DIR / f"gestao_{data_ref:%Y%m%d}.pdf")
    print(f"PDF gerado: {pdf}")


if __name__ == "__main__":
    main()

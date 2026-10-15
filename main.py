from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from datetime import datetime
from decimal import Decimal, InvalidOperation
from io import BytesIO

app = Flask(__name__, template_folder="Templates", static_folder="static")
app.secret_key = "credmais_chave_local"

movimentacoes = [
    {
        "data": "02/10",
        "tipo": "Parcela do Empréstimo",
        "categoria": "Despesa",
        "valor": 941.45
    },
    {
        "data": "07/09",
        "tipo": "Pagamento",
        "categoria": "Receita",
        "valor": 1621.00
    },
    {
        "data": "02/09",
        "tipo": "Parcela do Empréstimo",
        "categoria": "Despesa",
        "valor": 941.45
    },
    {
        "data": "02/07",
        "tipo": "Empréstimo",
        "categoria": "Receita",
        "valor": 10000.00
    }
]


@app.route("/")
@app.route("/movimentacoes")
def inicio():
    receitas = sum(
        item["valor"]
        for item in movimentacoes
        if item["categoria"] == "Receita"
    )

    despesas = sum(
        item["valor"]
        for item in movimentacoes
        if item["categoria"] == "Despesa"
    )

    saldo = receitas - despesas

    return render_template(
        "index.html",
        dados=movimentacoes,
        saldo=saldo,
        receitas=receitas,
        despesas=despesas
    )


@app.route("/nova-movimentacao", methods=["GET", "POST"])
def nova_movimentacao():
    if request.method == "POST":
        tipo = request.form.get("tipo", "").strip()
        categoria = request.form.get("categoria", "").strip()
        valor = request.form.get("valor", "").strip()

        if not tipo:
            flash("Informe o tipo de movimentação.", "erro")
            return redirect(url_for("nova_movimentacao"))

        if categoria not in ("Receita", "Despesa"):
            flash("Selecione Receita ou Despesa.", "erro")
            return redirect(url_for("nova_movimentacao"))

        try:
            valor_numerico = Decimal(
                valor.replace(".", "").replace(",", ".")
                if "," in valor
                else valor
            )

            if not valor_numerico.is_finite() or valor_numerico <= 0:
                raise InvalidOperation

        except (InvalidOperation, ValueError):
            flash("Informe um valor válido maior que zero.", "erro")
            return redirect(url_for("nova_movimentacao"))

        movimentacoes.insert(0, {
            "data": datetime.now().strftime("%d/%m"),
            "tipo": tipo,
            "categoria": categoria,
            "valor": float(valor_numerico)
        })

        flash("Movimentação registrada com sucesso!", "sucesso")
        return redirect(url_for("inicio"))

    return render_template("nova_movimentacao.html")


@app.route("/relatorio")
def relatorio():
    receitas = sum(
        item["valor"]
        for item in movimentacoes
        if item["categoria"] == "Receita"
    )

    despesas = sum(
        item["valor"]
        for item in movimentacoes
        if item["categoria"] == "Despesa"
    )

    saldo = receitas - despesas

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_title("Relatório Financeiro CredMais")

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 12, "Relatorio Financeiro - CredMais", ln=True, align="C")

    pdf.set_font("Arial", "", 10)
    pdf.cell(
        0,
        8,
        f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        ln=True,
        align="C"
    )

    pdf.ln(8)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 9, "Resumo financeiro", ln=True)

    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, f"Total de receitas: R$ {receitas:,.2f}", ln=True)
    pdf.cell(0, 8, f"Total de despesas: R$ {despesas:,.2f}", ln=True)
    pdf.cell(0, 8, f"Saldo: R$ {saldo:,.2f}", ln=True)

    pdf.ln(8)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 9, "Movimentacoes", ln=True)

    pdf.set_font("Arial", "B", 9)
    pdf.cell(28, 8, "Data", border=1)
    pdf.cell(76, 8, "Tipo", border=1)
    pdf.cell(30, 8, "Categoria", border=1)
    pdf.cell(56, 8, "Valor (R$)", border=1, ln=True)

    pdf.set_font("Arial", "", 9)

    for item in movimentacoes:
        pdf.cell(28, 8, str(item["data"]), border=1)
        pdf.cell(76, 8, str(item["tipo"])[:40], border=1)
        pdf.cell(30, 8, str(item["categoria"]), border=1)

        valor_formatado = f'{item["valor"]:,.2f}'
        valor_formatado = valor_formatado.replace(",", "X").replace(".", ",").replace("X", ".")

        pdf.cell(56, 8, valor_formatado, border=1, ln=True)

    conteudo = pdf.output()
    arquivo = BytesIO(bytes(conteudo))
    arquivo.seek(0)

    return send_file(
        arquivo,
        as_attachment=True,
        download_name="relatorio_credmais.pdf",
        mimetype="application/pdf"
    )


if __name__ == "__main__":
    app.run(debug=True)
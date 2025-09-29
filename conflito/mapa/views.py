import pandas as pd
import plotly.express as px
from django.shortcuts import render, redirect
from django.http import Http404, HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.template.loader import render_to_string
from weasyprint import HTML
import markdown
import subprocess
import os


def processar_pais(pais):
    return f"Análise fictícia para o país: {pais}"


def mapa_plotly(request, filename=None):
    arquivos_permitidos = {
        'pred_12_anyviolence__off_period.csv',
        'pred_12__off_period.csv',
        'pred_3_anyviolence__off_period.csv',
        'pred_3__off_period.csv',
    }

    if filename is None:
        filename = 'pred_3_anyviolence__off_period.csv'

    if filename not in arquivos_permitidos:
        raise Http404("Arquivo não permitido.")

    caminho_csv = os.path.join(settings.BASE_DIR, 'mapa', 'static', filename)

    if not os.path.exists(caminho_csv):
        raise Http404("Arquivo não encontrado.")

    df = pd.read_csv(caminho_csv)

    # Determina quantos meses recuar com base no nome do arquivo
    meses_recuar = 12 if '12' in filename else 3

    def get_n_back(group):
        # Pega o registro 'meses_recuar' antes do último
        if len(group) >= meses_recuar:
            return group.iloc[-(meses_recuar + 1)]
        else:
            return group.iloc[0]

    df_agg = df.groupby('iso').apply(get_n_back).reset_index(drop=True)

    if 'pred' in df_agg.columns:
        coluna_prob = 'pred'
    elif 'y_pred_prob' in df_agg.columns:
        coluna_prob = 'y_pred_prob'
    else:
        raise Http404("Coluna de probabilidade não encontrada no CSV.")

    df_agg['prob'] = (df_agg[coluna_prob] * 100).round(2).astype(str) + '%'

    fig = px.choropleth(
        df_agg,
        locations="iso",
        color=coluna_prob,
        color_continuous_scale=px.colors.sequential.Reds,
        hover_name="iso",
        hover_data={coluna_prob: False, 'prob': True},
    )

    fig.update_traces(marker_line_width=1, marker_line_color='black', showscale=True)
    fig.update_coloraxes(colorbar_title="risk")

    fig.update_geos(
        lonaxis=dict(range=[-140, 140]),
        lataxis=dict(range=[-60, 80]),
        projection_scale=0.9,
        bgcolor='lightblue',
        showcountries=True,
        countrycolor="black",
        showcoastlines=False,
        showframe=False,
        showland=True,
        landcolor="lightgray",
    )

    fig.update_layout(
        paper_bgcolor='#222',
        plot_bgcolor='#222',
        font_color='white',
        margin=dict(l=0, r=0, t=30, b=0),
        autosize=True,
    )

    plot_html = fig.to_html(
        full_html=False,
        include_plotlyjs='cdn',
        config={'responsive': True}
    )

    resultado = ""
    entrada = ""

    if request.method == "POST":
        entrada = request.POST.get("pais_input", "").strip().upper()
        if entrada:
            resultado = processar_pais(entrada)

    return render(request, "mapa.html", {
        "plot_html": plot_html,
        "filename": filename,
        "resultado": resultado,
        "entrada": entrada,
    })


def about_view(request):
    return render(request, "about.html")


def model_view(request):
    return render(request, "model.html")


@csrf_exempt
def report_view(request):
    if request.method == "POST":
        entrada = request.POST.get("codigo_iso", "").strip().upper()

        if entrada:
            caminho_script = os.path.join(settings.BASE_DIR, "mapa", "scripts", "report.py")

            try:
                resultado = subprocess.run(
                    ["python3", caminho_script, entrada],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True
                )
                md_text = resultado.stdout.strip()
                resposta_html = markdown.markdown(md_text)

            except subprocess.CalledProcessError as e:
                resposta_html = f"<pre>Erro ao executar o script:\n{e.stderr.strip()}</pre>"

            request.session['resposta'] = resposta_html
            request.session['entrada'] = entrada

            return redirect(reverse('resposta'))

    return render(request, "report.html")


def resposta_view(request):
    resposta_html = request.session.get('resposta')
    entrada = request.session.get('entrada')

    if not resposta_html or not entrada:
        return redirect(reverse('report'))

    return render(request, "resposta.html", {
        "resposta": resposta_html,
        "entrada": entrada,
    })


def baixar_pdf(request):
    resposta_html = request.session.get('resposta')

    if not resposta_html:
        return redirect(reverse('report'))

    contexto = {
        'resposta': resposta_html,
    }

    html_string = render_to_string('pdf_template.html', contexto)
    pdf_file = HTML(string=html_string).write_pdf()

    request.session.pop('resposta', None)
    request.session.pop('entrada', None)

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="relatorio_analise.pdf"'
    return response


def resultado(request):
    codigo = request.session.get('codigo_iso')
    resposta = request.session.get('resposta')

    codigos_validos = {"BRA", "COL", "PER", "MEX", "VEN"}
    codigo_valido = codigo in codigos_validos if codigo else False

    return render(request, 'resultado.html', {
        'resposta': resposta,
        'codigo_valido': codigo_valido
    })

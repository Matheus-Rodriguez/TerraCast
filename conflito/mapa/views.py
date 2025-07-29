import pandas as pd
import plotly.express as px
from django.shortcuts import render, redirect
from django.http import Http404
import os
from django.conf import settings
import subprocess
from django.views.decorators.csrf import csrf_exempt
import markdown  # Import para converter Markdown em HTML

def processar_pais(pais):
    # Função temporária para teste, substitua pela chamada real ao script OpenAI
    return f"Análise fictícia para o país: {pais}"

def mapa_plotly(request, filename=None):
    arquivos_permitidos = {
        'pred_12_anyviolence__off_period.csv',
        'pred_12__off_period.csv',
        'pred_3_anyviolence__off_period.csv',
        'pred_3__off_period.csv',
    }

    if filename is None:
        filename = 'pred_3_anyviolence__off_period.csv'  # default

    if filename not in arquivos_permitidos:
        raise Http404("Arquivo não permitido.")

    caminho_csv = os.path.join(settings.BASE_DIR, 'mapa', 'static', filename)

    if not os.path.exists(caminho_csv):
        raise Http404("Arquivo não encontrado.")

    df = pd.read_csv(caminho_csv)

    def get_12_back(group):
        if len(group) >= 12:
            return group.iloc[-12]
        else:
            return group.iloc[0]

    df_agg = df.groupby('iso').apply(get_12_back).reset_index(drop=True)

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
        height=800,
        autosize=True,
    )

    plot_html = fig.to_html(full_html=False)

    resultado = ""
    entrada = ""

    if request.method == "POST":
        entrada = request.POST.get("pais_input", "").strip()
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
                resposta_html = markdown.markdown(md_text)  # converte Markdown para HTML

            except subprocess.CalledProcessError as e:
                resposta_html = f"<pre>Erro ao executar o script:\n{e.stderr.strip()}</pre>"

            # Guarda resultado e entrada na sessão
            request.session['resposta'] = resposta_html
            request.session['entrada'] = entrada

            # Redireciona para evitar re-execução no refresh
            return redirect('report')

    else:  # GET
        resposta_html = request.session.pop('resposta', '')
        entrada = request.session.pop('entrada', '')

    return render(request, "report.html", {
        "entrada": entrada,
        "resposta": resposta_html,
    })

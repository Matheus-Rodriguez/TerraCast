import pandas as pd
import plotly.express as px
from django.shortcuts import render
from django.http import Http404
import os
from django.conf import settings

def mapa_plotly(request, filename=None):
    arquivos_permitidos = {
        'pred12anyviolence_06_2025.csv',
        'pred12armedconf_06_2025.csv',
        'pred_3anyviolence_06_2025.csv',
        'pred_3armedconf_06_2025.csv',
        'pred_12__off_period.csv',
    }

    if filename is None:
        filename = 'pred12anyviolence_06_2025.csv'

    if filename not in arquivos_permitidos:
        raise Http404("Arquivo não permitido.")

    caminho_csv = os.path.join(settings.BASE_DIR, 'mapa', 'static', filename)

    if not os.path.exists(caminho_csv):
        raise Http404("Arquivo não encontrado.")

    df = pd.read_csv(caminho_csv)

    if filename == 'pred_12__off_period.csv':
        # Pega o valor 12 registros antes do fim por isocode
        def get_12_back(group):
            if len(group) >= 12:
                return group.iloc[-12]
            else:
                return group.iloc[0]  # fallback se não houver 12 registros
        df_agg = df.groupby('isocode').apply(get_12_back).reset_index(drop=True)
        df_agg = df_agg[['isocode', 'y_pred_prob']]
    else:
        df_agg = df.groupby('isocode')['y_pred_prob'].last().reset_index()

    df_agg['prob'] = (df_agg['y_pred_prob'] * 100).round(2).astype(str) + '%'

    fig = px.choropleth(
        df_agg,
        locations="isocode",
        color="y_pred_prob",
        color_continuous_scale=px.colors.sequential.Reds,
        hover_name="isocode",
        hover_data={'y_pred_prob': False, 'prob': True},
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
    return render(request, "mapa.html", {"plot_html": plot_html})

# ✅ Nova view "About"
def about_view(request):
    return render(request, "about.html")

def model_view(request):
    return render(request, "model.html")

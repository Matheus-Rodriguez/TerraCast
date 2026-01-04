import os
import subprocess
import pandas as pd
import plotly.express as px
import markdown
from django.shortcuts import render, redirect
from django.http import Http404, HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse, reverse_lazy
from django.template.loader import render_to_string
from weasyprint import HTML
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .scripts.forms import UploadCSVForm


def processar_pais(pais):
    return f"Análise fictícia para o país: {pais}"


def mapa_plotly(request, filename=None):
    arquivos_permitidos = {
        'pred_12_anyviolence__off_period.csv',
        'pred_12__off_period.csv',
        'pred_3_anyviolence__off_period.csv',
        'pred_3__off_period.csv',
    }

    filename = filename or 'pred_3_anyviolence__off_period.csv'

    if filename not in arquivos_permitidos:
        raise Http404("Arquivo não permitido.")

    caminho_csv = os.path.join(
        settings.BASE_DIR,
        'media',
        filename
    )

    if not os.path.exists(caminho_csv):
        raise Http404("Arquivo não encontrado.")

    df = pd.read_csv(caminho_csv)

    if 'month' in df.columns:
        df = df.sort_values(['iso', 'month'])
    elif 'date' in df.columns:
        df = df.sort_values(['iso', 'date'])

    df_agg = df.groupby('iso', as_index=False).last()

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
        margin=dict(l=0, r=0, t=0, b=0),
        autosize=True,
        coloraxis_colorbar=dict(
            title='Risk',
            tickfont=dict(size=12, color='white'),
        )
    )

    plot_html = fig.to_html(
        full_html=False,
        include_plotlyjs='cdn',
        config={'responsive': True,
                'displayModeBar': False
        }
    )

    return render(request, "maps/map.html", {
        "plot_html": plot_html,
        "filename": filename,
    })


def about(request):
    return render(request, 'maps/about.html')


def model(request):
    return render(request, 'maps/model.html')


@csrf_exempt
def report(request):
    if request.method == "POST":
        entrada = request.POST.get("codigo_iso", "").strip().upper()

        if entrada:
            caminho_script = os.path.join(settings.BASE_DIR, "maps", "scripts", "report.py")

            # Executa subprocesso e captura status
            resultado = subprocess.run(
                ["python3", caminho_script, entrada],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if resultado.returncode == 0:
                # Sucesso
                status = "ok"
                md_text = resultado.stdout.strip()
                resposta_html = markdown.markdown(md_text)
            else:
                # Erro
                status = "error"
                resposta_html = f"<pre>Erro ao executar o script:\n{resultado.stderr.strip()}</pre>"

            request.session['resposta'] = resposta_html
            request.session['entrada'] = entrada
            request.session['status'] = status

            return redirect(reverse('resposta'))

    return render(request, "maps/report.html")


def resposta(request):
    resposta_html = request.session.get('resposta')
    entrada = request.session.get('entrada')
    status = request.session.get('status')

    if not resposta_html or not entrada:
        return redirect(reverse('report'))

    return render(request, "maps/resposta.html", {
        "resposta": resposta_html,
        "entrada": entrada,
        "status": status,
    })


def baixar_pdf(request):
    resposta_html = request.session.get('resposta')

    if not resposta_html:
        return redirect(reverse('report'))

    contexto = {'resposta': resposta_html}
    html_string = render_to_string('maps/pdf_template.html', contexto)
    pdf_file = HTML(string=html_string).write_pdf()

    # Limpa sessão
    request.session.pop('resposta', None)
    request.session.pop('entrada', None)
    request.session.pop('status', None)

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="analysis_report.pdf"'
    return response

@login_required
def upload_csv(request):
    if request.method == 'POST':
        form = UploadCSVForm(request.POST, request.FILES)
        if form.is_valid():
            arquivo = form.cleaned_data['arquivo']

            file_path = os.path.join(settings.MEDIA_ROOT, arquivo.name)

            with open(file_path, 'wb+') as destino:
                for chunk in arquivo.chunks():
                    destino.write(chunk)

            return render(request, 'maps/upload_success.html', {'filename': arquivo.name})
    else:
        form = UploadCSVForm()
    return render(request, 'maps/upload_csv.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user) 
            return redirect('upload') 
        else:
            messages.error(request, 'Usuário ou senha inválidos')

    return render(request, 'maps/login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

import os
import sys
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Inicializa cliente OpenAI
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Caminho para a pasta static
base_dir = os.path.dirname(os.path.abspath(__file__))
static_path = os.path.normpath(os.path.join(base_dir, '..', 'static'))

# Função para ler CSV
def ler_csv(nome_arquivo):
    caminho = os.path.join(static_path, nome_arquivo)
    return pd.read_csv(caminho)

# Carrega datasets
df_12c = ler_csv('pred_12__off_period.csv')
df_3c  = ler_csv('pred_3__off_period.csv')
df_12v = ler_csv('pred_12_anyviolence__off_period.csv')
df_3v  = ler_csv('pred_3_anyviolence__off_period.csv')

# Padroniza ISO e period
for df in [df_12c, df_3c, df_12v, df_3v]:
    df['period'] = df['period'].astype(str)
    df['iso'] = df['iso'].str.strip().str.upper()

# Função para filtrar últimos meses do último ano disponível no dataset
def filtrar_ultimos_meses(df, iso, meses):
    df_iso = df[df['iso'] == iso].copy()
    if df_iso.empty:
        return "Sem dados disponíveis."

    # Descobre o último período disponível no dataset
    ultimo_periodo = df_iso['period'].max()
    ultimo_ano = int(ultimo_periodo[:4])

    # Filtra apenas o último ano
    df_ano = df_iso[df_iso['period'].str.startswith(str(ultimo_ano))]

    # Ordena decrescente por período
    df_ano = df_ano.sort_values(by='period', ascending=False)

    # Seleciona os últimos 'meses' registros
    df_selecionado = df_ano.head(meses)

    if df_selecionado.empty:
        return "Sem dados disponíveis."

    return df_selecionado.to_csv(index=False)

# Função para gerar resposta do OpenAI
def gerar_resposta_openai(iso):
    sample_12c = filtrar_ultimos_meses(df_12c, iso, 12)
    sample_3c  = filtrar_ultimos_meses(df_3c, iso, 3)
    sample_12v = filtrar_ultimos_meses(df_12v, iso, 12)
    sample_3v  = filtrar_ultimos_meses(df_3v, iso, 3)

    # Verifica se todos os resultados estão vazios
    if all(s.startswith("Sem dados disponíveis.") for s in [sample_12c, sample_3c, sample_12v, sample_3v]):
        return f"❌ ERRO. Nenhum dado disponível para o código ISO '{iso}'. Verifique se está correto (ex: BRA, COL, UKR)."

    dados_atuais = f"""
🔸 Conflito Armado (12 meses):\n{sample_12c}
🔸 Conflito Armado (3 meses):\n{sample_3c}
🔸 Violência Geral (12 meses):\n{sample_12v}
🔸 Violência Geral (3 meses):\n{sample_3v}

As previsões estão organizadas por período de origem (`period`).

Analise apenas os dados do ano mais recente disponível no dataset.
Para previsão de curto prazo, use os últimos 3 meses desse ano.
Para previsão de longo prazo, use os últimos 12 meses desse ano.

Compare as previsões com os eventos reais que ocorreram nessas datas. Avalie a consistência da previsão, citando fontes públicas se possível.

Classifique a consistência como:
✅ Excelente – previsão antecipou corretamente  
✅ Boa – parcialmente coerente  
❌ Inconsistente – previsão não correspondeu

Apresente:
- As previsões lidas
- Eventos reais no período (com trechos de fontes e links)
- Avaliação de consistência
- Observações sobre acertos ou erros do modelo
"""

    mensagens = [
        {"role": "system", "content": """
Você é um analista político cordial, humano e prestativo, como se estivesse conversando com um colega.

Sempre que iniciar uma nova análise, cumprimente educadamente, pergunte como a pessoa está e mantenha um tom acolhedor.

Use os dados recebidos para realizar análises políticas realistas e bem estruturadas. As previsões representam riscos de conflito armado e violência para 12 e 3 meses à frente da data `period`.

Compare as previsões (coluna 'pred') com os eventos reais que ocorreram no período previsto (ver coluna `period`). Cite fontes públicas se possível. Seja objetivo, humano e encerre a conversa.

Finalize com: "Relatório finalizado."
        """},
        {"role": "user", "content": f"Nova análise para {iso}. Dados abaixo:\n{dados_atuais}"}
    ]

    resposta = client.chat.completions.create(
        model="gpt-4o",
        messages=mensagens,
        temperature=0.4,
    )

    return resposta.choices[0].message.content.strip()

# Entrada principal
if __name__ == "__main__":
    if len(sys.argv) >= 2:
        iso_code = sys.argv[1].strip().upper()
        if len(iso_code) == 3:
            resultado = gerar_resposta_openai(iso_code)
            print(resultado)
        else:
            print("Código ISO inválido. Use 3 letras, ex: BRA, COL, UKR.")
    else:
        print("Uso: python relatorio.py <ISO>")

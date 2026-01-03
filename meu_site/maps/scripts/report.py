import os
import sys
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

base_dir = os.path.dirname(os.path.abspath(__file__))
static_path = os.path.normpath(os.path.join(base_dir, '..', 'static'))

def ler_csv(nome_arquivo):
    caminho = os.path.join(static_path, 'data', nome_arquivo)
    return pd.read_csv(caminho)
df_12c = ler_csv('pred_12__off_period.csv')
df_3c  = ler_csv('pred_3__off_period.csv')
df_12v = ler_csv('pred_12_anyviolence__off_period.csv')
df_3v  = ler_csv('pred_3_anyviolence__off_period.csv')

for df in [df_12c, df_3c, df_12v, df_3v]:
    df['period'] = df['period'].astype(str)
    df['iso'] = df['iso'].str.strip().str.upper()

def filtrar_ultimos_meses(df, iso, meses):
    df_iso = df[df['iso'] == iso].copy()
    if df_iso.empty:
        return "Sem dados disponíveis."

    ultimo_periodo = df_iso['period'].max()
    ultimo_ano = int(ultimo_periodo[:4])

    df_ano = df_iso[df_iso['period'].str.startswith(str(ultimo_ano))]

    df_ano = df_ano.sort_values(by='period', ascending=False)

    df_selecionado = df_ano.head(meses)

    if df_selecionado.empty:
        return "Sem dados disponíveis."

    return df_selecionado.to_csv(index=False)

def gerar_resposta_openai(iso):
    sample_12c = filtrar_ultimos_meses(df_12c, iso, 12)
    sample_3c  = filtrar_ultimos_meses(df_3c, iso, 3)
    sample_12v = filtrar_ultimos_meses(df_12v, iso, 12)
    sample_3v  = filtrar_ultimos_meses(df_3v, iso, 3)

    if all(s.startswith("Sem dados disponíveis.") for s in [sample_12c, sample_3c, sample_12v, sample_3v]):
        return f"❌ ERROR. No available data for the ISO code '{iso}'. Make sure it's correct (e.g: BRA, COL, UKR)."

    dados_atuais = f"""
🔸 Armed Conflict (12 months):\n{sample_12c}
🔸 Armed Conflict (3 months):\n{sample_3c}
🔸 General Violence (12 months):\n{sample_12v}
🔸 General Violence (3 months):\n{sample_3v}

The forecasts are organized by source period (period).

Analyze only the data from the most recent year available in the dataset.
For short-term forecasts, use the last 3 months of that year.
For long-term forecasts, use the last 12 months of that year.

Compare the forecasts with the actual events that occurred during these dates. Assess the consistency of the predictions, citing public sources whenever possible.

Classify consistency as:
✅ Excellent – prediction correctly anticipated events
✅ Good – partially coherent
❌ Inconsistent – prediction did not match events

Present:

The forecasts read

Actual events during the period (with excerpts from sources and links)

Consistency evaluation

Observations on the model’s successes or errors
"""
    mensagens = [
        {"role": "system", "content": """
    You are a cordial, human, and helpful political analyst, as if you were talking to a colleague.

    Whenever starting a new analysis, greet politely, ask how the person is doing, and maintain a welcoming tone.

    Use the received data to carry out realistic and well-structured political analyses. The forecasts represent risks of armed conflict and violence for 12 and 3 months ahead of the `period` date.

    Compare the forecasts (column 'pred') with the actual events that occurred in the predicted period (see `period` column). Cite public sources if possible. Be objective, human, and end the conversation.

    Finish with: "Report completed."
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
            print("❌ ERROR. Invalid ISO Code. Use 3 letters, e.g: BRA, COL, UKR.")
    else:
        print("Uso: python relatorio.py <ISO>")

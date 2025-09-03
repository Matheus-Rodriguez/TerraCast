import os
import sys
import pandas as pd
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

base_dir = os.path.dirname(os.path.abspath(__file__))
static_path = os.path.normpath(os.path.join(base_dir, '..', 'static'))

def ler_csv(nome_arquivo):
    caminho = os.path.join(static_path, nome_arquivo)
    return pd.read_csv(caminho)

df_12c = ler_csv('pred_12__off_period.csv')
df_3c  = ler_csv('pred_3__off_period.csv')
df_12v = ler_csv('pred_12_anyviolence__off_period.csv')
df_3v  = ler_csv('pred_3_anyviolence__off_period.csv')

for df in [df_12c, df_3c, df_12v, df_3v]:
    df['period'] = df['period'].astype(str)
    df['iso'] = df['iso'].str.strip().str.upper()

def adicionar_meses(df, meses):
    df_temp = df.copy()
    df_temp['data_prevista'] = pd.to_datetime(df_temp['period'], format='%Y%m') + pd.DateOffset(months=meses)
    df_temp['data_prevista'] = df_temp['data_prevista'].dt.strftime('%Y-%m')
    return df_temp

def filtrar_csv(df, iso, meses):
    df = adicionar_meses(df, meses)
    df_filtrado = df[(df['iso'] == iso) & (df['period'] >= '202201')]
    df_filtrado = df_filtrado.sort_values(by="period", ascending=False)
    return df_filtrado.to_csv(index=False)[:3500] if not df_filtrado.empty else "Sem dados disponíveis."

def gerar_resposta_openai(iso):
    sample_12c = filtrar_csv(df_12c, iso, 12)
    sample_3c  = filtrar_csv(df_3c, iso, 3)
    sample_12v = filtrar_csv(df_12v, iso, 12)
    sample_3v  = filtrar_csv(df_3v, iso, 3)

    # Verifica se todos os resultados estão vazios
    if all(s.startswith("Sem dados disponíveis.") for s in [sample_12c, sample_3c, sample_12v, sample_3v]):
        return f"❌ ERRO. Nenhum dado disponível para o código ISO '{iso}'. Verifique se está correto (ex: BRA, COL, UKR)."

    dados_atuais = f"""
🔸 Conflito Armado (12 meses):\n{sample_12c}
🔸 Conflito Armado (3 meses):\n{sample_3c}
🔸 Violência Geral (12 meses):\n{sample_12v}
🔸 Violência Geral (3 meses):\n{sample_3v}

As previsões estão organizadas por período de origem (`period`) e sua data-alvo de impacto está indicada na coluna `data_prevista`.

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

Compare as previsões com os eventos reais que ocorreram no período previsto (ver coluna `data_prevista`). Cite fontes públicas se possível. Seja objetivo, humano e encerre a conversa.
        """},
        {"role": "user", "content": f"Nova análise para {iso}. Dados abaixo:\n{dados_atuais}"}
    ]

    resposta = client.chat.completions.create(
        model="gpt-4o",
        messages=mensagens,
        temperature=0.4,
    )

    return resposta.choices[0].message.content.strip()

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

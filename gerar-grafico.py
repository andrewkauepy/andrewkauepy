"""Gera o grafico de contribuicoes em SVG, no estilo do modelo (linha suave).

POR QUE NAO USA SERVICO DE TERCEIRO: o modelo do Pinterest depende do
`github-readme-activity-graph.vercel.app`, que hoje responde **HTTP 402** —
virou pago. Testei tres espelhos, todos fora. Imagem de terceiro some sem avisar
e vira <img> quebrado no meio do perfil. Este SVG mora no proprio repositorio.

=============================================================================
DOIS ERROS QUE ESTE ARQUIVO JA COMETEU, e por que a solucao e o que e
=============================================================================

1) LI `data-level` E CHAMEI DE CONTAGEM.
   A pagina publica do GitHub **nao tem `data-count`** — so `data-level`, que e
   uma ESCALA DE INTENSIDADE de 0 a 4 ("quao verde pintar o quadradinho").
   Somei niveis e publiquei o resultado como "N contribuicoes". O numero foi ao
   ar errado, num perfil publico. O parser nao falhou: ele leu certo o atributo
   errado, e respondeu com a mesma confianca que teria se estivesse certo.
   -> Agora os dados vem da **API GraphQL**, onde `contributionCount` e
      literalmente a contagem.

2) EU IA AFIRMAR UM TOTAL QUE NAO CONSIGO CONFERIR.
   A API devolve 3 contribuicoes; o calendario nativo no perfil mostra 36. Nao
   consegui reconciliar os dois (nao sao contribuicoes privadas —
   `restrictedContributionsCount` = 0; provavelmente e recorte de periodo
   diferente). Como o grafico fica LADO A LADO com o calendario do GitHub, um
   numero divergente ali le como defeito.
   -> Entao **este SVG nao afirma total nenhum**. Ele desenha a forma da
      atividade, que e o que o modelo mostra. Numero que eu nao sei defender nao
      vai para um perfil publico.

Uso:  python gerar-grafico.py <usuario>
Exige o `gh` autenticado (usa `gh api graphql`).
"""
import json
import subprocess
import sys

USUARIO = sys.argv[1] if len(sys.argv) > 1 else "andrewkauepy"
SAIDA = "assets/contribuicoes.svg"
GH = r"C:\Program Files\GitHub CLI\gh.exe"

L, A = 1000, 220
MARGEM_X, MARGEM_Y = 10, 20


def semanas_do_calendario(user):
    """Contagem por dia, agrupada por semana. Fonte: API GraphQL."""
    q = ("{ user(login: \"%s\") { contributionsCollection { contributionCalendar "
         "{ weeks { contributionDays { date contributionCount } } } } } }" % user)
    r = subprocess.run([GH, "api", "graphql", "-f", f"query={q}"],
                       capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise SystemExit(f"gh api falhou: {r.stderr.strip()[:200]}")
    cal = json.loads(r.stdout)["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    return [sum(d["contributionCount"] for d in w["contributionDays"]) for w in cal["weeks"]]


def suave(pontos):
    """Bezier cubica: linha reta entre pontos fica dura e nao parece com o
    modelo, que tem a curva arredondada."""
    if len(pontos) < 2:
        return ""
    d = f"M {pontos[0][0]:.1f},{pontos[0][1]:.1f}"
    for i in range(len(pontos) - 1):
        x0, y0 = pontos[i]
        x1, y1 = pontos[i + 1]
        cx = (x0 + x1) / 2
        d += f" C {cx:.1f},{y0:.1f} {cx:.1f},{y1:.1f} {x1:.1f},{y1:.1f}"
    return d


def gerar(semanas):
    if not semanas:
        raise SystemExit("a API nao devolveu semana nenhuma")

    topo = max(semanas) if max(semanas) > 0 else 1
    largura = L - 2 * MARGEM_X
    altura = A - 2 * MARGEM_Y
    passo = largura / max(len(semanas) - 1, 1)

    pts = [(MARGEM_X + i * passo, MARGEM_Y + altura - (v / topo) * altura)
           for i, v in enumerate(semanas)]
    linha = suave(pts)
    area = linha + f" L {pts[-1][0]:.1f},{MARGEM_Y + altura} L {pts[0][0]:.1f},{MARGEM_Y + altura} Z"

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {L} {A}" width="{L}" height="{A}" role="img" aria-label="Atividade de {USUARIO} no ultimo ano">
  <style>
    /* A COR BASE E UM CINZA MEDIO, DE PROPOSITO.
       A media query abaixo ajuda, mas ela le o tema do SISTEMA OPERACIONAL — e
       o tema do GitHub e escolhido DENTRO do GitHub. Quem usa GitHub escuro num
       Windows claro cairia no ramo "light" e a linha sumiria. Ja aconteceu:
       a 1a versao tinha traco preto e ficou invisivel no tema escuro, sem erro
       nenhum no console. A tela nao quebrou — ela apenas nao mostrou nada.
       Cinza medio nao e o mais bonito em nenhum dos dois fundos; e o unico que
       nunca desaparece. Aqui isso vale mais. */
    .traco {{ stroke: #8b949e; }}
    .ponto {{ fill: #8b949e; }}
    .area  {{ fill: rgba(139,148,158,0.15); }}
    @media (prefers-color-scheme: dark) {{
      .traco {{ stroke: #e6edf3; }}
      .ponto {{ fill: #e6edf3; }}
      .area  {{ fill: rgba(230,237,243,0.12); }}
    }}
    @media (prefers-color-scheme: light) {{
      .traco {{ stroke: #1f2328; }}
      .ponto {{ fill: #1f2328; }}
      .area  {{ fill: rgba(31,35,40,0.14); }}
    }}
  </style>
  <rect width="{L}" height="{A}" fill="none"/>
  <path class="area" d="{area}"/>
  <path class="traco" d="{linha}" fill="none" stroke-width="2.2"
        stroke-linecap="round" stroke-linejoin="round"/>
  <circle class="ponto" cx="{pts[-1][0]:.1f}" cy="{pts[-1][1]:.1f}" r="4"/>
</svg>
"""


if __name__ == "__main__":
    import os
    semanas = semanas_do_calendario(USUARIO)
    os.makedirs("assets", exist_ok=True)
    open(SAIDA, "w", encoding="utf-8").write(gerar(semanas))
    print(f"{SAIDA} — {len(semanas)} semanas, pico de {max(semanas)} numa semana")
    print("sem texto de total: ver o comentario no topo do arquivo.")

"""Gera o grafico de contribuicoes em SVG, no estilo do modelo (linha suave).

POR QUE EXISTE: o modelo do Pinterest usa o servico
`github-readme-activity-graph.vercel.app`, que hoje responde **HTTP 402** —
virou pago. Testei tres espelhos, todos fora (402, 404, sem resposta).

Depender de um servico gratuito de terceiro para uma peca visual do perfil
significa que a imagem some no dia em que ele cair, e ninguem avisa. O grafico
passa a ser um <img> quebrado no meio do README. Entao o SVG e gerado aqui e
commitado no proprio repositorio: some so se o GitHub sair do ar.

FONTE DOS DADOS: a pagina publica de contribuicoes do GitHub, que devolve o
calendario em HTML com um `data-count` por dia. Nao precisa de token.

Uso:  python gerar-grafico.py <usuario>
"""
import re
import sys
import urllib.request
from datetime import datetime

USUARIO = sys.argv[1] if len(sys.argv) > 1 else "andrewkauepy"
SAIDA = "assets/contribuicoes.svg"

L, A = 1000, 220           # tamanho da area de desenho
MARGEM_X, MARGEM_Y = 10, 20


def contribuicoes(user):
    """Le o calendario publico. Devolve [(data, quantidade)] em ordem."""
    url = f"https://github.com/users/{user}/contributions"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        html = r.read().decode("utf-8", errors="ignore")

    # cada dia vira um <td>/<rect> com data-date e data-level ou data-count.
    dias = []
    for m in re.finditer(r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*', html):
        trecho = html[m.start():m.start() + 400]
        cnt = re.search(r'data-count="(\d+)"', trecho)
        if cnt:
            dias.append((m.group(1), int(cnt.group(1))))
            continue
        # o GitHub mudou para data-level (0..4) em algumas paginas
        lvl = re.search(r'data-level="(\d+)"', trecho)
        dias.append((m.group(1), int(lvl.group(1)) if lvl else 0))
    dias.sort()
    return dias


def suave(pontos):
    """Curva com Bezier cubica. Linha reta entre pontos fica dura e nao parece
    com o modelo, que tem a curva arredondada."""
    if len(pontos) < 2:
        return ""
    d = f"M {pontos[0][0]:.1f},{pontos[0][1]:.1f}"
    for i in range(len(pontos) - 1):
        x0, y0 = pontos[i]
        x1, y1 = pontos[i + 1]
        cx = (x0 + x1) / 2
        d += f" C {cx:.1f},{y0:.1f} {cx:.1f},{y1:.1f} {x1:.1f},{y1:.1f}"
    return d


def gerar(dias):
    if not dias:
        raise SystemExit("nenhum dia lido — o formato da pagina do GitHub mudou")

    # agrupo por SEMANA. Dia a dia (365 pontos) vira serrote ilegivel na largura
    # de um README; o modelo mostra uma curva, nao um eletrocardiograma.
    semanas, atual = [], []
    for data, n in dias:
        atual.append(n)
        if datetime.strptime(data, "%Y-%m-%d").weekday() == 6:
            semanas.append(sum(atual))
            atual = []
    if atual:
        semanas.append(sum(atual))

    topo = max(semanas) if max(semanas) > 0 else 1
    largura = L - 2 * MARGEM_X
    altura = A - 2 * MARGEM_Y
    passo = largura / max(len(semanas) - 1, 1)

    pts = [(MARGEM_X + i * passo, MARGEM_Y + altura - (v / topo) * altura)
           for i, v in enumerate(semanas)]
    linha = suave(pts)
    area = linha + f" L {pts[-1][0]:.1f},{MARGEM_Y + altura} L {pts[0][0]:.1f},{MARGEM_Y + altura} Z"

    total = sum(n for _, n in dias)
    # ⚠️ O TRACO PRECISA TROCAR DE COR COM O TEMA.
    # A 1a versao usava stroke preto fixo. Ficou invisivel — o GitHub escuro tem
    # fundo #0d1117, e linha preta sobre fundo quase preto nao existe. So apareceu
    # ao comparar lado a lado com o modelo, onde a linha e BRANCA. O grafico
    # renderizava "sem erro" e nao mostrava nada: a tela nao quebra, ela some.
    #
    # Quem escolhe o tema e o VISITANTE, nao o dono do perfil. Entao nao da pra
    # escolher uma cor: o SVG tem que responder ao `prefers-color-scheme`, e a
    # media query vale porque o browser renderiza o SVG de verdade.
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {L} {A}" width="{L}" height="{A}" role="img" aria-label="Contribuicoes de {USUARIO}">
  <style>
    /* A COR BASE E UM CINZA MEDIO, DE PROPOSITO.
       A media query abaixo existe e ajuda, mas ela le o tema do SISTEMA
       OPERACIONAL — e o tema do GitHub e escolhido DENTRO do GitHub. Quem usa
       GitHub escuro num Windows claro cairia no ramo "light" e a linha sumiria
       de novo, exatamente o defeito que eu estava consertando.
       Cinza medio (#8b949e) tem contraste suficiente contra #ffffff E contra
       #0d1117. Nao e o mais bonito em nenhum dos dois; e o unico que nunca
       desaparece. Aqui isso vale mais. */
    .traco {{ stroke: #8b949e; }}
    .ponto {{ fill: #8b949e; }}
    .area  {{ fill: rgba(139,148,158,0.15); }}
    .nota  {{ fill: #8b949e; }}
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
  <text class="nota" x="{L - MARGEM_X}" y="{A - 4}" text-anchor="end"
        font-family="ui-monospace, SFMono-Regular, Menlo, monospace"
        font-size="11">{total} contribuicoes no ultimo ano</text>
</svg>
"""


if __name__ == "__main__":
    dias = contribuicoes(USUARIO)
    svg = gerar(dias)
    import os
    os.makedirs("assets", exist_ok=True)
    open(SAIDA, "w", encoding="utf-8").write(svg)
    total = sum(n for _, n in dias)
    print(f"{SAIDA} gerado — {len(dias)} dias lidos, {total} contribuicoes")
    if total == 0:
        print("AVISO: o total e ZERO. A curva vai sair reta no chao — e a verdade,")
        print("       nao um defeito. Ela sobe sozinha quando houver commit publico.")

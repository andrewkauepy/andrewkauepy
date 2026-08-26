"""Monta o banner do README a partir da arte PROJECT.EXE.

A arte nova (dithering P&B, as duas maos e a janela "PROJECT EXE") ja e a
identidade — ela nao precisa de nada por cima. O trabalho aqui e so de FORMATO.

O PROBLEMA DE FORMATO: a arte e 734x378, proporcao 1,94. O banner do modelo e
uma faixa bem mais larga (~3,5). Num README de 920px, usar a arte crua deixa um
bloco de 474px de altura — alto demais, empurra todo o resto pra baixo da dobra.

DUAS SAIDAS, e nenhuma corta a arte:
  pura     a imagem como veio. Mais alta, mas intocada.
  faixa    canvas 3:1 com a arte a direita e o nome a esquerda. Funciona porque
           o fundo da arte e preto e o canvas tambem — nao ha emenda visivel.

Uso: python montar-banner.py [pura|faixa]
"""
import sys

from PIL import Image, ImageDraw, ImageFont

MODO = sys.argv[1] if len(sys.argv) > 1 else "faixa"
ORIGEM = "assets/origem-banner.png"

arte = Image.open(ORIGEM).convert("RGB")

if MODO == "pura":
    arte.save("assets/banner.png", "PNG", optimize=True)
    print(f"assets/banner.png — {arte.width}x{arte.height} (arte intacta)")
    sys.exit()

# ------------------------------------------------------------------ faixa 3:1
# 1320, nao 1200: a frase mede ~630px e a arte comecava em 532px — o texto
# encostava no degrade. Alargar o canvas resolve sem encolher a fonte nem
# cortar a arte; o preto extra e invisivel porque o fundo dos dois e preto.
L, A = 1320, 344
canvas = Image.new("RGB", (L, A), (0, 0, 0))

# a arte ocupa a altura toda e vai pra direita
alvo_h = A
alvo_w = int(arte.width * (alvo_h / arte.height))
a = arte.resize((alvo_w, alvo_h), Image.LANCZOS)
canvas.paste(a, (L - alvo_w, 0))

# Degrade de preto na emenda esquerda da arte. O fundo dela e preto, mas o
# dithering tem pontos brancos ate a borda — sem o degrade, a linha vertical
# onde a arte comeca fica perceptivel como um "corte".
grad = Image.new("L", (140, A), 0)
gd = ImageDraw.Draw(grad)
for i in range(140):
    gd.line([(i, 0), (i, A)], fill=int(255 * (1 - i / 140)))
canvas.paste(Image.new("RGB", (140, A), (0, 0, 0)), (L - alvo_w, 0), grad)

d = ImageDraw.Draw(canvas)
try:
    f_nome = ImageFont.truetype("C:/Windows/Fonts/impact.ttf", 104)
    f_sub = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 20)
except OSError:
    f_nome = f_sub = ImageFont.load_default()

NOME = "KAUE"
SUB = sys.argv[2] if len(sys.argv) > 2 else ""
x, y = 62, int(A * 0.28)
d.text((x, y), NOME, font=f_nome, fill=(245, 245, 245))

if SUB:
    cy = y + 114
    larg = int(d.textlength(SUB, font=f_sub))
    d.line([(x + 4, cy), (x + 4 + larg, cy)], fill=(200, 200, 200), width=2)
    d.text((x + 4, cy + 14), SUB, font=f_sub, fill=(185, 185, 185))

canvas.save("assets/banner.png", "PNG", optimize=True)
print(f"assets/banner.png — {L}x{A} (faixa)")

"""Gera as Figuras 2-4 do relatório (vazão, atraso e perda) a partir do resumo.csv.

Uso: python3 graficos_equipe_6.py [resultados_equipe_6/resumo.csv] [figuras]
"""

import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402

CLIENTES = (1, 2, 4, 8, 16, 32)
APLICACOES = (("cbr", "CBR"), ("rajada", "Rajada"), ("cbr_rajada", "CBR/Rajada"))
MOBILIDADES = (("estatico", "Estático"), ("movel", "Móvel"))
TRANSPORTES = (("udp", "UDP", "#1f77b4", "o"),
               ("tcp", "TCP", "#d95f02", "s"),
               ("misto", "50% UDP / 50% TCP", "#1b9e77", "^"))
FIGURAS = (("vazao", "vazao_total_mbps", "Vazão agregada recebida", "Vazão (Mbit/s)", False),
           ("atraso", "atraso_medio_ms", "Atraso médio dos pacotes recebidos",
            "Atraso (ms; log)", True),
           ("perda", "perda_pct", "Perda de pacotes na camada IP", "Perda (%)", False))


def configurar_fonte():
    pasta = Path("/usr/share/texmf/fonts/opentype/public/tex-gyre")
    for arquivo in pasta.glob("texgyreheros-*.otf"):
        font_manager.fontManager.addfont(str(arquivo))
    if any(f.name == "TeX Gyre Heros" for f in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = "TeX Gyre Heros"
    plt.rcParams.update({"font.size": 7, "axes.titlesize": 7.5})


def carregar(caminho):
    with open(caminho, encoding="utf-8") as arquivo:
        return {(l["mobilidade"], l["transporte"], l["aplicacao"], int(l["clientes"])): l
                for l in csv.DictReader(arquivo)}


def desenhar(dados, saida, nome, chave, titulo, rotulo, log):
    fig, eixos = plt.subplots(3, 2, figsize=(5.5, 6.2), sharex=True, sharey=True)
    posicoes = range(len(CLIENTES))
    for linha, (app, nome_app) in enumerate(APLICACOES):
        for coluna, (mob, nome_mob) in enumerate(MOBILIDADES):
            eixo = eixos[linha][coluna]
            for tr, nome_tr, cor, marcador in TRANSPORTES:
                valores = [float(dados[(mob, tr, app, n)][chave]) for n in CLIENTES]
                eixo.plot(posicoes, valores, color=cor, marker=marcador,
                          markersize=3.5, linewidth=1.2, label=nome_tr)
            eixo.set_title(f"{nome_app} · {nome_mob}")
            eixo.grid(True, color="#dddddd", linewidth=0.5)
            if log:
                eixo.set_yscale("log")
            if coluna == 0:
                eixo.set_ylabel(rotulo)
            if linha == 2:
                eixo.set_xlabel("Número de clientes")
                eixo.set_xticks(list(posicoes), [str(n) for n in CLIENTES])
            eixo.tick_params(labelleft=True)
    if not log:
        eixos[0][0].set_ylim(bottom=0)
    fig.suptitle(titulo, fontweight="bold", fontsize=8.5)
    identificadores, rotulos = eixos[0][0].get_legend_handles_labels()
    fig.legend(identificadores, rotulos, loc="lower center", ncol=3, frameon=False)
    fig.tight_layout(rect=(0, 0.035, 1, 0.98))
    fig.savefig(saida / f"{nome}.pdf")
    plt.close(fig)


def main():
    resumo = Path(sys.argv[1] if len(sys.argv) > 1 else "resultados_equipe_6/resumo.csv")
    saida = Path(sys.argv[2] if len(sys.argv) > 2 else "figuras")
    saida.mkdir(parents=True, exist_ok=True)
    configurar_fonte()
    dados = carregar(resumo)
    for figura in FIGURAS:
        desenhar(dados, saida, *figura)
    print(f"Figuras salvas em {saida.resolve()}")


if __name__ == "__main__":
    main()

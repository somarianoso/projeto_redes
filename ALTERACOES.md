# Alterações no Projeto Prático de Redes — Equipe 6

**PCS3614 — Redes de Computadores I — 3º quadrimestre de 2026**

| NUSP | Integrante |
| --- | --- |
| 15447910 | Diego Fontes de Avila |
| 15453560 | Gabriel Lopes Prodossimo |
| 15463850 | João Victor Costa Teodoro |
| 15520593 | Matheus Davi Leão |
| 15511213 | Sophia Soares Mariano |

## Resumo

Antes da revisão, o trabalho já cumpria a parte técnica do enunciado:

- topologia com o servidor `s2` na LAN 10.1.1.0/24, o AP e os clientes Wi-Fi em 192.168.0.0/24;
- SSID `Equipe6` e padrão IEEE 802.11a;
- clientes estáticos e móveis;
- tráfego UDP, TCP e 50% UDP/50% TCP;
- 1, 2, 4, 8, 16 e 32 clientes, num total de 108 cenários;
- medição de vazão, atraso e perda.

As alterações corrigem problemas que tirariam pontos ou impediriam o professor de rodar o código. Os resultados numéricos, os gráficos e as conclusões **não mudaram**.

## Arquivos para enviar no Moodle

Os dois arquivos estão em `REVISAR_REDES/REVISAR_REDES/` e já estão prontos para a entrega:

| Arquivo | Situação |
| --- | --- |
| `equipe_6_relatorio_redes_3q2026.pdf` | Nome no padrão exigido; 8 páginas (o limite é 8); fontes embutidas; sem referências quebradas |
| `equipe_6_3q2026.py` | Nome no padrão exigido; erro que impedia a execução corrigido |

Prazo: **17/11/2026, até 23h59**. Uma única pessoa do grupo envia.

## Alterações no script (`equipe_6_3q2026.py`)

| Alteração | Por quê |
| --- | --- |
| Declaração do argumento `--rapido` | O código usava `args.rapido`, mas o argumento nunca tinha sido declarado. Por isso, **qualquer execução** parava com `AttributeError: 'Namespace' object has no attribute 'rapido'`, até a dos 108 cenários. O código também é avaliado, então precisa rodar. |
| Com `--rapido`, os CSVs vão para `resultados_teste_rapido/` | Antes, um teste rápido regravaria `resultados_equipe_6/resumo.csv` e apagaria os resultados dos 108 cenários. Quando `--saida` é informado, nada muda. |
| Cabeçalho com os integrantes, os NUSP e o que cada um fez, mais um comentário `# Responsável:` antes de cada função principal | Mostra no próprio código quem fez cada parte. Bate com a Tabela 2 do relatório. |
| `--help` formatado com `RawDescriptionHelpFormatter` | Antes, os exemplos de uso apareciam todos juntos numa única linha. |
| Comentário explicando `ns = None` | Explica que o ns-3 só é importado quando necessário, porque a importação leva cerca de um minuto. |

A topologia, o Wi-Fi, a mobilidade, as aplicações e as métricas **não foram alteradas**. Por isso, os resultados já obtidos continuam valendo.

## Alterações no relatório (`equipe_6_relatorio_redes_3q2026.tex` / `.pdf`)

| Alteração | Por quê |
| --- | --- |
| `relatorio_equipe_6` renomeado para `equipe_6_relatorio_redes_3q2026` | O enunciado exige o nome `equipe_x_relatorio_redes_3q2026.pdf`. Quem não segue o padrão perde 1,0 ponto. |
| Os cinco nomes como autores, no lugar de "Equipe 6"; endereço com a disciplina e a Poli-USP, em duas linhas | O modelo da SBC pede autores e instituição. Em uma linha só, o endereço passava da margem. |
| Seção 5 (Divisão do trabalho) reescrita como tabela com nome, NUSP e atividades | O enunciado pede o que cada integrante fez. O texto anterior atribuía tudo a "Codex", uma ferramenta, e não aos alunos. |
| Removido o `Path=fontes/` | A pasta `fontes/` não estava no projeto, então o `.tex` não compilava. Agora são usadas as fontes TeX Gyre instaladas no sistema, que são as mesmas do original. |
| Incluídos `sbc-template.sty` (do pacote oficial da SBC) e a pasta `figuras/` | Esses arquivos também faltavam. As quatro figuras foram recortadas, em formato vetorial, do PDF original. Por isso são idênticas às anteriores. |

Para compilar: `latexmk -xelatex equipe_6_relatorio_redes_3q2026.tex`. O PDF continua com 8 páginas, então não há desconto por página excedente.

Introdução, metodologia, resultados, discussão e conclusão continuam iguais. Essas seções já seguiam a ordem pedida pelo professor: resumo, introdução, exercício proposto com a figura da topologia, avaliação de desempenho com a máquina utilizada e a tabela de parâmetros, resultados de atraso, vazão e perda com a discussão, divisão do trabalho e conclusão.

## Divisão do trabalho

| Integrante | NUSP | Atividades | Funções no script |
| --- | --- | --- | --- |
| Diego Fontes de Avila | 15447910 | Instalação do ns-3; LAN CSMA, endereços IP e roteamento | `topologia` (parte cabeada) |
| Gabriel Lopes Prodossimo | 15453560 | Wi-Fi 802.11a (AP, SSID, potência) e caminhada aleatória | `topologia` (parte Wi-Fi), `mobilidade` |
| João Victor Costa Teodoro | 15463850 | Aplicações UDP, TCP e mista; padrões CBR e rajada | `aplicacoes` |
| Matheus Davi Leão | 15520593 | FlowMonitor, métricas, execução dos 108 cenários e CSVs | `metricas`, `resumo`, `main` |
| Sophia Soares Mariano | 15511213 | Gráficos, figura da topologia, redação e revisão do relatório; revisão final do script | — |

## Repositório

- `.gitignore` criado para ignorar os arquivos auxiliares do LaTeX, `__pycache__`, `.venv` e `resultados_teste_rapido/`.
- Repositório no GitHub configurado como **privado**, porque contém nomes e números USP.

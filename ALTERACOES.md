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

As alterações corrigem problemas que tirariam pontos ou impediriam o professor de rodar o código. Uma delas tornou os resultados de fato reproduzíveis. Por isso, os 108 cenários foram simulados de novo e as figuras foram refeitas. Os números mudaram pouco, e **as conclusões continuam as mesmas**.

## Arquivos para enviar no Moodle

Os dois arquivos estão em `REVISAR_REDES/REVISAR_REDES/` e já estão prontos para a entrega:

| Arquivo | Situação |
| --- | --- |
| `equipe_6_relatorio_redes_3q2026.pdf` | Nome no padrão exigido; 8 páginas (o limite é 8); fontes embutidas; sem referências quebradas |
| `equipe_6_3q2026.py` | Nome no padrão exigido; erro que impedia a execução corrigido; resultados reproduzíveis |

Prazo: **17/11/2026, até 23h59**. Uma única pessoa do grupo envia.

## Alterações no script (`equipe_6_3q2026.py`)

| Alteração | Por quê |
| --- | --- |
| Declaração do argumento `--rapido` | O código usava `args.rapido`, mas o argumento nunca tinha sido declarado. Por isso, **qualquer execução** parava com `AttributeError: 'Namespace' object has no attribute 'rapido'`, até a dos 108 cenários. O código também é avaliado, então precisa rodar. |
| Com `--rapido`, os CSVs vão para `resultados_teste_rapido/` | Antes, um teste rápido regravaria `resultados_equipe_6/resumo.csv` e apagaria os resultados dos 108 cenários. Quando `--saida` é informado, nada muda. |
| Cabeçalho com os integrantes, os NUSP e o que cada um fez, mais um comentário `# Responsável:` antes de cada função principal | Mostra no próprio código quem fez cada parte. Bate com a Tabela 2 do relatório. |
| `ns.RngSeedManager.ResetNextStreamIndex()` no início de cada cenário | No ns-3, o contador que numera as sequências aleatórias não volta a zero ao fim de cada cenário. Por isso, o resultado de um cenário mudava conforme os cenários que tinham rodado antes no mesmo processo. O mesmo cenário, com a mesma semente e a mesma rodada, deu atraso de 1,03 ms na primeira execução e de 1,43 ms na segunda. Ou seja, os resultados não eram reproduzíveis, ao contrário do que o relatório afirma. Com a correção, as duas execuções dão resultados idênticos, e há um teste que verifica isso. |
| `--help` formatado com `RawDescriptionHelpFormatter` | Antes, os exemplos de uso apareciam todos juntos numa única linha. |
| Comentário explicando `ns = None` | Explica que o ns-3 só é importado quando necessário, porque a importação leva cerca de um minuto. |

A topologia, o Wi-Fi, a mobilidade, as aplicações e as métricas **não foram alteradas**.

### Novos resultados e gráficos

- **Os 108 cenários rodaram de novo** com a correção da aleatoriedade: ns-3 3.44, Python 3.10, semente 6. Os CSVs `resultados_equipe_6/resumo.csv` e `fluxos.csv` foram incluídos no repositório. O relatório já os citava, mas eles não estavam na pasta.
- **Script de gráficos:** `graficos_equipe_6.py` foi criado para gerar as Figuras 2 a 4 a partir de `resumo.csv`. O script original de gráficos não estava no projeto, então antes não havia como refazer as figuras.
- **Números atualizados no relatório:** vários valores já batiam exatamente (16,757 Mbit/s; 97,0%; 159,9 ms; 20,4%; 148,0 ms). Os outros mudaram pouco, e **nenhuma conclusão mudou**:

| Valor no relatório (32 clientes) | Antes | Agora |
| --- | --- | --- |
| Vazão UDP CBR/Rajada, estático → móvel | 12,953 → 10,316 Mbit/s | 12,954 → 10,313 Mbit/s |
| Atraso UDP Rajada, estático | 16,6 ms | 16,8 ms |
| Atraso UDP CBR/Rajada, estático → móvel | 12,0 → 148,0 ms | 12,4 → 148,0 ms |
| Entrega CBR misto, estático → móvel | 97,4% → 80,7% | 97,3% → 80,5% |
| Atraso CBR misto, estático → móvel | 172,2 → 230,0 ms | 172,7 → 232,3 ms |
| Atraso TCP CBR, estático / móvel | 186,6 / 192,7 ms | 183,7 / 181,6 ms |
| Perda TCP CBR, estático / móvel | 1,4% / 1,4% | 1,2% / 1,5% |
| Jitter TCP Rajada, estático → móvel | 1,5 → 8,2 ms | 2,1 → 3,9 ms |
| Justiça de Jain, UDP CBR/Rajada móvel | 0,879 | 0,878 |

A configuração da máquina na Metodologia também foi atualizada, porque os resultados novos foram gerados em outra máquina: Ubuntu 22.04.5 sob WSL2, Intel Core i5-12450H com 12 núcleos lógicos, 3,7 GiB de memória e Python 3.10.12. O enunciado pede a configuração da máquina usada nos experimentos.

A Metodologia ganhou uma frase dizendo que o contador de sequências aleatórias é reiniciado em cada cenário, então o resultado não depende da ordem de execução.

## Alterações no relatório (`equipe_6_relatorio_redes_3q2026.tex` / `.pdf`)

| Alteração | Por quê |
| --- | --- |
| `relatorio_equipe_6` renomeado para `equipe_6_relatorio_redes_3q2026` | O enunciado exige o nome `equipe_x_relatorio_redes_3q2026.pdf`. Quem não segue o padrão perde 1,0 ponto. |
| Os cinco nomes como autores, no lugar de "Equipe 6"; endereço com a disciplina e a Poli-USP, em duas linhas | O modelo da SBC pede autores e instituição. Em uma linha só, o endereço passava da margem. |
| Seção 5 (Divisão do trabalho) reescrita como tabela com nome, NUSP e atividades | O enunciado pede o que cada integrante fez. O texto anterior atribuía tudo a "Codex", uma ferramenta, e não aos alunos. |
| Removido o `Path=fontes/` | A pasta `fontes/` não estava no projeto, então o `.tex` não compilava. Agora são usadas as fontes TeX Gyre instaladas no sistema, que são as mesmas do original. |
| Incluídos `sbc-template.sty` (do pacote oficial da SBC) e a pasta `figuras/` | Esses arquivos também faltavam. A figura da topologia foi recortada, em formato vetorial, do PDF original. As Figuras 2 a 4 foram geradas de novo com `graficos_equipe_6.py`, a partir dos resultados reproduzíveis. |

Para compilar: `latexmk -xelatex equipe_6_relatorio_redes_3q2026.tex`. O PDF continua com 8 páginas, então não há desconto por página excedente.

Fora os números atualizados (tabela acima) e uma frase nova na Metodologia, as seções de introdução, metodologia, resultados, discussão e conclusão continuam iguais. Essas seções já seguiam a ordem pedida pelo professor: resumo, introdução, exercício proposto com a figura da topologia, avaliação de desempenho com a máquina utilizada e a tabela de parâmetros, resultados de atraso, vazão e perda com a discussão, divisão do trabalho e conclusão.

## Divisão do trabalho

| Integrante | NUSP | Atividades | Funções no script |
| --- | --- | --- | --- |
| Diego Fontes de Avila | 15447910 | Instalação do ns-3; LAN CSMA, endereços IP e roteamento | `topologia` (parte cabeada) |
| Gabriel Lopes Prodossimo | 15453560 | Wi-Fi 802.11a (AP, SSID, potência) e caminhada aleatória | `topologia` (parte Wi-Fi), `mobilidade` |
| João Victor Costa Teodoro | 15463850 | Aplicações UDP, TCP e mista; padrões CBR e rajada | `aplicacoes` |
| Matheus Davi Leão | 15520593 | FlowMonitor, métricas, execução dos 108 cenários e CSVs | `metricas`, `resumo`, `main` |
| Sophia Soares Mariano | 15511213 | Gráficos, figura da topologia, redação e revisão do relatório; revisão final do script | — |

## Comprovação de que o trabalho atende ao enunciado

O arquivo `testes/test_requisitos.py` traz 22 testes automáticos, e cada um verifica um item das instruções do professor. Eles foram rodados com o ns-3 3.44 instalado, e **os 22 passaram** (`Ran 22 tests … OK`).

| Exigência do professor | Como foi comprovada | Resultado |
| --- | --- | --- |
| Nomes `equipe_6_relatorio_redes_3q2026.pdf` e `equipe_6_3q2026.py` | Expressão regular nos nomes dos arquivos | OK |
| Relatório com no máximo 8 páginas | `pdfinfo` | OK (8 páginas) |
| Template da SBC | `\usepackage{sbc-template}` presente | OK |
| Seções: resumo, introdução, exercício, avaliação (metodologia e parâmetros), resultados, discussão, divisão do trabalho, conclusão | Busca no PDF, na ordem exigida | OK |
| Figura da topologia, configuração da máquina e tabela de parâmetros | Busca no PDF | OK |
| Gráficos de atraso, vazão e perda | Figuras 2 a 4 presentes | OK |
| Divisão do trabalho por integrante | Os 5 nomes e os 5 NUSP aparecem no PDF | OK |
| Servidor `s2` como último nó da LAN cabeada, ligado ao AP | No ns-3: o servidor tem o IP 10.1.1.4, o último da LAN CSMA | OK |
| Clientes Wi-Fi na rede 192.168.0.0, com SSID `Equipe6` | No ns-3: o endereço e o SSID de cada cliente | OK |
| Cenário sem mobilidade | No ns-3: os clientes não se movem em 10 s | OK |
| Cenário com pessoas caminhando aleatoriamente (1 e 2 m/s) | No ns-3: os clientes se movem a 1 ou 2 m/s e ficam dentro de 140 m × 140 m | OK |
| Aplicações UDP, TCP e 50% UDP / 50% TCP | No ns-3: contagem de protocolos por cliente, mais `clientes_udp` e `clientes_tcp` nos CSVs | OK |
| Clientes em {1, 2, 4, 8, 16, 32} | Os 108 cenários aparecem completos no `resumo.csv` | OK |
| Medição de atraso, vazão e perda | Execução de um cenário no ns-3, mais os valores presentes nos 108 cenários | OK |
| Números citados no texto do relatório | Comparação com o `resumo.csv` (21 valores) | OK |
| Reprodutibilidade | O mesmo cenário rodado duas vezes no mesmo processo dá o mesmo resultado | OK |

Para rodar os testes: `python -m unittest -v testes/test_requisitos.py`, com um Python que tenha o ns-3 (`pip install ns3==3.44.post0`). Sem o ns-3, use `SEM_NS3=1`: assim só os testes de simulação são pulados.

## Repositório

- `.gitignore` criado para ignorar os arquivos auxiliares do LaTeX, `__pycache__`, `.venv` e `resultados_teste_rapido/`.
- Repositório no GitHub configurado como **privado**, porque contém nomes e números USP.
- Conteúdo de `REVISAR_REDES/REVISAR_REDES/`:

| Arquivo ou pasta | O que é |
| --- | --- |
| `equipe_6_3q2026.py` | Script de simulação (entregável) |
| `equipe_6_relatorio_redes_3q2026.pdf` / `.tex` | Relatório (entregável) e seu código-fonte LaTeX |
| `figuras/` e `sbc-template.sty` | Arquivos necessários para compilar o relatório |
| `graficos_equipe_6.py` | Gera as Figuras 2 a 4 a partir do `resumo.csv` |
| `resultados_equipe_6/` | `resumo.csv` (108 cenários) e `fluxos.csv` (um fluxo por cliente) |

- `testes/test_requisitos.py`: testes que comprovam os requisitos do enunciado.
- A docstring do script passou a explicar como instalar o ns-3 e a memória usada por processo. Ela também explica por que um cenário rodado sozinho não repete o valor do `resumo.csv`: o número da rodada é a posição do cenário na lista selecionada.

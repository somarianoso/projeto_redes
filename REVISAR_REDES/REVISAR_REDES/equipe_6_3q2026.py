"""Simulação da equipe 6: servidor cabeado envia dados a clientes Wi-Fi UDP/TCP.

PCS3614 - Redes de Computadores I (3º quadrimestre de 2026) - Equipe 6
Integrantes e responsabilidades no código:
    15447910 Diego Fontes de Avila      - instalação do ns-3; LAN CSMA, endereçamento
                                          IP e roteamento (topologia)
    15453560 Gabriel Lopes Prodossimo   - rede Wi-Fi 802.11a/AP e mobilidade dos
                                          clientes (topologia, mobilidade)
    15463850 João Victor Costa Teodoro  - aplicações UDP, TCP e mista; padrões CBR e
                                          rajada (aplicacoes)
    15520593 Matheus Davi Leão          - métricas com FlowMonitor, execução dos
                                          cenários e CSVs (metricas, resumo, main)
    15511213 Sophia Soares Mariano      - gráficos, figura da topologia, redação do
                                          relatório e revisão final do script

Instalação do ns-3 (bindings Python): pip install ns3==3.44.post0
Execute todos os 108 cenários: .venv/bin/python equipe_6_3q2026.py
Continuar em paralelo: .venv/bin/python -u equipe_6_3q2026.py --continuar --processos 3
    (cada processo usa cerca de 700 MB de memória; com pouca RAM, use --processos 1)
Teste rápido: .venv/bin/python equipe_6_3q2026.py --rapido
Teste um cenário:
    .venv/bin/python equipe_6_3q2026.py --mobilidade estatico --transporte udp --aplicacao cbr --clientes 2 --duracao 10
Gráficos do relatório: python3 graficos_equipe_6.py resultados_equipe_6/resumo.csv figuras

O número da rodada (que, com a semente, define os sorteios) é a posição do
cenário na lista selecionada. Por isso, um cenário rodado isoladamente não
repete o valor do resumo.csv dos 108 cenários; a execução completa, em série
ou em paralelo, sempre gera os mesmos resultados.

Os CSVs contêm contadores de pacotes/bytes IP, entrega, perda, vazão,
atraso, jitter e justiça de Jain. A vazão é calculada na janela de tráfego
(do segundo 4 até dois segundos antes do fim). Atraso e jitter são médias
ponderadas por pacotes recebidos. As medidas de perdas TCP são da camada IP,
podendo incluir retransmissões; não representam perda de dados da aplicação.
"""

import argparse
import csv
import itertools
import math
import os
import shutil
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import get_context
from pathlib import Path

ns = None  # Carregado sob demanda (carregar_ns), pois a importação é lenta.


CLIENTES = (1, 2, 4, 8, 16, 32)
TAXA_BPS = 512_000


def argumentos():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mobilidade", choices=("estatico", "movel", "todos"), default="todos")
    parser.add_argument("--transporte", choices=("udp", "tcp", "misto", "todos"), default="todos")
    parser.add_argument("--aplicacao", choices=("cbr", "rajada", "cbr_rajada", "todos"), default="todos")
    parser.add_argument("--clientes", type=int, nargs="+", default=CLIENTES)
    parser.add_argument("--duracao", type=float, default=60.0)
    parser.add_argument("--saida", type=Path, default=None,
                        help="Pasta dos CSVs (padrão: resultados_equipe_6; "
                             "com --rapido: resultados_teste_rapido)")
    parser.add_argument("--semente", type=int, default=6)
    parser.add_argument("--processos", type=int, default=1,
                        help="Número de cenários executados ao mesmo tempo")
    parser.add_argument("--continuar", action="store_true",
                        help="Reaproveita cenários completos dos CSVs existentes")
    parser.add_argument("--rapido", action="store_true",
                        help="Teste rápido: estático, UDP, CBR, 2 clientes, 10 s")
    args = parser.parse_args()
    if args.rapido:
        args.mobilidade, args.transporte, args.aplicacao = "estatico", "udp", "cbr"
        args.clientes, args.duracao = [2], 10.0
    if args.saida is None:
        # O teste rápido não pode sobrescrever os CSVs dos 108 cenários.
        args.saida = Path("resultados_teste_rapido" if args.rapido else "resultados_equipe_6")
    if any(not 1 <= n <= 200 for n in args.clientes):
        parser.error("Cada quantidade de clientes deve estar entre 1 e 200.")
    if args.duracao <= 6:
        parser.error("A duração deve ser maior que 6 s.")
    if args.semente < 1:
        parser.error("A semente deve ser positiva.")
    if not 1 <= args.processos <= (os.cpu_count() or 1):
        parser.error("--processos deve estar entre 1 e a quantidade de núcleos disponíveis.")
    return args


def opcoes(escolha, todas):
    return todas if escolha == "todos" else (escolha,)


# Responsável: Gabriel Lopes Prodossimo.
def mobilidade(clientes, ap, modo, duracao):
    fixo = ns.MobilityHelper()
    fixo.SetPositionAllocator("ns3::GridPositionAllocator",
                              "MinX", ns.DoubleValue(70), "MinY", ns.DoubleValue(70),
                              "GridWidth", ns.UintegerValue(1))
    fixo.SetMobilityModel("ns3::ConstantPositionMobilityModel")
    fixo.Install(ap)

    estacoes = ns.MobilityHelper()
    colunas = math.ceil(math.sqrt(clientes.GetN()))
    passo = 50.0 / max(1, colunas - 1)
    estacoes.SetPositionAllocator("ns3::GridPositionAllocator",
                                  "MinX", ns.DoubleValue(45), "MinY", ns.DoubleValue(45),
                                  "DeltaX", ns.DoubleValue(passo),
                                  "DeltaY", ns.DoubleValue(passo),
                                  "GridWidth", ns.UintegerValue(colunas))
    estacoes.SetMobilityModel("ns3::ConstantVelocityMobilityModel" if modo == "movel"
                             else "ns3::ConstantPositionMobilityModel")
    estacoes.Install(clientes)
    if modo == "movel":
        if not hasattr(ns, "IniciarCaminhadaAleatoriaEquipe6"):
            # O binding Python não converte callbacks Python para EventImpl.
            # Por isso, as mudanças periódicas de direção são agendadas em C++.
            ns.cppyy.cppdef("""
                #include <algorithm>
                #include <cmath>
                namespace ns3 {
                void CaminhadaAleatoriaEquipe6(Ptr<ConstantVelocityMobilityModel> no,
                                                Ptr<UniformRandomVariable> direcoes,
                                                double velocidade, double fim) {
                    constexpr double intervalo = 2.0;
                    const double angulo = direcoes->GetValue(0.0, 6.283185307179586);
                    double vx = velocidade * std::cos(angulo);
                    double vy = velocidade * std::sin(angulo);
                    const Vector posicao = no->GetPosition();
                    const double restante = std::min(intervalo,
                                                       fim - Simulator::Now().GetSeconds());
                    // Reflete a componente que sairia do quadrado de 140 x 140 m.
                    if (posicao.x + vx * restante < 0.0 ||
                        posicao.x + vx * restante > 140.0) {
                        vx = -vx;
                    }
                    if (posicao.y + vy * restante < 0.0 ||
                        posicao.y + vy * restante > 140.0) {
                        vy = -vy;
                    }
                    no->SetVelocity(Vector(vx, vy, 0.0));
                    if (Simulator::Now().GetSeconds() + intervalo < fim) {
                        Simulator::Schedule(Seconds(intervalo),
                                            &CaminhadaAleatoriaEquipe6, no, direcoes,
                                            velocidade, fim);
                    }
                }
                void IniciarCaminhadaAleatoriaEquipe6(Ptr<ConstantVelocityMobilityModel> no,
                                                       double velocidade, double fim,
                                                       int64_t fluxo_aleatorio) {
                    auto direcoes = CreateObject<UniformRandomVariable>();
                    direcoes->SetStream(fluxo_aleatorio);
                    CaminhadaAleatoriaEquipe6(no, direcoes, velocidade, fim);
                }
                }
            """)
        # 1 e 2 m/s = 3,6 e 7,2 km/h. Cada cliente possui fluxo aleatório
        # próprio reproduzível pela semente e pelo número da rodada.
        for i in range(clientes.GetN()):
            modelo = clientes.Get(i).GetObject[ns.ConstantVelocityMobilityModel]()
            velocidade = 1.0 if i % 2 == 0 else 2.0
            ns.IniciarCaminhadaAleatoriaEquipe6(modelo, velocidade, duracao, 10000 + i)


# Responsável: Diego Fontes de Avila (LAN/IP) e Gabriel Lopes Prodossimo (Wi-Fi).
def topologia(n, modo, duracao):
    clientes = ns.NodeContainer()
    clientes.Create(n)
    lan = ns.NodeContainer()
    lan.Create(4)  # AP, s0, s1, s2 (servidor).
    ap, servidor = lan.Get(0), lan.Get(3)

    canal = ns.YansWifiChannelHelper.Default()
    phy = ns.YansWifiPhyHelper()
    phy.SetChannel(canal.Create())
    phy.Set("TxPowerStart", ns.DoubleValue(16.0))
    phy.Set("TxPowerEnd", ns.DoubleValue(16.0))
    phy.Set("Antennas", ns.UintegerValue(1))
    wifi = ns.WifiHelper()
    wifi.SetStandard("802.11a")
    mac = ns.WifiMacHelper()
    ssid = ns.Ssid("Equipe6")
    mac.SetType("ns3::StaWifiMac", "Ssid", ns.SsidValue(ssid),
                "ActiveProbing", ns.BooleanValue(False))
    dispositivos_sta = wifi.Install(phy, mac, clientes)
    mac.SetType("ns3::ApWifiMac", "Ssid", ns.SsidValue(ssid))
    dispositivos_ap = wifi.Install(phy, mac, ap)
    mobilidade(clientes, ap, modo, duracao)

    csma = ns.CsmaHelper()
    csma.SetChannelAttribute("DataRate", ns.StringValue("100Mbps"))
    csma.SetChannelAttribute("Delay", ns.TimeValue(ns.MicroSeconds(10)))
    dispositivos_lan = csma.Install(lan)
    pilha = ns.InternetStackHelper()
    pilha.Install(clientes)
    pilha.Install(lan)
    enderecos = ns.Ipv4AddressHelper()
    enderecos.SetBase(ns.Ipv4Address("192.168.0.0"), ns.Ipv4Mask("255.255.255.0"))
    ips_clientes = enderecos.Assign(dispositivos_sta)
    enderecos.Assign(dispositivos_ap)
    enderecos.SetBase(ns.Ipv4Address("10.1.1.0"), ns.Ipv4Mask("255.255.255.0"))
    ips_lan = enderecos.Assign(dispositivos_lan)
    ns.Ipv4GlobalRoutingHelper.PopulateRoutingTables()
    return clientes, servidor, ips_clientes


# Responsável: João Victor Costa Teodoro.
def aplicacoes(clientes, servidor, ips_clientes, transporte, padrao, duracao):
    """Uma fonte no servidor e um receptor no cliente para cada fluxo """
    configuracoes = []
    n = int(clientes.GetN())
    for i in range(n):
        protocolo = ("udp" if i < math.ceil(n / 2) else "tcp") if transporte == "misto" else transporte
        tipo = ("cbr" if i % 2 == 0 else "rajada") if padrao == "cbr_rajada" else padrao
        fabrica = "ns3::UdpSocketFactory" if protocolo == "udp" else "ns3::TcpSocketFactory"
        tamanho = 512 if protocolo == "udp" else 1500
        porta = 9000 + i
        ip_cliente = ips_clientes.GetAddress(i)
        destino = ns.InetSocketAddress(ip_cliente, porta).ConvertTo()
        local = ns.InetSocketAddress(ns.Ipv4Address.GetAny(), porta).ConvertTo()
        receptor = ns.PacketSinkHelper(fabrica, local).Install(clientes.Get(i))
        receptor.Start(ns.Seconds(1))
        receptor.Stop(ns.Seconds(duracao))
        fonte = ns.OnOffHelper(fabrica, destino)
        fonte.SetAttribute("DataRate", ns.DataRateValue(ns.DataRate(TAXA_BPS)))
        fonte.SetAttribute("PacketSize", ns.UintegerValue(tamanho))
        fonte.SetAttribute("OnTime", ns.StringValue(
            "ns3::ConstantRandomVariable[Constant=1000]" if tipo == "cbr"
            else "ns3::ConstantRandomVariable[Constant=1]"))
        fonte.SetAttribute("OffTime", ns.StringValue(
            "ns3::ConstantRandomVariable[Constant=0]" if tipo == "cbr"
            else "ns3::ConstantRandomVariable[Constant=1]"))
        transmissor = fonte.Install(servidor)
        transmissor.Start(ns.Seconds(4 + i * 0.001))
        transmissor.Stop(ns.Seconds(duracao - 2))
        configuracoes.append({"cliente": f"c{i}", "porta": porta,
                              "ip_destino": str(ip_cliente),
                              "protocolo": protocolo, "padrao": tipo,
                              "tamanho_bytes": tamanho})
    return configuracoes


# Responsável: Matheus Davi Leão.
def metricas(monitor, helper, configuracoes, duracao):
    monitor.CheckForLostPackets()
    classificador = ns.DynamicCast[ns.Ipv4FlowClassifier](helper.GetClassifier())
    por_porta = {item["porta"]: item for item in configuracoes}
    linhas = []
    vistos = set()
    janela = duracao - 6
    for flow_id, dados in monitor.GetFlowStats():
        tupla = classificador.FindFlow(flow_id)
        porta = int(tupla.destinationPort)
        if (porta not in por_porta or
                str(tupla.destinationAddress) != por_porta[porta]["ip_destino"]):
            continue  # Exclui ACKs TCP e outros fluxos de controle.
        tx, rx = int(dados.txPackets), int(dados.rxPackets)
        perda = max(0, tx - rx)
        linhas.append({**por_porta[porta], "flow_id": int(flow_id),
                       "tx_pacotes": tx, "rx_pacotes": rx, "perdidos_pacotes": perda,
                       "tx_bytes_ip": int(dados.txBytes), "rx_bytes_ip": int(dados.rxBytes),
                       "entrega_pct": 100 * rx / tx if tx else 0.0,
                       "perda_pct": 100 * perda / tx if tx else 0.0,
                       "vazao_mbps": 8 * int(dados.rxBytes) / janela / 1e6,
                       "atraso_medio_ms": 1000 * dados.delaySum.GetSeconds() / rx if rx else 0.0,
                       "jitter_medio_ms": (1000 * dados.jitterSum.GetSeconds() / (rx - 1)
                                           if rx > 1 else 0.0)})
        vistos.add(porta)
    for porta, base in por_porta.items():
        if porta not in vistos:
            linhas.append({**base, "flow_id": "", "tx_pacotes": 0,
                           "rx_pacotes": 0, "perdidos_pacotes": 0,
                           "tx_bytes_ip": 0, "rx_bytes_ip": 0,
                           "entrega_pct": 0.0, "perda_pct": 0.0,
                           "vazao_mbps": 0.0, "atraso_medio_ms": 0.0,
                           "jitter_medio_ms": 0.0})
    return sorted(linhas, key=lambda linha: linha["porta"])


def resumo(linhas):
    n = len(linhas)
    tx = sum(l["tx_pacotes"] for l in linhas)
    rx = sum(l["rx_pacotes"] for l in linhas)
    perdas = sum(l["perdidos_pacotes"] for l in linhas)
    vazoes = [l["vazao_mbps"] for l in linhas]
    vazao = sum(vazoes)
    pares_jitter = sum(max(0, l["rx_pacotes"] - 1) for l in linhas)
    return {"clientes": n,
            "clientes_udp": sum(l["protocolo"] == "udp" for l in linhas),
            "clientes_tcp": sum(l["protocolo"] == "tcp" for l in linhas),
            "clientes_cbr": sum(l["padrao"] == "cbr" for l in linhas),
            "clientes_rajada": sum(l["padrao"] == "rajada" for l in linhas),
            "tx_pacotes": tx, "rx_pacotes": rx, "perdidos_pacotes": perdas,
            "tx_bytes_ip": sum(l["tx_bytes_ip"] for l in linhas),
            "rx_bytes_ip": sum(l["rx_bytes_ip"] for l in linhas),
            "entrega_pct": 100 * rx / tx if tx else 0.0,
            "perda_pct": 100 * perdas / tx if tx else 0.0,
            "vazao_total_mbps": vazao,
            "vazao_media_cliente_mbps": vazao / n,
            "atraso_medio_ms": (sum(l["atraso_medio_ms"] * l["rx_pacotes"] for l in linhas) / rx
                                if rx else 0.0),
            "jitter_medio_ms": (sum(l["jitter_medio_ms"] * max(0, l["rx_pacotes"] - 1)
                                    for l in linhas) / pares_jitter if pares_jitter else 0.0),
            "justica_jain": (vazao * vazao / (n * sum(v * v for v in vazoes))
                             if any(vazoes) else 0.0)}


def agendar_progresso(duracao):
    """Exibe marcos da simulação mesmo enquanto o C++ ocupa o Python."""
    if duracao <= 10:
        return
    if not hasattr(ns, "AgendarProgressoEquipe6"):
        ns.cppyy.cppdef("""
            #include <iostream>
            namespace ns3 {
            void AgendarProgressoEquipe6(double instante) {
                Simulator::Schedule(Seconds(instante), [instante]() {
                    std::cout << "  tempo simulado: " << instante << " s" << std::endl;
                });
            }
            }
        """)
    instante = 10.0
    while instante < duracao:
        ns.AgendarProgressoEquipe6(instante)
        instante += 10.0


def executar(n, modo, transporte, padrao, duracao, semente, rodada,
             mostrar_progresso=True):
    ns.RngSeedManager.SetSeed(semente)
    ns.RngSeedManager.SetRun(rodada)
    # O ns-3 numera os fluxos aleatórios com um contador global que não volta a
    # zero em Simulator::Destroy. Sem este reset, o resultado de um cenário
    # dependeria dos cenários executados antes no mesmo processo.
    ns.RngSeedManager.ResetNextStreamIndex()
    try:
        clientes, servidor, ips_clientes = topologia(n, modo, duracao)
        configs = aplicacoes(clientes, servidor, ips_clientes, transporte, padrao, duracao)
        helper = ns.FlowMonitorHelper()
        monitor = helper.InstallAll()
        if mostrar_progresso:
            agendar_progresso(duracao)
        ns.Simulator.Stop(ns.Seconds(duracao))
        ns.Simulator.Run()
        linhas = metricas(monitor, helper, configs, duracao)
        return resumo(linhas), linhas
    finally:
        ns.Simulator.Destroy()


def salvar(caminho, linhas):
    temporario = caminho.with_name(f".{caminho.name}.{os.getpid()}.tmp")
    with temporario.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(linhas[0]))
        escritor.writeheader()
        escritor.writerows(linhas)
    os.replace(temporario, caminho)


def carregar_ns():
    global ns
    from ns import ns as modulo_ns
    ns = modulo_ns


def identificar(rodada, modo, transporte, padrao, duracao, semente):
    return {"mobilidade": modo, "transporte": transporte,
            "aplicacao": padrao, "duracao_s": duracao,
            "semente": semente, "rodada": rodada,
            "area_m": "140x140", "padrao_wifi": "802.11a",
            "ssid": "Equipe6", "potencia_dbm": 16,
            "antenas_ap": 1, "taxa_cliente_kbps": 512,
            "velocidade_kmh": "3.6-7.2" if modo == "movel" else "0",
            "modelo_mobilidade": ("ConstantVelocityMobilityModel" if modo == "movel"
                                  else "ConstantPositionMobilityModel"),
            "modelo_caminhada": "direcao_aleatoria_2s" if modo == "movel" else "nao_aplica",
            "direcao_trafego": "servidor_para_clientes",
            "quadro_udp_bytes": 512, "quadro_tcp_bytes": 1500,
            "rede_wifi": "192.168.0.0/24", "rede_lan": "10.1.1.0/24"}


def rodar_tarefa(tarefa):
    rodada, modo, transporte, padrao, n, duracao, semente, progresso = tarefa
    inicio = time.monotonic()
    agregado, individuais = executar(n, modo, transporte, padrao, duracao,
                                     semente, rodada, progresso)
    identificacao = identificar(rodada, modo, transporte, padrao, duracao, semente)
    return ({**identificacao, **agregado},
            [{**identificacao, **linha} for linha in individuais],
            time.monotonic() - inicio)


def ler_csv(caminho):
    with caminho.open(newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def resultados_anteriores(saida, cenarios, duracao, semente):
    caminho_resumo = saida / "resumo.csv"
    caminho_fluxos = saida / "fluxos.csv"
    if not caminho_resumo.exists() and not caminho_fluxos.exists():
        return [], []
    if not caminho_resumo.exists() or not caminho_fluxos.exists():
        raise SystemExit("Para --continuar, resumo.csv e fluxos.csv precisam existir juntos.")
    anteriores = ler_csv(caminho_resumo)
    fluxos = ler_csv(caminho_fluxos)
    por_rodada = {}
    for fluxo in fluxos:
        por_rodada.setdefault(fluxo["rodada"], []).append(fluxo)
    validos, fluxos_validos = [], []
    moveis_antigos = 0
    uplink_antigo = 0
    for linha in anteriores:
        try:
            rodada = int(linha["rodada"])
            modo, transporte, padrao, n = cenarios[rodada - 1]
            confere = (linha["mobilidade"] == modo and
                       linha["transporte"] == transporte and
                       linha["aplicacao"] == padrao and
                       int(linha["clientes"]) == n and
                       float(linha["duracao_s"]) == duracao and
                       int(linha["semente"]) == semente)
        except (IndexError, KeyError, TypeError, ValueError):
            confere = False
        if not confere:
            raise SystemExit("Os CSVs existentes pertencem a outra configuração. "
                             "Use outro --saida para não sobrescrevê-los.")
        if linha.get("direcao_trafego") != "servidor_para_clientes":
            uplink_antigo += 1
            continue  # Resultados cliente -> servidor medem outra topologia de tráfego.
        if modo == "movel" and linha.get("modelo_caminhada") != "direcao_aleatoria_2s":
            moveis_antigos += 1
            continue  # Resultados com movimento determinístico não são reutilizados.
        individuais = por_rodada.get(str(rodada), [])
        if len(individuais) == n:
            linha["modelo_caminhada"] = ("direcao_aleatoria_2s" if modo == "movel"
                                         else "nao_aplica")
            for fluxo in individuais:
                fluxo["modelo_caminhada"] = linha["modelo_caminhada"]
            validos.append(linha)
            fluxos_validos.extend(individuais)
    if moveis_antigos or uplink_antigo:
        # A próxima gravação substitui as linhas antigas; guarde os CSVs originais.
        for caminho in (caminho_resumo, caminho_fluxos):
            sufixo = "uplink_antigo" if uplink_antigo else "mobilidade_antiga"
            backup = caminho.with_name(f"{caminho.stem}_{sufixo}.csv")
            if not backup.exists():
                shutil.copy2(caminho, backup)
    if uplink_antigo:
        print(f"Ignorando {uplink_antigo} cenário(s) de upload; "
              "serão recalculados de servidor para clientes. "
              "CSVs originais preservados como *_uplink_antigo.csv.", flush=True)
    if moveis_antigos:
        print(f"Ignorando {moveis_antigos} cenário(s) móveis antigos; "
              "serão recalculados com caminhada aleatória. "
              "CSVs originais preservados como *_mobilidade_antiga.csv.", flush=True)
    return validos, fluxos_validos


# Responsável: Matheus Davi Leão.
def main():
    args = argumentos()
    cenarios = list(itertools.product(
        opcoes(args.mobilidade, ("estatico", "movel")),
        opcoes(args.transporte, ("udp", "tcp", "misto")),
        opcoes(args.aplicacao, ("cbr", "rajada", "cbr_rajada")), args.clientes))
    args.saida.mkdir(parents=True, exist_ok=True)
    resumos, fluxos = (resultados_anteriores(args.saida, cenarios, args.duracao, args.semente)
                       if args.continuar else ([], []))
    concluidas = {int(linha["rodada"]) for linha in resumos}
    tarefas = [(rodada, modo, transporte, padrao, n, args.duracao, args.semente,
                args.processos == 1)
               for rodada, (modo, transporte, padrao, n) in enumerate(cenarios, 1)
               if rodada not in concluidas]
    print(f"{len(cenarios)} cenários de {args.duracao:g} s simulados; "
          f"{len(concluidas)} já concluídos, {len(tarefas)} pendentes.", flush=True)
    if not tarefas:
        print(f"Resultados: {args.saida.resolve()}")
        return

    def registrar(resultado):
        agregado, individuais, tempo_real = resultado
        resumos.append(agregado)
        fluxos.extend(individuais)
        resumos.sort(key=lambda linha: int(linha["rodada"]))
        fluxos.sort(key=lambda linha: (int(linha["rodada"]), int(linha["porta"])))
        salvar(args.saida / "resumo.csv", resumos)
        salvar(args.saida / "fluxos.csv", fluxos)
        print(f"[{len(resumos)}/{len(cenarios)}] {agregado['mobilidade']}, "
              f"{agregado['transporte']}, {agregado['aplicacao']}, "
              f"{agregado['clientes']} cliente(s): "
              f"{agregado['vazao_total_mbps']:.3f} Mbps, "
              f"entrega {agregado['entrega_pct']:.1f}%, "
              f"{tempo_real:.1f} s reais", flush=True)

    if args.processos == 1:
        print("Carregando ns-3; a inicialização pode levar cerca de um minuto...", flush=True)
        inicio_carga = time.monotonic()
        try:
            carregar_ns()
        except ModuleNotFoundError as erro:
            raise SystemExit("ns-3 não encontrado. Use .venv/bin/python.") from erro
        print(f"ns-3 carregado em {time.monotonic() - inicio_carga:.1f} s.", flush=True)
        for tarefa in tarefas:
            print(f"Iniciando rodada {tarefa[0]}: {tarefa[1]}, {tarefa[2]}, "
                  f"{tarefa[3]}, {tarefa[4]} cliente(s)", flush=True)
            registrar(rodar_tarefa(tarefa))
    else:
        quantidade = min(args.processos, len(tarefas))
        print(f"Carregando ns-3 em {quantidade} processos paralelos...", flush=True)
        with ProcessPoolExecutor(max_workers=quantidade,
                                 mp_context=get_context("spawn"),
                                 initializer=carregar_ns) as executor:
            futuros = [executor.submit(rodar_tarefa, tarefa) for tarefa in tarefas]
            for futuro in as_completed(futuros):
                registrar(futuro.result())
    print(f"Resultados: {args.saida.resolve()}")


if __name__ == "__main__":
    main()

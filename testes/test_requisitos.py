"""Testes que comprovam que o trabalho da Equipe 6 atende ao enunciado do PCS3614.

Uso (a partir da raiz do repositório):
    <python-com-ns3> -m unittest -v testes/test_requisitos.py

Variáveis de ambiente opcionais:
    RESULTADOS  pasta com resumo.csv e fluxos.csv dos 108 cenários
                (padrão: REVISAR_REDES/REVISAR_REDES/resultados_equipe_6)
    SEM_NS3=1   pula os testes que precisam carregar o ns-3

Cada teste cita o item do enunciado (Instrucoes_Projeto_PCS3614_2026.pdf) que verifica.
"""

import csv
import importlib.util
import itertools
import math
import os
import re
import shutil
import subprocess
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ENTREGA = RAIZ / "REVISAR_REDES" / "REVISAR_REDES"
SCRIPT = ENTREGA / "equipe_6_3q2026.py"
RELATORIO_PDF = ENTREGA / "equipe_6_relatorio_redes_3q2026.pdf"
RELATORIO_TEX = ENTREGA / "equipe_6_relatorio_redes_3q2026.tex"
RESULTADOS = Path(os.environ.get("RESULTADOS", ENTREGA / "resultados_equipe_6"))
CLIENTES = (1, 2, 4, 8, 16, 32)
INTEGRANTES = ("Diego Fontes de Avila", "Gabriel Lopes Prodossimo",
               "João Victor Costa Teodoro", "Matheus Davi Leão",
               "Sophia Soares Mariano")


def carregar_script():
    spec = importlib.util.spec_from_file_location("equipe6", SCRIPT)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def texto_pdf():
    return subprocess.run(["pdftotext", "-layout", str(RELATORIO_PDF), "-"],
                          check=True, capture_output=True, text=True).stdout


class Entregaveis(unittest.TestCase):
    """Seção 1.1 (nomenclatura) e item 4 das instruções (máximo de 8 páginas)."""

    def test_nomes_dos_arquivos(self):
        self.assertRegex(RELATORIO_PDF.name, r"^equipe_\d+_relatorio_redes_3q2026\.pdf$")
        self.assertRegex(SCRIPT.name, r"^equipe_\d+_3q2026\.(cc|py)$")
        self.assertTrue(RELATORIO_PDF.is_file() and SCRIPT.is_file())

    @unittest.skipUnless(shutil.which("pdfinfo"), "pdfinfo não instalado")
    def test_relatorio_tem_no_maximo_8_paginas(self):
        info = subprocess.run(["pdfinfo", str(RELATORIO_PDF)], check=True,
                              capture_output=True, text=True).stdout
        paginas = int(re.search(r"Pages:\s+(\d+)", info).group(1))
        self.assertLessEqual(paginas, 8)

    def test_relatorio_usa_template_sbc(self):
        self.assertIn(r"\usepackage{sbc-template}", RELATORIO_TEX.read_text(encoding="utf-8"))
        self.assertTrue((ENTREGA / "sbc-template.sty").is_file())


@unittest.skipUnless(shutil.which("pdftotext"), "pdftotext não instalado")
class Relatorio(unittest.TestCase):
    """Seção 2: organização obrigatória das seções do relatório."""

    @classmethod
    def setUpClass(cls):
        cls.texto = texto_pdf()

    def test_secoes_na_ordem_exigida(self):
        secoes = ["Resumo", "Introdução", "Descrição do exercício proposto",
                  "Avaliação de desempenho", "Metodologia", "Parâmetros",
                  "Resultados", "Discussão dos resultados",
                  "Detalhamento da divisão do trabalho", "Conclusão"]
        posicao = -1
        for secao in secoes:
            achada = self.texto.find(secao, posicao + 1)
            self.assertGreater(achada, posicao, f"seção fora de ordem ou ausente: {secao}")
            posicao = achada

    def test_figura_da_topologia(self):
        self.assertIn("Figura 1. Topologia", self.texto)
        self.assertTrue((ENTREGA / "figuras" / "topologia.pdf").is_file())

    def test_configuracao_da_maquina(self):
        self.assertRegex(self.texto, r"Intel Core i[357]")
        self.assertRegex(self.texto, r"GiB de memória")

    def test_tabela_de_parametros(self):
        self.assertIn("Tabela 1. Parâmetros", self.texto)

    def test_graficos_de_vazao_atraso_e_perda(self):
        for figura in ("vazao", "atraso", "perda"):
            self.assertTrue((ENTREGA / "figuras" / f"{figura}.pdf").is_file())
        self.assertIn("Figura 2. Vazão", self.texto)
        self.assertIn("Figura 3. Atraso", self.texto)
        self.assertIn("Figura 4. Fração de pacotes", self.texto)

    def test_divisao_do_trabalho_com_todos_os_integrantes(self):
        # Os nomes aparecem como autores e (abreviados) na Tabela 2.
        texto = " ".join(self.texto.split())
        for nome in INTEGRANTES:
            self.assertIn(nome, texto)
        for nusp in ("15447910", "15453560", "15463850", "15520593", "15511213"):
            self.assertIn(nusp, texto)
        self.assertNotIn("Codex", texto)


class Script(unittest.TestCase):
    """Seção 3.2: parâmetros da simulação definidos no código."""

    @classmethod
    def setUpClass(cls):
        cls.codigo = SCRIPT.read_text(encoding="utf-8")

    def test_ssid_da_equipe(self):
        self.assertIn('ns.Ssid("Equipe6")', self.codigo)

    def test_quantidades_de_clientes(self):
        self.assertEqual(carregar_script().CLIENTES, CLIENTES)

    def test_argumentos_sem_erro(self):
        # Regressão: args.rapido era usado sem o argumento existir.
        modulo = carregar_script()
        import sys
        antigo = sys.argv
        try:
            sys.argv = ["x", "--rapido"]
            args = modulo.argumentos()
            self.assertEqual((args.clientes, args.duracao), ([2], 10.0))
            self.assertEqual(args.saida, Path("resultados_teste_rapido"))
            sys.argv = ["x"]
            args = modulo.argumentos()
            self.assertEqual(tuple(args.clientes), CLIENTES)
            self.assertEqual(args.saida, Path("resultados_equipe_6"))
        finally:
            sys.argv = antigo


@unittest.skipIf(os.environ.get("SEM_NS3") == "1", "SEM_NS3=1")
class SimulacaoNs3(unittest.TestCase):
    """Seção 3.2: topologia, Wi-Fi, mobilidade e aplicações montadas no ns-3."""

    @classmethod
    def setUpClass(cls):
        cls.m = carregar_script()
        try:
            cls.m.carregar_ns()
        except ModuleNotFoundError:
            raise unittest.SkipTest("ns-3 não encontrado neste Python")
        cls.ns = cls.m.ns

    def tearDown(self):
        self.ns.Simulator.Destroy()

    def ipv4(self, no, interface=1):
        return str(no.GetObject[self.ns.Ipv4]().GetAddress(interface, 0).GetLocal())

    def test_topologia_cabeada_e_sem_fio(self):
        ns = self.ns
        clientes, servidor, ips = self.m.topologia(4, "estatico", 20)
        self.assertEqual(clientes.GetN(), 4)
        # Servidor (s2) é o último nó da LAN 10.1.1.0: AP=.1, s0=.2, s1=.3, s2=.4.
        self.assertEqual(self.ipv4(servidor), "10.1.1.4")
        self.assertIsNotNone(servidor.GetDevice(1).GetObject[ns.CsmaNetDevice]())
        for i in range(4):
            self.assertTrue(str(ips.GetAddress(i)).startswith("192.168.0."))
            dispositivo = ns.DynamicCast[ns.WifiNetDevice](clientes.Get(i).GetDevice(0))
            self.assertEqual(dispositivo.GetStandard(), ns.WIFI_STANDARD_80211a)
            # O ns-3 imprime o SSID como "ssid=<nome>".
            self.assertEqual(str(dispositivo.GetMac().GetSsid()).removeprefix("ssid="), "Equipe6")
            self.assertTrue(dispositivo.GetMac().GetObject[ns.StaWifiMac]())

    def test_clientes_estaticos_nao_se_movem(self):
        ns = self.ns
        clientes, _, _ = self.m.topologia(4, "estatico", 20)
        modelos = [clientes.Get(i).GetObject[ns.MobilityModel]() for i in range(4)]
        inicio = [(m.GetPosition().x, m.GetPosition().y) for m in modelos]
        ns.Simulator.Stop(ns.Seconds(10))
        ns.Simulator.Run()
        for modelo, (x, y) in zip(modelos, inicio):
            self.assertEqual(modelo.GetInstanceTypeId().GetName(),
                             "ns3::ConstantPositionMobilityModel")
            self.assertEqual((modelo.GetPosition().x, modelo.GetPosition().y), (x, y))

    def test_clientes_moveis_caminham_a_1_ou_2_m_s(self):
        ns = self.ns
        clientes, _, _ = self.m.topologia(8, "movel", 30)
        modelos = [clientes.Get(i).GetObject[ns.MobilityModel]() for i in range(8)]
        inicio = [(m.GetPosition().x, m.GetPosition().y) for m in modelos]

        ns.Simulator.Stop(ns.Seconds(25))
        ns.Simulator.Run()
        for i, (modelo, (x, y)) in enumerate(zip(modelos, inicio)):
            v = modelo.GetVelocity()
            velocidade = math.hypot(v.x, v.y)
            self.assertAlmostEqual(velocidade, 1.0 if i % 2 == 0 else 2.0, places=6)
            p = modelo.GetPosition()
            self.assertNotEqual((p.x, p.y), (x, y))
            self.assertTrue(0 <= p.x <= 140 and 0 <= p.y <= 140)

    def test_transportes_udp_tcp_e_misto(self):
        for transporte, esperado in (("udp", (4, 0)), ("tcp", (0, 4)), ("misto", (2, 2))):
            clientes, servidor, ips = self.m.topologia(4, "estatico", 20)
            configs = self.m.aplicacoes(clientes, servidor, ips, transporte, "cbr", 20)
            udp = sum(c["protocolo"] == "udp" for c in configs)
            tcp = sum(c["protocolo"] == "tcp" for c in configs)
            self.assertEqual((udp, tcp), esperado, transporte)
            self.ns.Simulator.Destroy()

    def test_cenario_reproduzivel_no_mesmo_processo(self):
        # Regressão: sem ResetNextStreamIndex, a 2ª execução dava outro resultado.
        primeiro, _ = self.m.executar(4, "estatico", "tcp", "rajada", 12, 6, 27, False)
        self.m.executar(2, "movel", "udp", "cbr", 8, 6, 5, False)
        segundo, _ = self.m.executar(4, "estatico", "tcp", "rajada", 12, 6, 27, False)
        self.assertEqual(primeiro, segundo)

    def test_execucao_mede_vazao_atraso_e_perda(self):
        resumo, fluxos = self.m.executar(4, "movel", "misto", "cbr_rajada", 10, 6, 1, False)
        for chave in ("vazao_total_mbps", "atraso_medio_ms", "perda_pct"):
            self.assertIn(chave, resumo)
        self.assertEqual(len(fluxos), 4)
        self.assertGreater(resumo["vazao_total_mbps"], 0)
        self.assertGreater(resumo["atraso_medio_ms"], 0)
        self.assertGreaterEqual(resumo["perda_pct"], 0)


@unittest.skipUnless((RESULTADOS / "resumo.csv").is_file(), "resultados não encontrados")
class Resultados(unittest.TestCase):
    """Seção 3.2, itens 1 a 6: todas as variações de cenário foram executadas."""

    @classmethod
    def setUpClass(cls):
        with (RESULTADOS / "resumo.csv").open(encoding="utf-8") as arquivo:
            cls.linhas = list(csv.DictReader(arquivo))
        cls.por_cenario = {(l["mobilidade"], l["transporte"], l["aplicacao"],
                            int(l["clientes"])): l for l in cls.linhas}

    def test_108_cenarios_completos(self):
        esperado = set(itertools.product(("estatico", "movel"), ("udp", "tcp", "misto"),
                                         ("cbr", "rajada", "cbr_rajada"), CLIENTES))
        self.assertEqual(set(self.por_cenario), esperado)
        self.assertEqual(len(self.linhas), 108)

    def test_misto_metade_udp_metade_tcp(self):
        for (_, transporte, _, n), linha in self.por_cenario.items():
            if transporte == "misto" and n > 1:
                self.assertEqual(int(linha["clientes_udp"]), n // 2)
                self.assertEqual(int(linha["clientes_tcp"]), n // 2)

    def test_metricas_presentes(self):
        for linha in self.linhas:
            self.assertGreater(float(linha["vazao_total_mbps"]), 0)
            self.assertGreater(float(linha["atraso_medio_ms"]), 0)
            self.assertTrue(0 <= float(linha["perda_pct"]) <= 100)

    def test_valores_citados_no_relatorio(self):
        """Os números do texto do relatório saem destes CSVs."""
        def valor(mob, tr, app, chave):
            return float(self.por_cenario[(mob, tr, app, 32)][chave])
        casos = [
            ("estatico", "udp", "cbr", "vazao_total_mbps", 16.757, 0.0005),
            ("estatico", "udp", "rajada", "vazao_total_mbps", 8.624, 0.0005),
            ("estatico", "udp", "cbr_rajada", "vazao_total_mbps", 12.954, 0.0005),
            ("movel", "udp", "cbr_rajada", "vazao_total_mbps", 10.313, 0.0005),
            ("estatico", "udp", "cbr", "entrega_pct", 97.0, 0.05),
            ("estatico", "udp", "cbr", "atraso_medio_ms", 159.9, 0.05),
            ("estatico", "udp", "rajada", "atraso_medio_ms", 16.8, 0.05),
            ("estatico", "udp", "cbr_rajada", "atraso_medio_ms", 12.4, 0.05),
            ("movel", "udp", "cbr_rajada", "perda_pct", 20.4, 0.05),
            ("movel", "udp", "cbr_rajada", "atraso_medio_ms", 148.0, 0.05),
            ("estatico", "misto", "cbr", "entrega_pct", 97.3, 0.05),
            ("movel", "misto", "cbr", "entrega_pct", 80.5, 0.05),
            ("estatico", "misto", "cbr", "atraso_medio_ms", 172.7, 0.05),
            ("movel", "misto", "cbr", "atraso_medio_ms", 232.3, 0.05),
            ("estatico", "tcp", "cbr", "atraso_medio_ms", 183.7, 0.05),
            ("movel", "tcp", "cbr", "atraso_medio_ms", 181.6, 0.05),
            ("estatico", "tcp", "cbr", "perda_pct", 1.2, 0.05),
            ("movel", "tcp", "cbr", "perda_pct", 1.5, 0.05),
            ("estatico", "tcp", "rajada", "jitter_medio_ms", 2.1, 0.05),
            ("movel", "tcp", "rajada", "jitter_medio_ms", 3.9, 0.05),
            ("movel", "udp", "cbr_rajada", "justica_jain", 0.878, 0.0005),
        ]
        for mob, tr, app, chave, esperado, tolerancia in casos:
            with self.subTest(cenario=(mob, tr, app, chave)):
                self.assertAlmostEqual(valor(mob, tr, app, chave), esperado,
                                       delta=tolerancia)


if __name__ == "__main__":
    unittest.main(verbosity=2)

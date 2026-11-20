#!/usr/bin/env python3
"""
Gera dados FICTÍCIOS no mesmo layout dos arquivos abertos do CNPJ (Receita Federal),
para o pipeline rodar sem baixar nada. Nenhuma empresa ou pessoa aqui é real:
os CNPJs começam com 000 e os nomes são inventados.

Uso:  python3 exemplo/gerar_exemplo.py
"""
import csv
import os
import random

random.seed(42)
AQUI = os.path.dirname(os.path.abspath(__file__))

MUNICIPIOS = {  # código fictício -> nome
    "9001": "RIO DE JANEIRO", "9002": "NITEROI", "9003": "SAO GONCALO",
    "9004": "DUQUE DE CAXIAS", "9005": "NOVA IGUACU", "9006": "PETROPOLIS",
}
CNAES_ICP = ["8650003", "8650004", "8650005", "8650006", "8650099", "8690901"]
CNAES_OUTROS = ["8630503", "8550302", "8599699", "4771701", "9602501"]
PREFIXOS = ["CLINICA", "ESPACO", "CENTRO", "INSTITUTO", "NUCLEO", "CONSULTORIO", "STUDIO", ""]
TEMAS = ["DESENVOLVER", "CRESCER", "TEA KIDS", "NEURO INFANTIL", "INTEGRADO", "MULTI TERAPIAS",
         "VIVER", "ABA AFETO", "INCLUSAO", "SER", "EQUILIBRIO", "FALA E MOVIMENTO", "ACOLHER"]
BAIRROS = ["CENTRO", "MEIER", "TIJUCA", "BOTAFOGO", "ICARAI", "ALCANTARA", "CAMPO GRANDE"]
SITUACOES = ["02"] * 9 + ["08"]  # 08 = baixada


def escrever(nome, linhas):
    with open(os.path.join(AQUI, nome), "w", encoding="latin-1", newline="") as f:
        csv.writer(f, delimiter=";", quoting=csv.QUOTE_ALL).writerows(linhas)


def main():
    escrever("K3241.K03200Y0.D61114.MUNICCSV", [[k, v] for k, v in MUNICIPIOS.items()])
    estab, empre, socio = [], [], []
    for i in range(1, 121):
        basico = f"000{i:05d}"
        tema = random.choice(TEMAS)
        prefixo = random.choice(PREFIXOS)
        fantasia = f"{prefixo} {tema}".strip()
        razao = f"{fantasia} EXEMPLO {i:03d} LTDA"
        n_icp = random.choices([0, 1, 2, 3, 4], weights=[2, 4, 4, 2, 1])[0]
        cnaes = random.sample(CNAES_ICP, n_icp) + random.sample(CNAES_OUTROS, random.randint(0, 2))
        if not cnaes:
            cnaes = [random.choice(CNAES_OUTROS)]
        random.shuffle(cnaes)
        mun = random.choice(list(MUNICIPIOS))
        uf = "RJ" if random.random() > 0.05 else "SP"
        estab.append([basico, "0001", f"{i % 100:02d}", "1", fantasia, random.choice(SITUACOES), "20240101",
                      "00", "", "", f"20{random.randint(10, 25):02d}0{random.randint(1, 9)}15",
                      cnaes[0], ",".join(cnaes[1:]), "RUA", "EXEMPLO", str(random.randint(1, 999)), "",
                      random.choice(BAIRROS), f"2{random.randint(0, 9999999):07d}", uf, mun,
                      "21", "00000000", "", "", "", "", "contato@exemplo.invalid", "", ""])
        capital = random.choice([1000, 5000, 20000, 50000, 100000, 250000])
        empre.append([basico, razao, "2062", "49", f"{capital},00", random.choice(["01", "03", "05"]), ""])
        for s in range(random.choices([0, 1, 2, 3, 4], weights=[2, 4, 4, 2, 1])[0]):
            socio.append([basico, "2", f"SOCIO FICTICIO {i:03d}-{s + 1}", "***000000**", "49",
                          "20240101", "", "***000000**", "", "00", "4"])
    escrever("K3241.K03200Y0.D61114.ESTABELE", estab)
    escrever("K3241.K03200Y0.D61114.EMPRECSV", empre)
    escrever("K3241.K03200Y0.D61114.SOCIOCSV", socio)
    print(f"{len(estab)} estabelecimentos, {len(empre)} empresas e {len(socio)} sócios fictícios em {AQUI}/")


if __name__ == "__main__":
    main()

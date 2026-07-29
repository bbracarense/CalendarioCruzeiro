#!/usr/bin/env python3
"""
Busca automaticamente os jogos do Cruzeiro e escreve jogos.json sozinho —
ninguém precisa editar esse arquivo à mão.

Duas fontes de dados, porque nenhuma sozinha cobre tudo de graça:
  1) football-data.org -> Brasileirão Série A
  2) API-Football       -> Copa do Brasil, Libertadores, Sul-Americana
     (essas competições não existem no plano gratuito da football-data.org)

Chaves de API esperadas nas variáveis de ambiente (no GitHub Actions são
"Secrets" — veja o README, ninguém digita chave dentro do código):
  - FOOTBALL_DATA_API_KEY
  - API_FOOTBALL_KEY

Se a chave da API-Football não estiver configurada, o script simplesmente
pula a busca de copas e continua funcionando só com o Brasileirão (não
quebra nada pra quem ainda não configurou a segunda chave).

Como funciona a lógica de datas/placar (igual pras duas fontes):
  - Jogo sem data definida ainda -> entra como aviso de dia inteiro,
    marcado "[data a confirmar]".
  - Data/hora confirmada -> vira um evento com hora certa (atualiza o
    mesmo evento, não duplica).
  - Jogo encerrado -> o placar final é adicionado no título e na descrição.
  - O nome do estádio, quando disponível na fonte, vai no campo "local".
"""

import json
import os
import sys
import urllib.request
import urllib.error

ARQUIVO_SAIDA = "jogos.json"
ARQUIVO_APELIDOS = "nomes_times.json"
NOME_TIME = "Cruzeiro"

# ---------------------------------------------------------------------
# Apelidos dos times (nomes_times.json) — igual antes
# ---------------------------------------------------------------------

def carregar_apelidos() -> dict:
    try:
        with open(ARQUIVO_APELIDOS, encoding="utf-8") as f:
            apelidos = json.load(f)
    except FileNotFoundError:
        return {}
    apelidos.pop("_como_usar", None)
    return apelidos

def normalizar_nome(nome: str, apelidos: dict) -> str:
    return apelidos.get(nome, nome)

def chamar_api(url: str, headers: dict) -> dict:
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            corpo = resp.read()
    except urllib.error.HTTPError as e:
        print(f"Erro ao consultar {url}: {e.code} {e.reason}", file=sys.stderr)
        return {}
    except urllib.error.URLError as e:
        print(f"Erro de conexão com {url}: {e.reason}", file=sys.stderr)
        return {}

    try:
        return json.loads(corpo)
    except json.JSONDecodeError:
        print(f"Aviso: resposta de {url} não era JSON válido, ignorando.", file=sys.stderr)
        return {}

# ---------------------------------------------------------------------
# Fonte 1: football-data.org (Brasileirão)
# ---------------------------------------------------------------------

STATUS_FOOTBALL_DATA = {
    "SCHEDULED": "agendado",
    "TIMED": "agendado",
    "IN_PLAY": "em andamento",
    "PAUSED": "em andamento",
    "FINISHED": "encerrado",
    "POSTPONED": "adiado",
    "SUSPENDED": "suspenso",
    "CANCELLED": "cancelado",
}

def buscar_brasileirao(token: str, apelidos: dict) -> list:
    if not token:
        print("Aviso: FOOTBALL_DATA_API_KEY não configurada, pulando o Brasileirão.")
        return []

    dados = chamar_api(
        "https://api.football-data.org/v4/competitions/BSA/matches",
        {"X-Auth-Token": token},
    )
    jogos = []
    for partida in dados.get("matches", []):
        mandante = partida["homeTeam"]["name"] or ""
        visitante = partida["awayTeam"]["name"] or ""
        if NOME_TIME not in mandante and NOME_TIME not in visitante:
            continue

        status = partida.get("status", "SCHEDULED")
        utc_date = partida.get("utcDate")

        jogo = {
            "competicao": "Brasileirão",
            "mandante": normalizar_nome(mandante, apelidos),
            "visitante": normalizar_nome(visitante, apelidos),
            "chave_unica": f"BSA-{partida.get('matchday')}-{mandante}-{visitante}",
            "local": (partida.get("venue") or ""),
            "status": STATUS_FOOTBALL_DATA.get(status, status),
            "data_confirmada": utc_date is not None,
        }
        if utc_date:
            jogo["utc_datetime"] = utc_date
        if status == "FINISHED":
            jogo["gols_mandante"] = partida["score"]["fullTime"]["home"]
            jogo["gols_visitante"] = partida["score"]["fullTime"]["away"]
        jogos.append(jogo)

    return jogos

# ---------------------------------------------------------------------
# Fonte 2: API-Football (Copa do Brasil, Libertadores, Sul-Americana)
# ---------------------------------------------------------------------

API_FOOTBALL_BASE = "https://v3.football.api-sports.io"

# Nomes exatamente como a API-Football chama essas competições na busca.
COMPETICOES_COPAS = {
    "Copa do Brasil": "Copa do Brasil",
    "CONMEBOL Libertadores": "Libertadores",
    "CONMEBOL Sudamericana": "Sul-Americana",
}

STATUS_API_FOOTBALL = {
    "TBD": "agendado",       # data a definir
    "NS": "agendado",        # not started
    "1H": "em andamento",
    "HT": "em andamento",
    "2H": "em andamento",
    "ET": "em andamento",
    "P": "em andamento",
    "FT": "encerrado",
    "AET": "encerrado",
    "PEN": "encerrado",
    "PST": "adiado",
    "CANC": "cancelado",
    "ABD": "suspenso",
}

def buscar_id_time(headers: dict) -> int | None:
    dados = chamar_api(
        f"{API_FOOTBALL_BASE}/teams?search={NOME_TIME}", headers
    )
    if dados.get("errors"):
        print(f"Aviso: a API-Football retornou um erro ao buscar o time: {dados['errors']}", file=sys.stderr)
    respostas = dados.get("response") or []
    for item in respostas:
        time = item.get("team") or {}
        if time.get("country") == "Brazil" and time.get("name") == "Cruzeiro":
            return time.get("id")
    for item in respostas:
        time = item.get("team") or {}
        if time.get("country") == "Brazil":
            return time.get("id")
    return None

def buscar_id_liga(nome_busca: str, headers: dict) -> tuple[int, int] | None:
    """Retorna (id_da_liga, ano_da_temporada_atual) ou None se não achar."""
    dados = chamar_api(
        f"{API_FOOTBALL_BASE}/leagues?search={nome_busca}", headers
    )
    if dados.get("errors"):
        print(f"Aviso: a API-Football retornou um erro ao buscar '{nome_busca}': {dados['errors']}", file=sys.stderr)
    for item in dados.get("response") or []:
        liga = item.get("league") or {}
        for temporada in item.get("seasons") or []:
            if temporada.get("current"):
                return liga.get("id"), temporada.get("year")
    return None

def buscar_copas(token: str, apelidos: dict) -> list:
    if not token:
        print("Aviso: API_FOOTBALL_KEY não configurada, pulando Copa do Brasil/Libertadores/Sul-Americana.")
        return []

    headers = {"x-apisports-key": token}
    time_id = buscar_id_time(headers)
    if not time_id:
        print("Aviso: não encontrei o Cruzeiro na API-Football.", file=sys.stderr)
        return []

    jogos = []
    for nome_busca, nome_exibicao in COMPETICOES_COPAS.items():
        liga = buscar_id_liga(nome_busca, headers)
        if not liga:
            print(f"Aviso: não encontrei a competição '{nome_busca}' nesta temporada (pode ainda não ter começado).")
            continue
        liga_id, temporada = liga

        dados = chamar_api(
            f"{API_FOOTBALL_BASE}/fixtures?league={liga_id}&season={temporada}&team={time_id}",
            headers,
        )
        if dados.get("errors"):
            print(f"Aviso: erro da API-Football nos jogos de '{nome_busca}': {dados['errors']}", file=sys.stderr)

        for partida in dados.get("response") or []:
            try:
                times = partida.get("teams") or {}
                mandante = (times.get("home") or {}).get("name")
                visitante = (times.get("away") or {}).get("name")
                fixture = partida.get("fixture") or {}
                status_curto = (fixture.get("status") or {}).get("short")
                data_iso = fixture.get("date")  # ex: 2026-04-07T21:00:00+00:00
                venue = fixture.get("venue") or {}

                if not mandante or not visitante:
                    continue

                jogo = {
                    "competicao": nome_exibicao,
                    "mandante": normalizar_nome(mandante, apelidos),
                    "visitante": normalizar_nome(visitante, apelidos),
                    "chave_unica": f"{nome_exibicao}-{(partida.get('league') or {}).get('round')}-{mandante}-{visitante}",
                    "local": venue.get("name") or "",
                    "status": STATUS_API_FOOTBALL.get(status_curto, status_curto or ""),
                    "data_confirmada": status_curto != "TBD" and data_iso is not None,
                }
                if data_iso:
                    jogo["utc_datetime"] = (
                        data_iso.replace("+00:00", "Z") if data_iso.endswith("+00:00") else data_iso
                    )
                if status_curto in ("FT", "AET", "PEN"):
                    gols = partida.get("goals") or {}
                    if gols.get("home") is not None:
                        jogo["gols_mandante"] = gols["home"]
                        jogo["gols_visitante"] = gols["away"]

                jogos.append(jogo)
            except Exception as e:
                # Um jogo com formato inesperado não pode derrubar os outros.
                print(f"Aviso: ignorando um jogo de '{nome_busca}' com dado inesperado ({e}).", file=sys.stderr)
                continue

    return jogos

# ---------------------------------------------------------------------
# Jogos manuais (jogos_manuais.json) — pra você adicionar à mão jogos que
# a busca automática não pega (ex: Copa do Brasil/Libertadores, já que a
# API-Football suspende a conta quando usada a partir do GitHub Actions,
# porque o IP muda a cada execução e o sistema antifraude dela interpreta
# isso como a chave sendo compartilhada/vazada).
#
# Esse arquivo NUNCA é sobrescrito pelo robô — ele só lê e soma ao que
# já buscou sozinho. É seguro editar quando quiser.
# ---------------------------------------------------------------------

ARQUIVO_MANUAL = "jogos_manuais.json"

def carregar_jogos_manuais(apelidos: dict) -> list:
    try:
        with open(ARQUIVO_MANUAL, encoding="utf-8") as f:
            bruto = json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as e:
        print(f"Aviso: {ARQUIVO_MANUAL} tem um erro de formatação e foi ignorado ({e}).", file=sys.stderr)
        return []

    jogos = []
    for item in bruto:
        if "_como_usar" in item:
            continue
        jogo = dict(item)  # cópia, não mexe no arquivo original
        jogo["mandante"] = normalizar_nome(jogo.get("mandante", ""), apelidos)
        jogo["visitante"] = normalizar_nome(jogo.get("visitante", ""), apelidos)
        jogo.setdefault(
            "chave_unica",
            f"manual-{jogo.get('competicao')}-{jogo.get('mandante')}-{jogo.get('visitante')}",
        )
        jogos.append(jogo)
    return jogos

# ---------------------------------------------------------------------

def main():
    apelidos = carregar_apelidos()

    jogos = []
    jogos += buscar_brasileirao(os.environ.get("FOOTBALL_DATA_API_KEY"), apelidos)

    try:
        jogos += buscar_copas(os.environ.get("API_FOOTBALL_KEY"), apelidos)
    except Exception as e:
        # Se a busca de copas falhar de vez, o Brasileirão não pode ser
        # perdido junto — melhor salvar só ele do que travar tudo.
        print(f"Aviso: falha ao buscar Copa do Brasil/Libertadores/Sul-Americana: {e}", file=sys.stderr)

    jogos += carregar_jogos_manuais(apelidos)

    jogos.sort(key=lambda j: j.get("utc_datetime") or "9999")

    with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as f:
        json.dump(jogos, f, ensure_ascii=False, indent=2)

    print(f"{len(jogos)} jogo(s) do {NOME_TIME} salvos em {ARQUIVO_SAIDA}.")

if __name__ == "__main__":
    main()

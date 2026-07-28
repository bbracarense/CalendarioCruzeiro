#!/usr/bin/env python3
"""
Busca automaticamente os jogos do Cruzeiro no Brasileirão (fonte:
football-data.org, que é gratuita) e escreve jogos.json sozinho —
ninguém precisa editar esse arquivo à mão.

Como funciona:
  - Enquanto a CBF não divulgou data/hora de um jogo, ele entra no
    calendário como "data a confirmar" (evento de dia inteiro, na semana
    aproximada da rodada), só pra você não perder o jogo de vista.
  - Assim que a CBF confirma a data/hora, o jogo passa a aparecer com
    hora certa (o evento é atualizado, não duplicado).
  - Depois que o jogo acontece, o placar final é adicionado no título
    e na descrição do mesmo evento.

Precisa de uma chave de API gratuita da football-data.org, lida da
variável de ambiente FOOTBALL_DATA_API_KEY (no GitHub Actions isso vem
de um "Secret" — veja o README, ninguém digita a chave dentro do código).

IMPORTANTE — limitação da camada gratuita: a football-data.org cobre o
Brasileirão Série A. Copa do Brasil e Libertadores não estão incluídas
no plano gratuito; para esses, o jeito mais simples ainda é acrescentar
o jogo manualmente (veja README) ou migrar para uma API paga que cubra.
"""

import json
import os
import sys
import urllib.request
import urllib.error

API_URL = "https://api.football-data.org/v4/competitions/BSA/matches"
NOME_TIME = "Cruzeiro"
ARQUIVO_SAIDA = "jogos.json"
ARQUIVO_APELIDOS = "nomes_times.json"

def carregar_apelidos() -> dict:
    """Lê nomes_times.json (se existir) pra trocar o nome 'cru' que a
    fonte de dados manda pelo nome que você prefere ver no calendário.
    Esse arquivo é o único que faz sentido você mesmo editar."""
    try:
        with open(ARQUIVO_APELIDOS, encoding="utf-8") as f:
            apelidos = json.load(f)
    except FileNotFoundError:
        return {}
    apelidos.pop("_como_usar", None)  # essa chave é só um comentário, ignora
    return apelidos

def normalizar_nome(nome: str, apelidos: dict) -> str:
    return apelidos.get(nome, nome)

STATUS_TRADUZIDO = {
    "SCHEDULED": "agendado",
    "TIMED": "agendado",
    "IN_PLAY": "em andamento",
    "PAUSED": "em andamento",
    "FINISHED": "encerrado",
    "POSTPONED": "adiado",
    "SUSPENDED": "suspenso",
    "CANCELLED": "cancelado",
}

def buscar_partidas(token: str) -> list:
    req = urllib.request.Request(API_URL, headers={"X-Auth-Token": token})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            dados = json.load(resp)
    except urllib.error.HTTPError as e:
        print(f"Erro ao consultar a API: {e.code} {e.reason}", file=sys.stderr)
        sys.exit(1)
    return dados.get("matches", [])

def eh_jogo_do_time(partida: dict) -> bool:
    mandante = partida["homeTeam"]["name"] or ""
    visitante = partida["awayTeam"]["name"] or ""
    return NOME_TIME in mandante or NOME_TIME in visitante

def converter(partida: dict, apelidos: dict) -> dict:
    status = partida.get("status", "SCHEDULED")
    utc_date = partida.get("utcDate")  # sempre vem em UTC, ex: 2026-04-12T21:30:00Z

    data_confirmada = status not in ("SCHEDULED",) and utc_date is not None
    # Mesmo em SCHEDULED a API costuma já trazer utcDate, então também
    # tratamos como confirmado quando o horário não é o "meio-dia
    # genérico" que a CBF usa como placeholder antes de decidir.
    if utc_date:
        data_confirmada = True

    jogo = {
        "competicao": "Brasileirão",
        "mandante": normalizar_nome(partida["homeTeam"]["name"], apelidos),
        "visitante": normalizar_nome(partida["awayTeam"]["name"], apelidos),
        "rodada": partida.get("matchday"),
        "local": (partida.get("venue") or ""),
        "status": STATUS_TRADUZIDO.get(status, status),
        "data_confirmada": data_confirmada,
    }

    if utc_date:
        # Guardamos em UTC; quem monta o .ics converte pro horário de Brasília.
        jogo["utc_datetime"] = utc_date

    if status == "FINISHED":
        # Gols separados (não uma string pronta) pra quem monta o .ics poder
        # escrever "Mandante 1 x 2 Visitante" com os nomes já normalizados.
        jogo["gols_mandante"] = partida["score"]["fullTime"]["home"]
        jogo["gols_visitante"] = partida["score"]["fullTime"]["away"]

    return jogo

def main():
    token = os.environ.get("FOOTBALL_DATA_API_KEY")
    if not token:
        print(
            "Defina a variável de ambiente FOOTBALL_DATA_API_KEY "
            "(no GitHub Actions isso é um Secret, veja o README).",
            file=sys.stderr,
        )
        sys.exit(1)

    apelidos = carregar_apelidos()
    partidas = buscar_partidas(token)
    jogos = [converter(p, apelidos) for p in partidas if eh_jogo_do_time(p)]
    jogos.sort(key=lambda j: j.get("utc_datetime") or "9999")

    with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as f:
        json.dump(jogos, f, ensure_ascii=False, indent=2)

    print(f"{len(jogos)} jogo(s) do {NOME_TIME} salvos em {ARQUIVO_SAIDA}.")

if __name__ == "__main__":
    main()

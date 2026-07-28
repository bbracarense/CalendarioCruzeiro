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

def converter(partida: dict) -> dict:
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
        "mandante": partida["homeTeam"]["name"],
        "visitante": partida["awayTeam"]["name"],
        "rodada": partida.get("matchday"),
        "local": (partida.get("venue") or ""),
        "status": STATUS_TRADUZIDO.get(status, status),
        "data_confirmada": data_confirmada,
    }

    if utc_date:
        # Guardamos em UTC; quem monta o .ics converte pro horário de Brasília.
        jogo["utc_datetime"] = utc_date

    if status == "FINISHED":
        gols_casa = partida["score"]["fullTime"]["home"]
        gols_fora = partida["score"]["fullTime"]["away"]
        jogo["placar"] = f"{gols_casa} x {gols_fora}"

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

    partidas = buscar_partidas(token)
    jogos = [converter(p) for p in partidas if eh_jogo_do_time(p)]
    jogos.sort(key=lambda j: j.get("utc_datetime") or "9999")

    with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as f:
        json.dump(jogos, f, ensure_ascii=False, indent=2)

    print(f"{len(jogos)} jogo(s) do {NOME_TIME} salvos em {ARQUIVO_SAIDA}.")

if __name__ == "__main__":
    main()

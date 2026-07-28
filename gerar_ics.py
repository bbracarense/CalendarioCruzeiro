#!/usr/bin/env python3
"""
Gera cruzeiro.ics a partir de jogos.json (que agora é escrito
automaticamente pelo buscar_jogos.py — você não precisa mexer aqui).
"""

import json
import uuid
from datetime import datetime, timedelta, timezone

ARQUIVO_JOGOS = "jogos.json"
ARQUIVO_SAIDA = "cruzeiro.ics"
DURACAO_JOGO_MIN = 120
NOME_CALENDARIO = "Jogos do Cruzeiro"
FUSO_BRASILIA = timezone(timedelta(hours=-3))

def escapar(texto: str) -> str:
    return (
        str(texto)
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )

def dobra_linha(linha: str) -> str:
    if len(linha.encode("utf-8")) <= 75:
        return linha
    partes, atual = [], ""
    for ch in linha:
        if len((atual + ch).encode("utf-8")) > 74:
            partes.append(atual)
            atual = " " + ch
        else:
            atual += ch
    partes.append(atual)
    return "\r\n".join(partes)

def montar_titulo(jogo: dict) -> str:
    base = f"{jogo['mandante']} x {jogo['visitante']} ({jogo['competicao']})"
    if jogo.get("placar"):
        base = f"{base} — {jogo['placar']}"
    elif not jogo.get("data_confirmada", True):
        base = f"{base} [data a confirmar]"
    return base

def main():
    with open(ARQUIVO_JOGOS, encoding="utf-8") as f:
        jogos = json.load(f)

    agora = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    linhas = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Cruzeiro Fans//Calendario de Jogos//PT",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{escapar(NOME_CALENDARIO)}",
        "X-WR-TIMEZONE:America/Sao_Paulo",
        "REFRESH-INTERVAL;VALUE=DURATION:PT6H",
        "X-PUBLISHED-TTL:PT6H",
    ]

    for jogo in jogos:
        chave = f"{jogo.get('rodada')}-{jogo['mandante']}-{jogo['visitante']}"
        uid = uuid.uuid5(uuid.NAMESPACE_URL, chave)
        titulo = montar_titulo(jogo)
        descricao_partes = [jogo["competicao"], f"Status: {jogo.get('status', '')}"]
        if jogo.get("placar"):
            descricao_partes.append(f"Placar final: {jogo['placar']}")
        descricao = " | ".join(descricao_partes)

        linhas.append("BEGIN:VEVENT")
        linhas.append(f"UID:{uid}@cruzeiro-fans-calendar")
        linhas.append(f"DTSTAMP:{agora}")

        if jogo.get("data_confirmada") and jogo.get("utc_datetime"):
            inicio_utc = datetime.strptime(
                jogo["utc_datetime"], "%Y-%m-%dT%H:%M:%SZ"
            ).replace(tzinfo=timezone.utc)
            inicio_local = inicio_utc.astimezone(FUSO_BRASILIA)
            fim_local = inicio_local + timedelta(minutes=DURACAO_JOGO_MIN)
            linhas.append(
                f"DTSTART;TZID=America/Sao_Paulo:{inicio_local.strftime('%Y%m%dT%H%M%S')}"
            )
            linhas.append(
                f"DTEND;TZID=America/Sao_Paulo:{fim_local.strftime('%Y%m%dT%H%M%S')}"
            )
        else:
            dia_ref = jogo.get("utc_datetime", "")[:10] or datetime.now().strftime("%Y-%m-%d")
            data_evento = dia_ref.replace("-", "")
            linhas.append(f"DTSTART;VALUE=DATE:{data_evento}")
            linhas.append(f"DTEND;VALUE=DATE:{data_evento}")

        linhas.append(dobra_linha(f"SUMMARY:{escapar(titulo)}"))
        linhas.append(dobra_linha(f"LOCATION:{escapar(jogo.get('local', ''))}"))
        linhas.append(dobra_linha(f"DESCRIPTION:{escapar(descricao)}"))
        linhas.append("END:VEVENT")

    linhas.append("END:VCALENDAR")

    with open(ARQUIVO_SAIDA, "w", encoding="utf-8", newline="") as f:
        f.write("\r\n".join(linhas) + "\r\n")

    print(f"Gerado {ARQUIVO_SAIDA} com {len(jogos)} jogo(s).")

if __name__ == "__main__":
    main()

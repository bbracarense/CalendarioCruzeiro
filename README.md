# Calendário do Cruzeiro — 100% automático (guia sem jargão)

Você **não precisa saber programar** pra usar isso. Sua única tarefa é
seguir os passos abaixo **uma única vez** (leva uns 15-20 minutos). Depois
disso, um "robô" cuida de tudo sozinho, pra sempre: ele busca os jogos,
descobre datas confirmadas, e adiciona os placares depois dos jogos.

## O que é cada arquivo (só pra você entender, sem decorar nada)

| Arquivo | O que é | Você mexe nisso? |
|---|---|---|
| `jogos.json` | A lista de jogos, escrita como texto | **Não** — o robô escreve sozinho |
| `nomes_times.json` | "Apelidos" dos times (nome bonito de cada time) | **Sim, se quiser** — é um dos arquivos pensados pra você mexer |
| `jogos_manuais.json` | Jogos de Copa do Brasil/Libertadores adicionados à mão | **Sim** — veja o Passo 4.5 |
| `buscar_jogos.py` | O "robô" que busca os jogos numa fonte oficial de dados | Não |
| `gerar_ics.py` | O "robô" que transforma a lista em calendário | Não |
| `cruzeiro.ics` | O calendário final, que seus amigos vão assinar | Não |
| `.github/workflows/atualizar.yml` | A instrução de **quando** o robô deve rodar (todo dia) | Não |

Ou seja: depois de configurado, **nenhum arquivo desses precisa ser aberto
por você de novo**. Quem mexe é o robô.

## Passo 1 — Criar uma conta no GitHub (se ainda não tiver)

O GitHub é só um "armário na nuvem" onde os arquivos ficam guardados e de
onde o link do calendário vai sair.

1. Acesse **github.com** e clique em **Sign up**.
2. Crie a conta com seu e-mail (é grátis).

## Passo 2 — Criar o "repositório" (a pasta do projeto)

1. Depois de logado, clique no **+** no canto superior direito → **New
   repository**.
2. Dê um nome, por exemplo `cruzeiro-calendario`.
3. Marque a opção **Public** (precisa ser público pra o link do calendário
   funcionar de graça).
4. Clique em **Create repository**.

## Passo 3 — Subir os arquivos (arrastar e soltar, sem terminal)

1. Na página do repositório recém-criado, clique em **Add file → Upload
   files**.
2. Arraste **todos** os arquivos que eu gerei para você (inclusive a
   pasta `.github` inteira, com o arquivo `atualizar.yml` dentro).
   > Dica: se o site não deixar arrastar a pasta `.github` direto, crie
   > o caminho manualmente: clique em "Add file → Create new file",
   > digite o nome como `.github/workflows/atualizar.yml` (as barras
   > `/` criam as pastas sozinhas) e cole o conteúdo do arquivo lá dentro.
3. Clique em **Commit changes** (é só o botão de "salvar").

## Passo 4 — Pegar sua chave gratuita da fonte de dados dos jogos

Pra buscar os jogos automaticamente, usamos um serviço gratuito chamado
**football-data.org**. Ele te dá uma "senha" (chave) só sua, pra provar
que é você usando.

1. Acesse **football-data.org/client/register**.
2. Preencha seu e-mail e crie a conta (plano **Free** já serve).
3. Depois de confirmar o e-mail, copie a chave (um código de letras e
   números) que aparece na sua área de cliente.

## Passo 4.5 (atualizado) — Copa do Brasil, Libertadores/Sul-Americana e estádio

**Atualização importante:** a princípio a ideia era buscar Copa do Brasil e
Libertadores automaticamente numa segunda API gratuita (API-Football).
Só que descobrimos um problema sério: como o robô roda no GitHub Actions,
cada execução sai de um endereço de internet diferente — e o sistema
antifraude dessa API interpreta isso como "essa chave está sendo
compartilhada/vazada" e **suspende a conta automaticamente a cada
execução**. Não é algo que dá pra contornar de forma confiável de graça,
então a estratégia mudou.

**Como ficou, então:**
- O Brasileirão continua 100% automático, sem mudança nenhuma.
- Copa do Brasil, Libertadores e Sul-Americana passam a ser preenchidas
  por você, à mão, num arquivo separado chamado **`jogos_manuais.json`**.
  Isso é bem mais leve do que parece: esses jogos do Cruzeiro são poucos
  por temporada (bem menos que os 38 jogos do Brasileirão), e você só
  precisa adicionar um bloco quando a CBF/CONMEBOL sortear ou marcar
  a próxima fase.
- O robô **nunca sobrescreve** esse arquivo — ele só lê o que tiver lá e
  soma aos jogos que busca sozinho. Pode editar quando quiser, o robô
  não vai apagar.
- O código ainda sabe conversar com a API-Football, caso um dia você
  queira rodar a busca de outro lugar que não tenha IP mudando toda
  hora (seu próprio computador, por exemplo). Só não recomendo deixar a
  chave configurada como Secret do GitHub Actions, porque ela vai
  continuar sendo suspensa.

### Como adicionar um jogo em `jogos_manuais.json`

Abra o arquivo (dá pra editar direto pelo site do GitHub, clicando no
lápis ✏️) e copie o bloco de exemplo que já está lá, ajustando os dados:

```json
{
  "competicao": "Copa do Brasil",
  "mandante": "CRUZEIRO",
  "visitante": "Ferroviária",
  "local": "Mineirão",
  "status": "agendado",
  "data_confirmada": true,
  "utc_datetime": "2026-08-13T21:30:00Z"
}
```

Detalhes de cada campo:
- **`data_confirmada`**: `true` se já tem data marcada, `false` se ainda
  não (aí não precisa nem colocar o `utc_datetime`, o jogo entra como
  "[data a confirmar]").
- **`utc_datetime`**: é a data/hora em UTC, ou seja, **hora de Brasília +
  3 horas**. Exemplo: jogo às 21h30 de Brasília vira `21:30 + 3h =
  00:30 do dia seguinte`, em UTC.
- **`status`**: `"agendado"` antes do jogo, `"encerrado"` depois.
- Depois que o jogo acabar, volte nesse mesmo bloco e acrescente
  `"gols_mandante": 2, "gols_visitante": 1` (por exemplo) — o placar
  aparece no calendário exatamente como nos jogos automáticos.
- Se tiver mais de um jogo (ida e volta, por exemplo), é só copiar o
  bloco de novo dentro dos colchetes `[ ]`, separado por vírgula.

Depois de editar e salvar (**Commit changes**), não precisa nem esperar
o robô rodar sozinho — dá pra forçar rodando **Run workflow** de novo, e
o jogo já aparece no calendário.



## Passo 5 — Guardar essa chave como um "segredo" no GitHub

Isso é importante: a chave **não** vai dentro do código, ela fica guardada
separada, num cofre do próprio GitHub.

1. No repositório, vá em **Settings → Secrets and variables → Actions**.
2. Clique em **New repository secret**.
3. Em **Name**, escreva exatamente: `FOOTBALL_DATA_API_KEY`
4. Em **Secret**, cole a chave que você copiou no Passo 4.
5. Clique em **Add secret**.

## Passo 6 — Ligar o robô

1. Vá na aba **Actions**, no topo do repositório.
2. Se aparecer um aviso pra habilitar workflows, clique em habilitar.
3. Você vai ver "Atualizar calendário do Cruzeiro" na lista. Clique nela
   e depois em **Run workflow** pra rodar pela primeira vez, na hora,
   sem esperar o horário automático.
4. Espere uns 30 segundos e atualize a página — deve aparecer um ✅
   verde. Isso já significa que `jogos.json` e `cruzeiro.ics` foram
   gerados e salvos sozinhos.

Pronto. A partir de agora, todo dia às 9h (horário de Brasília) o robô
roda sozinho, sem você precisar fazer nada.

## Passo 7 — Pegar o link e mandar pros amigos

1. No repositório, clique no arquivo `cruzeiro.ics`.
2. Clique no botão **Raw** (canto superior direito da visualização do
   arquivo) — isso abre a URL "crua" do arquivo.
3. Copie essa URL. Vai ser parecida com:
   `https://raw.githubusercontent.com/SEU_USUARIO/cruzeiro-calendario/main/cruzeiro.ics`
4. Pra virar link de assinatura "oficial", troque só o começo:
   `https://` → `webcal://`

Mande o link `webcal://...` no grupo dos amigos.

### Como cada amigo assina

**iPhone (Apple Calendar):** tocar no link `webcal://...` já abre a tela
de "Adicionar Assinatura de Calendário" sozinho. Caminho manual:
**Ajustes → Calendário → Contas → Adicionar Conta → Outra → Adicionar
Calendário Assinado** → colar a URL.

**Android (Google Calendar):** no navegador, ir em **calendar.google.com
→ Outros calendários → "+" → Através do URL** → colar a URL `https://...`
→ **Adicionar calendário**. Depois disso ele aparece sozinho no app do
Google Calendar do celular.

## O que o robô faz automaticamente a partir de agora

- **Busca Brasileirão, Copa do Brasil e Libertadores/Sul-Americana** —
  cada um com sua própria fonte de dados, combinados no mesmo calendário.
- **Jogo sem data definida ainda:** entra no calendário como um aviso de
  dia inteiro, marcado "[data a confirmar]", só pra ninguém esquecer que
  o jogo existe.
- **Data e horário confirmados:** o robô atualiza o mesmo evento com a
  hora certa (não cria um evento duplicado).
- **Jogo terminou:** o robô adiciona o placar final no título e na
  descrição daquele evento (ex: "Internacional 1 x 2 CRUZEIRO").
- **Estádio:** quando a fonte de dados já sabe qual vai ser, ele aparece
  no campo de local do evento.
- **Nomes dos times:** seguem o que estiver definido em
  `nomes_times.json` (ex: sempre "CRUZEIRO" em maiúsculas).

## Limitação importante (seja honesto saber disso)

Essas duas APIs gratuitas cobrem bem o Brasileirão, Copa do Brasil e
Libertadores/Sul-Americana. Coisas que ainda ficam de fora do automático,
pra você saber:
- **Amistosos e jogos de pré-temporada** — geralmente não entram nas
  competições oficiais rastreadas.
- **Estadual (Mineiro)** — não é rastreado por nenhuma das duas fontes
  configuradas hoje. Se quiser incluir, dá pra adaptar o script.
- O **estádio** só aparece quando a própria fonte de dados já sabe qual
  vai ser (às vezes só é confirmado perto da data do jogo).

Se quiser cobrir alguma dessas lacunas, me chama que eu adapto o
`buscar_jogos.py`.

## Se algo der errado

Na aba **Actions**, clique na última execução — se tiver um ❌ vermelho,
clique em cima pra ver a mensagem de erro em texto (geralmente é chave
da API errada ou expirada). Pode colar a mensagem de erro aqui na
conversa que eu te ajudo a resolver.

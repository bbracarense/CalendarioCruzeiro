# Calendário do Cruzeiro — 100% automático (guia sem jargão)

Você **não precisa saber programar** pra usar isso. Sua única tarefa é
seguir os passos abaixo **uma única vez** (leva uns 15-20 minutos). Depois
disso, um "robô" cuida de tudo sozinho, pra sempre: ele busca os jogos,
descobre datas confirmadas, e adiciona os placares depois dos jogos.

## O que é cada arquivo (só pra você entender, sem decorar nada)

| Arquivo | O que é | Você mexe nisso? |
|---|---|---|
| `jogos.json` | A lista de jogos, escrita como texto | **Não** — o robô escreve sozinho |
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

- **Jogo sem data definida ainda:** entra no calendário como um aviso de
  dia inteiro, marcado "[data a confirmar]", só pra ninguém esquecer que
  o jogo existe.
- **CBF confirma data e horário:** no dia seguinte, o robô já atualiza o
  mesmo evento com a hora certa (não cria um evento duplicado).
- **Jogo terminou:** no dia seguinte, o robô adiciona o placar final no
  título e na descrição daquele evento (ex: "Cruzeiro x Grêmio — 2 x 1").

## Limitação importante (seja honesto saber disso)

A fonte de dados gratuita (football-data.org) cobre bem o **Brasileirão
Série A**. **Copa do Brasil e Libertadores não entram no plano
gratuito** dela. Duas opções, se quiser esses jogos também:
- Adicionar esses jogos manualmente e ocasionalmente no `jogos.json`
  (aí sim precisaria mexer no arquivo só pra esses casos específicos); ou
- Trocar a fonte de dados por uma API paga que cubra essas competições —
  me chama que eu adapto o `buscar_jogos.py` pra isso quando quiser.

## Se algo der errado

Na aba **Actions**, clique na última execução — se tiver um ❌ vermelho,
clique em cima pra ver a mensagem de erro em texto (geralmente é chave
da API errada ou expirada). Pode colar a mensagem de erro aqui na
conversa que eu te ajudo a resolver.

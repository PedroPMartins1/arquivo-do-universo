# Autenticação, sessões e proteção CSRF

Este documento descreve os controlos de autenticação da aplicação, conforme a decisão D-033.
Protegem contra tentativas automatizadas de acesso, falsificação de pedidos entre sites, abuso de
`X-Forwarded-For` e exposição acidental de dados de autenticação.

## Modelo de ameaça e estado anterior

Os principais riscos são a adivinhação repetida de palavras-passe, a enumeração de contas, pedidos
de alteração de estado iniciados por outro site, a falsificação do IP do cliente através de cabeçalhos
encaminhados e a reutilização de sessões após nova autenticação. A base de dados, o processo da
aplicação, os proxies explicitamente confiáveis e o canal HTTPS de produção fazem parte da fronteira
de confiança.

Antes de D-033, não existiam limites partilhados de tentativas nem validação da origem dos pedidos
mutáveis. A política CORS era ampla e os erros de validação podiam incluir os dados de entrada.
As sessões já usavam um cookie `HttpOnly`, `SameSite=Lax` e validade de 30 dias; esta decisão
mantém esses atributos, garante `Secure` apenas em produção e acrescenta rotação explícita e
`no-store`, sem alterar o prazo da sessão.

## Limites de tentativas

Os limites são janelas deslizantes, partilhadas por processos através da tabela PostgreSQL
`auth_throttle`. Cada evento guarda apenas o âmbito, um hash HMAC-SHA256 da chave e a hora UTC
fornecida pela aplicação. Não são guardados emails, IPs nem identificadores de utilizador na tabela.

| Âmbito | Valor limitado | Máximo | Janela | Armazenamento | Chave e pseudonimização | Retenção |
|---|---|---:|---:|---|---|---|
| `login_ip` | Falhas de autenticação por IP | 20 | 15 min | PostgreSQL, tabela `auth_throttle` | HMAC-SHA256 da chave configurada sobre `login_ip:<IP>` | Limpeza oportunística de linhas com mais de 2 h |
| `login_account_ip` | Falhas por email normalizado e IP | 5 | 15 min | PostgreSQL, tabela `auth_throttle` | HMAC-SHA256 sobre `login_account_ip:<email normalizado>\|<IP>` | Limpeza oportunística de linhas com mais de 2 h |
| `login_account` | Falhas por email normalizado, incluindo emails inexistentes | 50 | 60 min | PostgreSQL, tabela `auth_throttle` | HMAC-SHA256 sobre `login_account:<email normalizado>` | Limpeza oportunística de linhas com mais de 2 h |
| `register_ip` | Pedidos de registo que chegam ao handler, incluindo duplicados | 10 | 60 min | PostgreSQL, tabela `auth_throttle` | HMAC-SHA256 sobre `register_ip:<IP>` | Limpeza oportunística de linhas com mais de 2 h |

O HMAC usa `ARQUIVO_AUTH_RATE_LIMIT_KEY` em produção. Em desenvolvimento e testes, se a variável
estiver ausente, usa-se uma constante fixa. A configuração de produção exige uma chave própria
e recusa essa constante. As operações sobre cada chave são serializadas com advisory locks transacionais,
para que pedidos concorrentes e vários workers observem o mesmo limite.

O limite global por email (`login_account`) é intencional: um atacante distribuído pode bloquear
temporariamente novas tentativas para esse email, mesmo a partir de outro IP. É um compromisso
deliberado contra ataques distribuídos; os limites por IP e por email/IP, isoladamente, não afetam
um acesso feito a partir de outro endereço.

### Política de espera

Quando um limite é atingido, a API responde `429` com `Retry-After`. O prazo corresponde ao tempo
até o evento relevante mais antigo sair da janela, arredondado para cima e com mínimo de um segundo.
O login verifica todos os limites antes de testar a palavra-passe, pelo que até uma palavra-passe
correta recebe `429` durante esse período. As falhas de login recebem sempre a mesma resposta
`401`, exista ou não a conta. Um login bem-sucedido limpa as falhas da combinação email/IP.

Não há backoff exponencial nem bloqueio permanente: a recuperação acontece quando os eventos saem
da respetiva janela. Cada tentativa de registo que chega ao handler é contabilizada, quer termine
com sucesso, quer com conflito por email já usado.

## Proteção CSRF e CORS

Os pedidos diferentes de `GET`, `HEAD` e `OPTIONS`, em qualquer rota, seguem esta ordem:

1. Se existir `Origin`, só é aceite uma correspondência exata com `ARQUIVO_CORS_ORIGINS`.
   `Origin: null` é sempre recusado.
2. Na ausência de `Origin`, `Sec-Fetch-Site` só pode ser `same-origin` ou `none`.
3. Na ausência dos anteriores, a origem de `Referer` tem de pertencer à mesma lista.
4. Se nenhum destes cabeçalhos existir, o pedido é permitido para suportar clientes não-browser.

Uma origem recusada recebe `403` com `{"detail":"origem do pedido não autorizada"}`. Os browsers
enviam `Origin` em pedidos cross-origin de escrita. Mantém-se `SameSite=Lax`; não é usado um token
CSRF. A lista de origens configurada é partilhada por CSRF e CORS. O CORS permite credenciais,
métodos `GET`, `POST`, `PUT` e `DELETE`, e apenas o cabeçalho `Content-Type`.

## Cookies e sessões

O cookie `arquivo_sessao` tem `HttpOnly`, `SameSite=Lax`, `Path=/` e validade absoluta de 30 dias.
O atributo `Secure` só é ativado em produção, onde todo o acesso deve usar HTTPS. Ao iniciar sessão
ou registar uma conta com um cookie de sessão anterior, a sessão anterior é revogada antes de abrir
uma nova. No login, as sessões expiradas dessa conta são removidas. Logout e eliminação da conta
apagam o cookie com os mesmos atributos; `GET /me` e os endpoints de autenticação não são guardados
em cache.

Os erros `422` de validação incluem apenas `type`, `loc` e `msg`; nunca ecoam `input`, `ctx` ou `url`.

## IP do cliente e proxies confiáveis

Sem proxies configurados, o código usa apenas `request.client.host` e ignora `X-Forwarded-For`.
Quando `ARQUIVO_TRUSTED_PROXIES` contém endereços IP ou redes CIDR, a aplicação instala o
`ProxyHeadersMiddleware` do Uvicorn, que resolve o cliente a partir da cadeia encaminhada confiando
apenas nos proxies configurados.

O Uvicorn confia, por omissão, em `127.0.0.1` para cabeçalhos de proxy. Em produção, desativa essa
confiança implícita com `--no-proxy-headers` (ou com `--forwarded-allow-ips ""`) e define
`ARQUIVO_TRUSTED_PROXIES` com o endereço ou CIDR do proxy reverso real. O proxy tem de substituir
ou acrescentar corretamente os cabeçalhos encaminhados; não confies em valores enviados diretamente
por clientes.

## Configuração de produção

A partir de `backend/`, o comando `uv run alembic upgrade head` aplica as migrações de autenticação
e de pré-geração. Uma base que já tenha recebido uma delas pode seguir o mesmo procedimento.

Define as variáveis através do gestor de segredos e da configuração de deployment, nunca no código
ou em logs:

```text
ARQUIVO_ENVIRONMENT=production
ARQUIVO_CORS_ORIGINS=["https://app.example"]
ARQUIVO_TRUSTED_PROXIES=["10.0.0.10/32"]
ARQUIVO_AUTH_RATE_LIMIT_KEY=<segredo aleatório com pelo menos 32 caracteres>
```

As origens têm de ser origens explícitas `http://host[:port]` ou `https://host[:port]`, sem caminho,
query, fragmento, wildcard ou barra final. Em produção, a lista não pode estar vazia e todas as
origens têm de usar HTTPS. Endereços dos proxies têm de ser IPs ou redes CIDR válidas. Uma
configuração que confie em toda a Internet (`/0`) impede a aplicação de arrancar. O Uvicorn deve ser executado com
`--no-proxy-headers`, por exemplo:

```text
uvicorn arquivo.main:app --no-proxy-headers
```

Termina TLS no proxy de confiança e protege também o tráfego entre proxy e aplicação. A configuração
de CORS deve conter apenas os frontends autorizados.

## Riscos residuais

- O registo continua a devolver `409` quando o email já existe, o que permite alguma enumeração.
  A verificação de email e a recuperação de palavra-passe permanecem abertas em L-016.
- O limite global por email pode ser usado para negação de serviço temporária contra essa conta.
- `GET /me/reading/today` pode gerar e guardar uma leitura, apesar de ser um `GET`.
- O cookie não usa o prefixo `__Host-`.
- A sessão tem validade absoluta de 30 dias e não tem timeout por inatividade.
- Ainda não existe ação para terminar todas as sessões de uma conta.
- Os limites dependem da disponibilidade e consistência da base de dados PostgreSQL; não há fallback
  local que enfraqueça a proteção quando a base de dados está indisponível.

# Versão de teste online

Esta instalação é uma proposta para validar a aplicação num telemóvel real. Usa um serviço web
Render e PostgreSQL 16 na região Frankfurt. O `render.yaml` seleciona explicitamente os planos
gratuitos. A publicação exige uma conta Render do proprietário e autorização de acesso ao GitHub.

## Limites desta instalação

A base de dados gratuita expira 30 dias após a criação. O serviço web adormece após 15 minutos
sem tráfego e pode demorar cerca de um minuto a responder ao acesso seguinte. A conta Anthropic
tem faturação independente. Confirmar os limites apresentados pelo Render antes de criar os recursos.
Usar dados fictícios nesta primeira validação. Antes de guardar dados que devam ser conservados,
escolher armazenamento duradouro, confirmar os custos e testar cópia de segurança e recuperação.

A pré-geração contínua de leituras exige um worker separado. Nesta instalação, o pedido da
aplicação gera a leitura através do fallback já existente. A chave Anthropic tem de estar configurada
para que as interpretações sejam geradas. Sem essa chave, o cálculo do mapa continua disponível.

## Publicar

1. Iniciar sessão no Render com a conta do proprietário.
2. Abrir https://dashboard.render.com/select-repo?type=blueprint e selecionar
   `PedroPMartins1/arquivo-do-universo`, ramo `main`.
3. Rever os dois recursos e confirmar que os planos apresentados são gratuitos.
4. Introduzir a chave Anthropic no campo `ARQUIVO_ANTHROPIC_API_KEY` do Render.
   Guardar o segredo exclusivamente no fornecedor. O ficheiro de instalação gera automaticamente
   a chave interna de proteção da autenticação e liga a base de dados pela rede privada.
5. Criar a instalação e acompanhar a construção e o arranque até o serviço ficar disponível.
6. Abrir o endereço HTTPS atribuído pelo Render no telemóvel.

O endereço real é atribuído pelo fornecedor. A configuração de origem é derivada desse endereço
durante o arranque. As atualizações automáticas estão desligadas nesta versão de teste.

## O que o arranque faz

A imagem compila a interface e instala as dependências Python com os ficheiros de versões fixadas.
Inclui as efemérides verificadas por SHA-256 e descarrega as localidades GeoNames durante a construção.
O processo de arranque adapta a ligação PostgreSQL ao driver psycopg, valida as definições de produção,
aplica migrações e importa as localidades apenas se a tabela estiver vazia. Um bloqueio PostgreSQL
coordena arranques sobrepostos. Uma falha de migração ou importação impede a abertura do servidor.

A API e a interface usam a mesma origem. A entrada de desenvolvimento `arquivo.main:app` mantém-se
disponível e a entrada da imagem é `arquivo.web:app`. O servidor de instalação corre sem utilizador
root. O PostgreSQL conserva os dados nos reinícios do serviço web, durante a vida da base de dados.
O health check confirma a disponibilidade da API após a inicialização.

## Validar no telemóvel

1. Criar uma conta com dados de teste e introduzir data, hora e local de nascimento fictícios.
2. Confirmar pesquisa de localidades, mapa natal, ampliação e regresso à visualização completa.
3. Confirmar geração de uma leitura, horários de abertura e acesso às reflexões.
4. Guardar uma nota, terminar sessão, voltar a entrar e confirmar que a nota se mantém.
5. Verificar teclado aberto, orientação horizontal e acesso à navegação durante a leitura.
6. Registar problemas e só depois decidir a instalação duradoura.

## Fontes do fornecedor

- https://render.com/docs/blueprint-spec
- https://render.com/docs/docker
- https://render.com/docs/environment-variables
- https://render.com/docs/free
- https://render.com/docs/postgresql-creating-connecting

Documentação consultada em 2026-11-19. O workflow `Validação da instalação` constrói a imagem,
inicializa PostgreSQL e verifica arranque, pesquisa de localidades e reinício. O HTTPS do fornecedor
e a geração real com Anthropic exigem validação depois da publicação.

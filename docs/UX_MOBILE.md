# Experiência móvel — primeira revisão funcional

## Objetivo

Permitir chegar à leitura do dia, ao mapa natal e à escrita pessoal sem orientação externa. Esta revisão parte da dificuldade real de encontrar o Diário durante o primeiro teste de utilização.

## Navegação

Quatro destinos permanentes, com texto e ícone: Hoje, Mapa Natal, Diário e Perfil. As áreas Explorar e Jornada continuam no planeamento do produto; deixam de ocupar a navegação enquanto não têm funcionalidades utilizáveis. O Mapa Natal passa a ter entrada própria. O Perfil reúne os dados de nascimento e a gestão da conta.

## Hoje

A data e o local contextualizam a leitura. A energia do dia recebe destaque, seguida do número de revelações disponíveis e do botão para chegar às leituras. A disponibilidade é calculada a partir dos dados do servidor, sem alterar desbloqueios. Existe um acesso direto ao Diário.

A interpretação vem antes dos detalhes técnicos. A origem astrológica continua consultável em cada revelação. A reflexão associada à leitura mantém o contrato e a gravação existentes. Os erros na leitura permitem tentar novamente.

## Diário e Arquivo

O Diário abre com a nota do dia e apresenta o Arquivo de leituras e reflexões abaixo. A nota usa a mesma data no fuso de residência e os mesmos serviços de gravação já existentes; não cria um armazenamento paralelo.

Uma nota existente deve carregar antes de ser editada. Em caso de erro, o editor fica oculto até a repetição ter sucesso. Uma gravação atualiza o estado visível e o resumo do Arquivo. O botão Guardar não permite texto vazio. A confirmação de gravação é anunciada como estado acessível.

## Mapa Natal

A roda e o resumo de Sol, Lua e Ascendente ficam em primeiro plano. As posições técnicas são expansíveis. A interpretação permanece disponível abaixo, sem alterar cálculos, aspetos ou dados de nascimento.

## Sistema visual

Azul profundo, superfícies com contraste, dourado discreto e títulos serifados. Corpo de texto a 16 px, campos a 16 px e controlos de toque com pelo menos 44 px. A navegação respeita a área segura inferior; a página mantém deslocamento independente. O estilo contempla foco por teclado e redução de movimento.

## Validação e limites

Testes de componentes cobrem a navegação, a gravação e a recuperação de erros do Diário. A revisão visual usa a interface real com respostas fictícias isoladas da conta do utilizador. Esta é uma primeira revisão implementada, não o encerramento do desenho do produto. A exploração interativa dos elementos do mapa, os percursos e os relatórios futuros exigem trabalho próprio.

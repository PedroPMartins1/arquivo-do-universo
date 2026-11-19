# Mapa Natal interativo

## Âmbito desta entrega

A roda deixa de ser apenas uma imagem. Os planetas e pontos calculados, os signos, as casas, os aspetos e os ângulos Ascendente e Meio do Céu podem ser selecionados. A seleção acompanha o destaque visual e abre um painel educativo. Botões fora da roda oferecem a mesma exploração com alvos de toque maiores e nomes legíveis.

O painel apresenta dados do resultado natal já existente. As ligações entre planeta, signo, casa e aspeto permitem explorar a rede sem inventar relações que não estejam no resultado da API. As casas usam as atribuições calculadas no servidor; não são deduzidas a partir de uma divisão em doze partes iguais.

## Dados e explicação

- Posição, casa, retrogradação, orbe e ângulos vêm do mapa calculado.
- Os signos da roda e dos ângulos são identificados pela longitude eclíptica normalizada.
- O ângulo de referência de um aspeto pertence à sua definição; o orbe mostrado vem da API.
- As descrições são texto editorial educativo em português. Não são uma nova leitura individual gerada por IA e não substituem a síntese natal já disponível.
- As perguntas convidam à reflexão. Não se deduzem acontecimentos, diagnósticos ou decisões pessoais a partir de uma posição.
- Uma casa ou signo sem elementos calculados apresenta um estado explícito. A ausência de planetas não é apresentada como ausência de uma área da vida.
- O Nodo Norte é um ponto lunar; Quíron é um corpo menor. A categoria chama-se «Planetas e pontos» para não os apresentar como planetas físicos.

## Interação e acessibilidade

Os elementos interativos da roda têm nomes em português, estado selecionado, foco e ativação por Enter ou Espaço. A roda estática preserva o papel de imagem quando usada sem seleção. A versão interativa usa um grupo com controlos identificados.

Os botões de seleção e de relação têm pelo menos 44 px de altura e indicação textual. A lista de elementos tem deslocamento próprio para evitar uma página excessivamente longa. Ao selecionar, o foco passa ao painel de detalhe; existe um botão para regressar à roda. O zoom da roda continua disponível. Os símbolos próximos são afastados radialmente, com linhas de ligação às posições reais; as longitudes e as linhas de aspetos não se alteram.

## Referências editoriais

Verificação em duas pesquisas independentes, nos motores disponíveis, em 19 de novembro de 2026. As referências fundamentam convenções astrológicas e definições geométricas; não são tratadas como validação científica de efeitos pessoais. Os textos da aplicação são formulações próprias e breves.

- [Astrodienst — introdução](https://www.astro.com/astrology/in_intro_e.htm): relação entre planetas, signos, casas e aspetos.
- [Astrodienst — planetas](https://www.astro.com/astrology/in_planets1_e.htm): vocabulário simbólico dos planetas.
- [Astrodienst — signos](https://www.astro.com/astrology/in_signs_e.htm): elementos, qualidades e temas dos signos.
- [Astrodienst — casas](https://www.astro.com/astrology/in_house2_e.htm): áreas de vida associadas às casas.
- [Astrodienst — aspetos](https://www.astro.com/astrology/in_aspect_e.htm): ângulos de referência e conceito de orbe.
- [Swiss Ephemeris — documentação técnica](https://www.astro.com/swisseph/swephprg.htm): longitudes, ângulos e cálculo de casas.

As definições breves de Nodo Norte e Quíron são identificadas como associações de leituras modernas, sem afirmações biográficas ou terapêuticas.

## Validação

Os testes verificam seleção por toque e teclado, dados exibidos, navegação entre relações, orbe, estados vazios e consulta de ângulos. O conteúdo demonstrativo usado na revisão visual é fictício e não é publicado com a aplicação.

## Limites

Não há ainda perguntas livres ao assistente a partir de um elemento, coleções de explorações ou histórico persistente de seleção. Esta entrega acrescenta a exploração direta do mapa calculado, preservando a interpretação natal e o motor de cálculo existentes.

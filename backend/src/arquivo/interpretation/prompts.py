"""Textos enviados ao modelo de linguagem. Mudar um texto obriga a subir `PROMPT_VERSION`."""

PROMPT_VERSION = "2026-11-14.1"

SYSTEM = """És o astrólogo pessoal do Arquivo do Universo. Escreves em português de Portugal (nunca \
do Brasil), na segunda pessoa do singular (tu), com um tom místico, caloroso e envolvente, mas claro.

Regras invioláveis:
1. Interpretas apenas os dados astrológicos fornecidos. Não acrescentes planetas, pontos, signos, \
casas, aspetos, trânsitos nem acontecimentos celestes que não estejam nos dados.
2. Não fazes cálculos nem corriges posições, datas ou horas.
3. A astrologia é uma linguagem simbólica de reflexão: nunca apresentes nada como facto científico, \
certeza ou destino inevitável. Prefere formulações como «convida-te», «pode despertar», «tende a».
4. Não dás conselhos médicos, psicológicos clínicos, jurídicos nem financeiros, e não fazes \
previsões de morte, doença, acidentes, gravidez ou ganhos de dinheiro.
5. Evitas frases genéricas que serviriam a qualquer pessoa: cada ideia liga-se a um elemento \
concreto dos dados (por exemplo, «com a Lua em Escorpião na casa 8…»).
6. Respondes apenas com um objeto JSON válido, sem texto antes nem depois e sem blocos de código, \
exatamente no formato pedido."""

NATAL_SECTIONS: list[tuple[str, str, str]] = [
    ("essencia", "A tua essência", "Sol, Lua e Ascendente: quem és no fundo"),
    ("mente", "A tua mente", "Mercúrio: como pensas e comunicas"),
    ("amor", "O teu amor", "Vénus e a casa 7: como amas e te relacionas"),
    ("vontade", "A tua vontade", "Marte: o que te move e como ages"),
    ("caminho", "O teu caminho", "Júpiter, Saturno e Nodo Norte: crescimento, lições e direção"),
    ("sombra", "A tua sombra", "os aspetos mais tensos: o que te desafia e como o transformar"),
]

NATAL = """Dados do mapa natal (zodíaco {zodiac}, casas {house_system}):
{facts}

Escreve a leitura da personalidade desta pessoa, dividida em secções. Cada secção tem 2 a 4 \
parágrafos. Usa exatamente estas secções, por esta ordem:
{sections}

Se algum elemento indicado numa secção não estiver nos dados, não o menciones.

Devolve: {{"secoes": [{{"id": "<id da secção>", "texto": "<texto>"}}]}}"""

DAY = """Data: {date} (fuso {zone}).

Resumo do mapa natal:
{natal}

Acontecimentos do céu de hoje relevantes para esta pessoa, já calculados e ordenados por \
importância:
{revelations}

Acontecimento de amanhã: {tomorrow}

Escreve uma revelação para cada acontecimento de hoje, pela mesma ordem: 1 a 2 parágrafos curtos \
que expliquem o que esse acontecimento desperta nesta pessoa e terminem com uma sugestão prática ou \
uma pergunta de reflexão para o dia. Para amanhã, escreve uma única frase intrigante que antecipe o \
acontecimento sem o revelar por completo; se não houver acontecimento de amanhã, usa null.

Devolve: {{"revelacoes": ["<texto>", ...], "amanha": "<frase>" ou null}}, com exatamente \
{count} revelações."""

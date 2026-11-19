/** Texto editorial educativo. Não é uma interpretação individual nem uma previsão.
 * Referências e limites: docs/MAPA_INTERATIVO.md.
 */
export const BODY_GUIDE: Record<string, { theme: string; meaning: string; question: string }> = {
  sun: { theme: 'Identidade e expressão', meaning: 'Simboliza a identidade, a vitalidade e a expressão pessoal.', question: 'Em que situações sentes que estás a ser fiel a ti?' },
  moon: { theme: 'Emoções e segurança', meaning: 'Simboliza as emoções, os hábitos e a procura de segurança.', question: 'O que te ajuda a sentir acolhimento e estabilidade?' },
  mercury: { theme: 'Pensamento e comunicação', meaning: 'Simboliza o pensamento, a aprendizagem e a comunicação.', question: 'Como organizas e partilhas as tuas ideias?' },
  venus: { theme: 'Afetos e valores', meaning: 'Simboliza os afetos, o prazer e aquilo que valorizas.', question: 'O que valorizas nas tuas relações e escolhas?' },
  mars: { theme: 'Ação e iniciativa', meaning: 'Simboliza a iniciativa, o desejo e a forma de agir.', question: 'Como tomas iniciativa e afirmas os teus limites?' },
  jupiter: { theme: 'Expansão e sentido', meaning: 'Simboliza a expansão, a confiança e a procura de sentido.', question: 'Onde procuras aprender e alargar horizontes?' },
  saturn: { theme: 'Estrutura e compromisso', meaning: 'Simboliza os limites, a responsabilidade e a construção paciente.', question: 'Que compromisso queres construir com consistência?' },
  uranus: { theme: 'Mudança e autonomia', meaning: 'Simboliza a mudança, a autonomia e a experimentação.', question: 'Onde sentes necessidade de experimentar outra forma de fazer?' },
  neptune: { theme: 'Imaginação e sensibilidade', meaning: 'Simboliza a imaginação, a sensibilidade e os ideais.', question: 'Como distingues uma inspiração de uma expectativa?' },
  pluto: { theme: 'Transformação e profundidade', meaning: 'Simboliza processos de transformação, poder e renovação.', question: 'Que padrões queres compreender com mais profundidade?' },
  north_node: { theme: 'Direção de aprendizagem', meaning: 'Ponto lunar associado, em leituras modernas, à aprendizagem e ao desenvolvimento.', question: 'Que aprendizagem gostarias de explorar com abertura?' },
  chiron: { theme: 'Vulnerabilidade e integração', meaning: 'Corpo menor associado, em leituras modernas, à vulnerabilidade e à integração.', question: 'Que experiência gostarias de acolher com mais compreensão?' },
}

export const SIGN_GUIDE = [
  { element: 'Fogo', mode: 'Cardinal', meaning: 'Iniciativa, coragem e impulso para começar.' },
  { element: 'Terra', mode: 'Fixo', meaning: 'Estabilidade, continuidade e relação com o concreto.' },
  { element: 'Ar', mode: 'Mutável', meaning: 'Curiosidade, troca de ideias e adaptação.' },
  { element: 'Água', mode: 'Cardinal', meaning: 'Acolhimento, memória e ligação emocional.' },
  { element: 'Fogo', mode: 'Fixo', meaning: 'Expressão, criatividade e afirmação pessoal.' },
  { element: 'Terra', mode: 'Mutável', meaning: 'Discernimento, organização e aperfeiçoamento.' },
  { element: 'Ar', mode: 'Cardinal', meaning: 'Equilíbrio, cooperação e atenção às relações.' },
  { element: 'Água', mode: 'Fixo', meaning: 'Intensidade, profundidade e transformação.' },
  { element: 'Fogo', mode: 'Mutável', meaning: 'Exploração, sentido e abertura de horizontes.' },
  { element: 'Terra', mode: 'Cardinal', meaning: 'Estrutura, responsabilidade e construção.' },
  { element: 'Ar', mode: 'Fixo', meaning: 'Independência, perspetiva coletiva e inovação.' },
  { element: 'Água', mode: 'Mutável', meaning: 'Imaginação, sensibilidade e permeabilidade.' },
] as const

export const HOUSE_GUIDE = [
  'Identidade e apresentação pessoal', 'Recursos e valores', 'Comunicação e aprendizagem quotidiana',
  'Origens, família e lar', 'Criatividade, prazer e expressão', 'Rotinas, trabalho e cuidado quotidiano',
  'Parcerias e relações', 'Recursos partilhados e transformação', 'Estudo, viagens e procura de sentido',
  'Vocação e vida pública', 'Amizades, grupos e projetos coletivos', 'Recolhimento e vida interior',
] as const

export const ASPECT_GUIDE: Record<string, { angle: number; meaning: string }> = {
  conjunction: { angle: 0, meaning: 'Proximidade e combinação de funções; o sentido depende dos elementos envolvidos.' },
  sextile: { angle: 60, meaning: 'Possibilidade de cooperação e desenvolvimento entre duas funções.' },
  square: { angle: 90, meaning: 'Tensão que convida a ajustar necessidades ou modos de agir.' },
  trine: { angle: 120, meaning: 'Facilidade de expressão e cooperação entre duas funções.' },
  opposition: { angle: 180, meaning: 'Polaridade que convida a reconhecer e integrar duas perspetivas.' },
}

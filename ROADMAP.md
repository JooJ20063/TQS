# Roadmap do Estruturalis

Este documento apresenta a direção planejada para o desenvolvimento do Estruturalis.

O roadmap pode mudar conforme o projeto evolui, novos testes forem realizados e novas necessidades aparecerem.

---

## Fase 1 — Núcleo 2D de barras

Estado: avançado.

Objetivos:

- implementar pórticos planos 2D;
- resolver estruturas por matriz de rigidez;
- aceitar cargas nodais;
- aceitar cargas distribuídas;
- calcular reações;
- calcular deslocamentos;
- calcular esforços internos;
- gerar diagramas;
- gerar resultados em JSON;
- implementar peso próprio;
- implementar casos e combinações;
- gerar envoltória 2D;
- gerar dimensionamento preliminar de vigas 2D.

---

## Fase 2 — Núcleo 3D de barras

Estado: avançado/preliminar.

Objetivos:

- implementar `frame3d`;
- usar 6 graus de liberdade por nó;
- montar matriz de rigidez 3D;
- transformar esforços entre sistemas local e global;
- aceitar cargas nodais 3D;
- aceitar cargas distribuídas locais;
- aceitar cargas distribuídas globais;
- implementar peso próprio global;
- calcular reações 3D;
- calcular deslocamentos e rotações 3D;
- calcular esforços internos locais;
- verificar equilíbrio global 3D;
- gerar gráficos 3D;
- gerar visualização HTML interativa.

---

## Fase 3 — Pós-processamento e relatórios

Estado: em andamento.

Objetivos:

- gerar envoltória 3D;
- gerar relatório de deslocamentos e drift;
- gerar relatório preliminar de flechas;
- gerar dimensionamento preliminar de vigas 3D;
- gerar relatório crítico de pilares 3D;
- gerar relatório de cortante e torção em vigas 3D;
- gerar memorial integrado 3D;
- padronizar arquivos CSV, TXT e JSON;
- melhorar legibilidade dos relatórios;
- separar valores calculados, mínimos, máximos e adotados.

---

## Fase 4 — Validação acadêmica

Estado: iniciada.

Objetivos:

- criar suíte automática de validação 3D;
- validar vigas em balanço;
- validar cargas nodais;
- validar cargas distribuídas;
- validar barras inclinadas;
- validar peso próprio;
- validar pórticos simples;
- comparar resultados com soluções analíticas;
- comparar resultados com softwares conhecidos;
- documentar hipóteses e tolerâncias;
- ampliar cobertura de testes no CI.

---

## Fase 5 — Verificações normativas preliminares

Estado: planejada.

Objetivos:

- organizar parâmetros normativos em módulos;
- separar parâmetros configuráveis por norma;
- criar relatórios normativos preliminares;
- melhorar verificação de flechas;
- iniciar verificações preliminares de estados limites;
- melhorar dimensionamento de vigas;
- iniciar verificação de cortante;
- iniciar verificação de torção;
- iniciar verificação de pilares;
- estudar interação `N + My + Mz`;
- deixar todas as limitações explícitas nos relatórios.

Observação: esta fase não transforma o Estruturalis em software profissional. As verificações devem continuar sendo tratadas como preliminares e acadêmicas.

---

## Fase 6 — Detalhamento preliminar

Estado: planejada.

Objetivos:

- sugerir armaduras longitudinais;
- sugerir estribos;
- verificar espaçamentos preliminares;
- gerar relatórios de detalhamento;
- estudar ancoragem;
- estudar emendas;
- estudar critérios construtivos;
- melhorar apresentação dos resultados de dimensionamento.

---

## Fase 7 — Novos elementos estruturais

Estado: planejada.

Possíveis módulos futuros:

- lajes;
- grelhas;
- paredes;
- sapatas;
- vigas baldrame;
- radier;
- blocos de fundação;
- elementos de treliça;
- elementos de casca ou placa em fase futura.

A prioridade inicial continua sendo consolidar bem barras 2D e 3D antes de expandir para elementos mais complexos.

---

## Fase 8 — Distribuição experimental

Estado: planejada.

Objetivos:

- auditar dependências;
- melhorar interface de linha de comando;
- adicionar `--help` mais completo;
- adicionar `--version`;
- estudar opção `--no-plots`;
- estudar opção `--no-html`;
- testar PyInstaller;
- gerar executável experimental;
- medir tempo de execução;
- estimar requisitos mínimos;
- documentar instalação para usuários sem familiaridade com Python.

---

## Fase 9 — Interface de usuário

Estado: ideia futura.

Possibilidades:

- interface web local;
- interface desktop;
- editor visual simples de nós, barras e cargas;
- visualização integrada dos resultados;
- exportação de relatórios;
- integração com templates de projetos acadêmicos.

---

## Prioridades imediatas

As próximas prioridades do projeto são:

1. Consolidar documentação pública;
2. Ampliar validação 3D;
3. Melhorar relatórios e memorial;
4. Criar verificações preliminares de cortante e torção;
5. Iniciar estudo de dimensionamento de pilares;
6. Preparar empacotamento experimental.

---

## Princípio de desenvolvimento

O Estruturalis deve evoluir em passos pequenos, testáveis e revisáveis.

Cada nova funcionalidade deve, sempre que possível:

- ter exemplo;
- ter validação;
- gerar relatório claro;
- deixar hipóteses explícitas;
- deixar limitações explícitas;
- não quebrar funcionalidades já existentes.

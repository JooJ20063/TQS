# Estruturalis

**Estruturalis** é uma ferramenta acadêmica e open source de análise estrutural, desenvolvida em Python, com foco inicial em estruturas de barras 2D e 3D.

O projeto nasceu como um mini software didático de análise estrutural e vem evoluindo para uma plataforma modular de estudo, validação e pré-dimensionamento preliminar de estruturas.

> Estado atual: protótipo acadêmico em desenvolvimento.  
> Não substitui softwares profissionais nem verificação por profissional habilitado.

---

## Recursos atuais

### Análise 2D

- Pórticos planos 2D;
- nós com 3 graus de liberdade: `ux`, `uy`, `rz`;
- cargas nodais;
- cargas distribuídas uniformes;
- peso próprio automático;
- casos de carregamento;
- combinações;
- envoltória de esforços;
- verificação preliminar de flechas;
- dimensionamento preliminar de vigas em concreto armado;
- saída em JSON, CSV, TXT e PNG.

### Análise 3D

- Pórticos espaciais `frame3d`;
- nós com 6 graus de liberdade: `ux`, `uy`, `uz`, `rx`, `ry`, `rz`;
- elementos de barra 3D com 12 graus de liberdade;
- cargas nodais 3D;
- cargas distribuídas locais e globais;
- peso próprio automático;
- equilíbrio global 3D;
- envoltória 3D;
- relatório de deslocamentos e drift;
- dimensionamento preliminar de vigas 3D;
- relatório crítico de pilares 3D;
- relatório de cortante e torção em vigas 3D;
- memorial integrado 3D;
- gráficos 3D estáticos;
- visualização 3D interativa em HTML;
- suíte de validação para exemplos 3D.

---

## Instalação

### Linux/macOS

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

---

## Como rodar exemplos 2D

Viga com carga central:

```bash
python app/main.py examples/viga_carga_central.json -o results/viga_carga_central
```

Pórtico com peso próprio:

```bash
python app/main.py examples/portico_peso_proprio.json -o results/portico_peso_proprio
```

Pórtico com combinações:

```bash
python app/main.py examples/portico_combinacoes.json -o results/portico_combinacoes
```

---

## Como rodar exemplos 3D

Viga 3D em balanço com carga nodal:

```bash
python app/main.py examples/viga_3d_console.json -o results/viga_3d_console
```

Viga 3D em balanço com carga distribuída:

```bash
python app/main.py examples/viga_3d_console_q.json -o results/viga_3d_console_q
```

Pórtico 3D simples:

```bash
python app/main.py examples/portico_3d_simples.json -o results/portico_3d_simples
```

Suíte de validação 3D:

```bash
python scripts/validate_frame3d_examples.py
```

---

## Principais arquivos gerados em análises 3D

```text
resultados.json
envoltoria_3d.json
envoltoria_3d.csv
resumo_envoltoria_3d.txt
deslocamentos_3d.csv
resumo_deslocamentos_3d.txt
dimensionamento_vigas_3d.csv
resumo_dimensionamento_vigas_3d.txt
vigas_cortante_torcao_3d.csv
resumo_vigas_cortante_torcao_3d.txt
pilares_3d.csv
resumo_pilares_3d.txt
memorial_3d.txt
estrutura_3d.png
deformada_3d.png
estrutura_3d_interativa.html
resumo_grafico_3d.txt
resumo_flechas.txt
```

O arquivo recomendado para primeira leitura em análises 3D é:

```text
memorial_3d.txt
```

---

## Documentação

- [Análise frame3d](docs/frame3d.md): documentação do módulo tridimensional, incluindo graus de liberdade, cargas, eixos locais, envoltória, deslocamentos, vigas, pilares e limitações.
- [Roadmap](ROADMAP.md): plano de evolução do projeto.
- [Contribuindo](CONTRIBUTING.md): orientações para contribuir com o Estruturalis.

---

## Validação

O Estruturalis possui uma suíte inicial de validação para exemplos `frame3d`.

Ela verifica:

- execução dos principais exemplos 3D;
- equilíbrio global;
- deslocamentos conhecidos;
- esforços internos por módulo;
- geração dos principais arquivos de saída.

Para rodar:

```bash
python scripts/validate_frame3d_examples.py
```

---

## Limitações atuais

O Estruturalis ainda está em desenvolvimento e possui limitações importantes:

- não realiza dimensionamento normativo completo;
- não substitui softwares profissionais;
- não substitui revisão por engenheiro habilitado;
- o dimensionamento de vigas é preliminar;
- pilares 3D ainda não são dimensionados, apenas têm esforços críticos listados;
- cortante e torção em vigas 3D ainda não são dimensionados;
- interação `N + My + Mz` ainda não é verificada;
- detalhamento de armaduras ainda não é gerado;
- módulos de lajes, paredes e fundações ainda não estão implementados.

---

## Objetivo do projeto

O objetivo do Estruturalis é servir como uma base acadêmica, didática e aberta para:

- estudar análise estrutural matricial;
- comparar resultados com soluções conhecidas;
- desenvolver rotinas de pós-processamento;
- experimentar modelos 2D e 3D;
- evoluir gradualmente para verificações preliminares de concreto armado;
- construir uma alternativa open source de estudo estrutural.

---

## Licença

Projeto open source sob licença GNU GPL 3.0.

---

## Aviso técnico

O Estruturalis é uma ferramenta acadêmica em desenvolvimento.

Os resultados devem ser conferidos criticamente e não devem ser usados como única base para decisões de projeto, execução ou segurança estrutural.

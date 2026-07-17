# MiniTQS - software didático de análise estrutural 2D

Mini software didático de análise estrutural 2D por matriz de rigidez.

## Recursos atuais

- Pórtico plano 2D;
- nós com 3 graus de liberdade: `ux`, `uy`, `rz`;
- cargas nodais;
- cargas distribuídas uniformes;
- peso próprio automático;
- seções retangulares automáticas por `b` e `h`;
- casos de carregamento;
- combinações;
- saída em JSON;
- diagramas PNG: estrutura, deformada, cortante e momento fletor.

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

No Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Como rodar

```bash
python app/main.py examples/viga_carga_central.json -o results/viga_carga_central
```

```bash
python app/main.py examples/portico_peso_proprio.json -o results/portico_peso_proprio
```

```bash
python app/main.py examples/portico_combinacoes.json -o results/portico_combinacoes
```

## Observação

Projeto didático. Não substitui software profissional de projeto estrutural.

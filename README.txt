# MiniTQS - atualização: load_cases + combinations

Substitua estes arquivos no projeto:

- app/main.py
- core/model.py
- core/validation.py
- io_module/json_reader.py

Adicione este novo arquivo:

- core/load_cases.py

Adicione este exemplo:

- examples/portico_combinacoes.json

Depois rode:

python app/main.py examples/portico_combinacoes.json -o results/portico_combinacoes

Saída esperada:

results/portico_combinacoes/
├── ELS_01/
│   ├── resultados.json
│   ├── estrutura.png
│   ├── deformada.png
│   ├── cortante.png
│   └── momento_fletor.png
├── ELU_01/
│   └── ...
└── ELU_02/
    └── ...

Novidades:

1. load_cases

Agora você pode separar:
- PP
- SC
- VENTO_X
- outros casos

2. combinations

Agora você pode criar combinações como:

ELU_01 = 1.4 PP + 1.4 SC

3. Peso próprio automático integrado

Se self_weight estiver ligado e houver load_cases/combinations,
o peso próprio é inserido automaticamente no caso "PP".

Exemplo:

"self_weight": {
  "enabled": true,
  "gamma_default": 25.0,
  "load_case": "PP"
}

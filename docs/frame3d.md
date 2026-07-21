# Análise `frame3d` no Estruturalis

O módulo `frame3d` do Estruturalis permite a análise estrutural de pórticos espaciais, isto é, estruturas compostas por barras tridimensionais com seis graus de liberdade por nó.

Este documento descreve o funcionamento geral do `frame3d`, suas convenções, arquivos gerados, hipóteses adotadas e limitações atuais.

---

## 1. Objetivo do módulo `frame3d`

O `frame3d` foi desenvolvido para permitir a análise de estruturas tridimensionais formadas por barras, como:

- pórticos espaciais;
- vigas tridimensionais;
- pilares;
- estruturas com carregamentos em diferentes direções;
- modelos simplificados de edifícios.

O foco atual do Estruturalis é acadêmico e preliminar, com ênfase inicial em estruturas de concreto armado.

---

## 2. Ativando a análise 3D

Para usar o módulo tridimensional, o arquivo JSON do modelo deve conter:

```json
{
    "analysis_type": "frame3d"
}
```

Quando `analysis_type` não é informado, o Estruturalis assume, por padrão, análise `frame2d`.

---

## 3. Graus de liberdade por nó

Em modelos `frame3d`, cada nó possui seis graus de liberdade:

```text
ux, uy, uz, rx, ry, rz
```

Onde:

| Grau de liberdade | Significado |
|---|---|
| `ux` | deslocamento na direção global X |
| `uy` | deslocamento na direção global Y |
| `uz` | deslocamento na direção global Z |
| `rx` | rotação em torno do eixo global X |
| `ry` | rotação em torno do eixo global Y |
| `rz` | rotação em torno do eixo global Z |

Assim, uma estrutura com `n` nós possui:

```text
6 × n graus de liberdade
```

---

## 4. Nós

Cada nó 3D deve possuir coordenadas `x`, `y` e `z`.

Exemplo:

```json
{
    "id": 1,
    "x": 0.0,
    "y": 0.0,
    "z": 0.0
}
```

---

## 5. Elementos

Os elementos `frame3d` são barras espaciais ligando dois nós.

Exemplo:

```json
{
    "id": 1,
    "node_i": 1,
    "node_j": 2,
    "material": 1,
    "section": 1,
    "kind": "frame3d"
}
```

Cada elemento possui 12 graus de liberdade locais:

```text
[u, v, w, rx, ry, rz] no nó i
[u, v, w, rx, ry, rz] no nó j
```

---

## 6. Eixos locais da barra

Cada barra possui um sistema local de coordenadas.

O eixo local `x` é orientado do nó `i` para o nó `j`.

Os eixos locais `y` e `z` são definidos automaticamente pelo Estruturalis a partir da orientação espacial da barra.

Os esforços internos são apresentados no sistema local da barra.

| Esforço | Significado |
|---|---|
| `normal` | esforço axial local |
| `shear_y` | cortante na direção local y |
| `shear_z` | cortante na direção local z |
| `torsion` | torção em torno do eixo local x |
| `moment_y` | momento em torno do eixo local y |
| `moment_z` | momento em torno do eixo local z |

Atenção: em modelos tridimensionais, o sinal e o eixo local de um esforço dependem da orientação da barra.

---

## 7. Materiais

O material deve informar, no mínimo, o módulo de elasticidade `E`.

Exemplo:

```json
{
    "id": 1,
    "name": "concreto",
    "E": 30000000.0,
    "poisson": 0.2,
    "gamma": 25.0
}
```

| Campo | Significado |
|---|---|
| `E` | módulo de elasticidade |
| `poisson` | coeficiente de Poisson |
| `G` | módulo de cisalhamento, se informado diretamente |
| `gamma` | peso específico |

Se `G` não for informado, mas `poisson` for fornecido, o Estruturalis calcula:

```text
G = E / [2 × (1 + poisson)]
```

---

## 8. Seções

Para elementos 3D, a seção pode conter:

| Campo | Significado |
|---|---|
| `A` | área da seção |
| `Iy` | momento de inércia em torno do eixo local y |
| `Iz` | momento de inércia em torno do eixo local z |
| `J` | constante de torção |
| `I` | inércia usada por compatibilidade com modelos 2D |

Exemplo simplificado:

```json
{
    "id": 1,
    "name": "viga_25x50",
    "A": 0.125,
    "Iy": 0.0026041667,
    "Iz": 0.0006510417,
    "J": 0.001
}
```

---

## 9. Apoios

Em `frame3d`, os apoios podem restringir qualquer um dos seis graus de liberdade:

```json
{
    "node": 1,
    "ux": true,
    "uy": true,
    "uz": true,
    "rx": true,
    "ry": true,
    "rz": true
}
```

Um engaste tridimensional restringe todos os graus de liberdade.

---

## 10. Cargas nodais

As cargas nodais 3D podem conter forças e momentos:

```json
{
    "node": 2,
    "fx": 0.0,
    "fy": 0.0,
    "fz": -10.0,
    "mx": 0.0,
    "my": 0.0,
    "mz": 0.0
}
```

| Campo | Significado |
|---|---|
| `fx` | força na direção global X |
| `fy` | força na direção global Y |
| `fz` | força na direção global Z |
| `mx` | momento em torno do eixo global X |
| `my` | momento em torno do eixo global Y |
| `mz` | momento em torno do eixo global Z |

---

## 11. Cargas distribuídas

As cargas distribuídas podem ser definidas no sistema local ou global.

### 11.1 Carga distribuída local

```json
{
    "element": 1,
    "qx": 0.0,
    "qy": 0.0,
    "qz": -10.0,
    "coordinate_system": "local"
}
```

Nesse caso, `qx`, `qy` e `qz` são interpretados nos eixos locais da barra.

### 11.2 Carga distribuída global

```json
{
    "element": 1,
    "qx": 0.0,
    "qy": 0.0,
    "qz": -10.0,
    "coordinate_system": "global"
}
```

Nesse caso, a carga é informada no sistema global da estrutura e convertida internamente para o sistema local da barra.

---

## 12. Peso próprio

O peso próprio pode ser ativado no JSON do modelo.

Exemplo:

```json
{
    "self_weight": {
        "enabled": true,
        "load_case": "PP"
    }
}
```

Para modelos `frame3d`, o peso próprio é aplicado como carga distribuída global no eixo `Z` negativo:

```text
qz = -gamma × A
```

| Termo | Significado |
|---|---|
| `gamma` | peso específico do material |
| `A` | área da seção transversal |

---

## 13. Resultados principais

Após a análise, o Estruturalis gera diversos arquivos na pasta de saída.

Os principais são:

```text
resultados.json
envoltoria_3d.json
envoltoria_3d.csv
resumo_envoltoria_3d.txt
deslocamentos_3d.csv
resumo_deslocamentos_3d.txt
dimensionamento_vigas_3d.csv
resumo_dimensionamento_vigas_3d.txt
pilares_3d.csv
resumo_pilares_3d.txt
memorial_3d.txt
estrutura_3d.png
deformada_3d.png
estrutura_3d_interativa.html
resumo_grafico_3d.txt
resumo_flechas.txt
```

---

## 14. Equilíbrio global 3D

O Estruturalis calcula o equilíbrio global da estrutura 3D.

O resultado aparece em `resultados.json` no campo:

```json
"equilibrium": {
    "sum_forces": {
        "fx": 0.0,
        "fy": 0.0,
        "fz": 0.0
    },
    "sum_moments": {
        "mx": 0.0,
        "my": 0.0,
        "mz": 0.0
    },
    "force_norm": 0.0,
    "moment_norm": 0.0,
    "tolerance": 0.0,
    "status": "OK"
}
```

O status esperado para uma análise consistente é:

```text
OK
```

---

## 15. Envoltória 3D

A envoltória 3D reúne os esforços críticos por elemento.

Ela considera os seguintes grupos:

```text
normal
shear_y
shear_z
torsion
moment_y
moment_z
```

Para cada grupo, são registrados:

```text
valor mínimo
valor máximo
maior valor em módulo
caso responsável
componente responsável
elemento responsável
```

Arquivos gerados:

```text
envoltoria_3d.json
envoltoria_3d.csv
resumo_envoltoria_3d.txt
```

---

## 16. Deslocamentos e drift

O relatório de deslocamentos 3D calcula:

```text
máximo ux
máximo uy
máximo uz
máximo rx
máximo ry
máximo rz
deslocamento horizontal resultante
deslocamento translacional resultante
rotação resultante
drift aproximado por pavimento
```

Arquivos gerados:

```text
deslocamentos_3d.csv
resumo_deslocamentos_3d.txt
```

O drift é calculado comparando nós com mesmas coordenadas `x,y` em níveis `z` consecutivos.

---

## 17. Dimensionamento preliminar de vigas 3D

O Estruturalis possui uma rotina preliminar de dimensionamento de vigas 3D em concreto armado.

Arquivos gerados:

```text
dimensionamento_vigas_3d.csv
resumo_dimensionamento_vigas_3d.txt
```

A rotina:

- identifica elementos classificados como vigas;
- ignora elementos classificados como pilares;
- extrai `My` e `Mz` da envoltória 3D;
- dimensiona flexão simples separada em dois eixos;
- aplica armadura mínima preliminar;
- registra avisos e limitações.

Hipóteses atuais:

```text
Mz usa h como altura principal da seção
My usa b como altura resistente secundária
cortante não é dimensionado
torção não é dimensionada
ancoragem não é verificada
detalhamento não é gerado
```

Esta rotina é preliminar e acadêmica.

---

## 18. Relatório crítico de pilares 3D

O Estruturalis também gera um relatório de esforços críticos em pilares 3D.

Arquivos gerados:

```text
pilares_3d.csv
resumo_pilares_3d.txt
```

A rotina:

- identifica elementos predominantemente verticais;
- classifica esses elementos como pilares;
- extrai `N`, `Vy`, `Vz`, `T`, `My` e `Mz` da envoltória;
- aponta os pilares críticos;
- calcula um índice preliminar de triagem.

O índice preliminar usado é:

```text
|N|/Nmax + |My|/Mymax + |Mz|/Mzmax
```

Esse índice não é uma verificação normativa. Ele serve apenas para indicar quais pilares merecem atenção primeiro.

---

## 19. Memorial integrado 3D

O arquivo `memorial_3d.txt` reúne os principais resultados da análise:

```text
dados gerais
equilíbrio global
deslocamentos e drift
envoltória 3D
dimensionamento preliminar de vigas 3D
pilares críticos
arquivos gerados
limitações técnicas
```

Esse memorial é o primeiro arquivo recomendado para leitura após uma análise 3D.

---

## 20. Gráficos 3D

O Estruturalis gera gráficos estáticos:

```text
estrutura_3d.png
deformada_3d.png
```

Também gera uma visualização interativa:

```text
estrutura_3d_interativa.html
```

A visualização HTML permite inspecionar a estrutura em 3D no navegador.

---

## 21. Exemplo de execução

Para rodar uma viga 3D em balanço:

```bash
python app/main.py examples/viga_3d_console.json -o results/viga_3d_console
```

Para rodar um pórtico 3D simples:

```bash
python app/main.py examples/portico_3d_simples.json -o results/portico_3d_simples
```

Para rodar a suíte de validação 3D:

```bash
python scripts/validate_frame3d_examples.py
```

---

## 22. Limitações atuais

O módulo `frame3d` ainda possui limitações importantes:

- não realiza dimensionamento completo de pilares;
- não verifica interação `N + My + Mz`;
- não dimensiona cortante em vigas 3D;
- não dimensiona torção;
- não gera detalhamento final de armaduras;
- não substitui softwares profissionais;
- não substitui verificação por profissional habilitado;
- ainda está em fase acadêmica/preliminar.

---

## 23. Uso recomendado

O `frame3d` deve ser usado atualmente para:

- aprendizado de análise estrutural;
- estudo de pórticos espaciais;
- verificação didática de deslocamentos;
- comparação com soluções conhecidas;
- geração de relatórios acadêmicos;
- experimentação computacional.

O uso prático em engenharia exige validação adicional, revisão normativa e conferência por profissional habilitado.

---

## 24. Direção futura

Próximas evoluções previstas:

- validação adicional contra casos analíticos;
- documentação normativa;
- relatório de cortante e torção em vigas 3D;
- dimensionamento preliminar de pilares;
- verificação de interação `N + My + Mz`;
- detalhamento preliminar de armaduras;
- módulos para lajes, paredes e fundações;
- empacotamento experimental com PyInstaller;
- requisitos mínimos de sistema;
- interface mais amigável.

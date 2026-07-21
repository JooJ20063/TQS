# Contribuindo com o Estruturalis

Obrigado pelo interesse em contribuir com o Estruturalis.

O projeto está em desenvolvimento acadêmico e busca evoluir de forma organizada, com mudanças pequenas, testáveis e bem documentadas.

---

## Como contribuir

Contribuições podem envolver:

- correções de bugs;
- novos exemplos;
- melhorias de documentação;
- validações contra soluções conhecidas;
- melhorias em relatórios;
- novos módulos de cálculo;
- melhorias gráficas;
- revisão de hipóteses técnicas;
- organização do código.

---

## Fluxo recomendado

Crie uma branch a partir da `main`:

```bash
git checkout main
git pull origin main
git checkout -b nome-da-sua-branch
```

Faça alterações pequenas e focadas.

Depois rode os testes básicos:

```bash
python -m compileall app core io_module plots scripts
python scripts/validate_frame3d_examples.py
```

Faça o commit:

```bash
git add .
git commit -m "Mensagem clara sobre a alteração"
```

Envie para o GitHub:

```bash
git push -u origin nome-da-sua-branch
```

Abra um Pull Request para a branch `main`.

---

## Estilo de desenvolvimento

Prefira PRs pequenos.

Um bom PR deve ter:

- objetivo claro;
- poucas alterações misturadas;
- nomes de arquivos coerentes;
- código legível;
- comentários quando necessários;
- relatório ou documentação atualizada quando a saída mudar;
- testes ou validações quando possível.

Evite misturar, no mesmo PR:

- mudança no solver;
- mudança em gráficos;
- mudança em documentação;
- mudança em relatórios;
- mudança em exemplos.

Quando possível, faça um PR para cada assunto.

---

## Cuidados técnicos

O Estruturalis trabalha com análise estrutural. Por isso:

- não esconda hipóteses;
- não remova avisos técnicos sem justificativa;
- não apresente rotinas preliminares como dimensionamento final;
- não trate resultados como substitutos de software profissional;
- mantenha mensagens de limitação quando necessário.

---

## Convenções atuais

Algumas convenções importantes:

- `frame2d`: análise plana com graus de liberdade `ux`, `uy`, `rz`;
- `frame3d`: análise espacial com graus de liberdade `ux`, `uy`, `uz`, `rx`, `ry`, `rz`;
- esforços 3D são apresentados no sistema local da barra;
- relatórios preliminares devem indicar hipóteses e limitações;
- arquivos gerados devem ter nomes descritivos;
- exemplos devem ficar em `examples/`;
- resultados gerados devem ficar em `results/`.

---

## Validação

Antes de abrir um PR, rode:

```bash
python -m compileall app core io_module plots scripts
python scripts/validate_frame3d_examples.py
```

Também é recomendado rodar pelo menos um exemplo 2D e um exemplo 3D:

```bash
python app/main.py examples/viga_carga_central.json -o results/teste_viga_2d
python app/main.py examples/portico_3d_simples.json -o results/teste_portico_3d
```

---

## Documentação

Ao adicionar ou alterar uma funcionalidade, verifique se algum destes arquivos precisa ser atualizado:

- `README.md`;
- `ROADMAP.md`;
- `docs/frame3d.md`;
- relatórios TXT gerados pelo sistema;
- exemplos JSON.

---

## Aviso

O Estruturalis é uma ferramenta acadêmica em desenvolvimento.

Contribuições são bem-vindas, mas qualquer uso prático dos resultados exige conferência independente e responsabilidade técnica de profissional habilitado.

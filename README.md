# 🏋️ Code Gym

Aplicação web em **Python + Flask** para treinar programação em dupla: toda segunda-feira um novo desafio é liberado, cada pessoa envia a própria solução até domingo, e um placar acompanha pontos e *streak* (semanas seguidas de treino).

Criei o projeto para manter a constância nos estudos de Python com um colega. A ideia é simples: um desafio por semana, sem poder "colar" da solução do outro, e um pouco de competição saudável para manter a motivação.

---

## ✨ Funcionalidades

- **Login com senha** para cada participante.
- **Desafio da semana** escolhido automaticamente na primeira visita da segunda-feira.
- **Envio único e definitivo**: ninguém altera o código depois de ver o do outro.
- **Solução do outro bloqueada** até você enviar a sua (ou até o prazo acabar).
- **Comparação lado a lado** das duas soluções.
- **Histórico** de todas as semanas e quem concluiu cada uma.
- **Placar** com pontos por dificuldade e *streak* de semanas seguidas.
- Editor simples no navegador: Tab insere indentação, contador de linhas e confirmação antes de enviar.

## 🛠️ Tecnologias

| Camada | Ferramenta |
|---|---|
| Back-end | Python 3, Flask |
| Banco de dados | SQLite (`sqlite3` da biblioteca padrão, SQL escrito à mão) |
| Front-end | Jinja2, HTML, CSS ([Pico.css](https://picocss.com/)) e JavaScript puro |
| Segurança | `werkzeug.security` (hash de senha), sessões assinadas do Flask, `python-dotenv` |
| Deploy | PythonAnywhere (WSGI) |

## 🔒 Segurança

Alguns cuidados que tomei:

- **Senhas nunca são salvas em texto puro**: o banco guarda só o *hash* (`generate_password_hash` / `check_password_hash` do Werkzeug).
- **Nenhum segredo no repositório**: a `SECRET_KEY` fica num arquivo `.env`, que está no `.gitignore`. O repositório traz apenas o modelo `.env.example`.
- **O banco de dados não é versionado** (`code_gym.db` está no `.gitignore`), então usuários, hashes e soluções não vão para o GitHub.
- **Consultas parametrizadas** (`?` no SQL) em todo o acesso ao banco, o que evita SQL injection.
- **Usuários são criados só pelo terminal** (`flask criar-usuario`), com a senha digitada de forma oculta. Não existe cadastro aberto na web.
- **Rotas protegidas** por um decorator `login_obrigatorio`.
- Regras de negócio validadas **no servidor** (prazo, envio único), não só na interface.

## 🧠 Regras do jogo

| Regra | Detalhe |
|---|---|
| Desafio da semana | Na primeira visita de cada semana, o sistema pega o próximo desafio ainda não usado, na ordem do `desafios.json`. Quando todos foram usados, repete o mais antigo. |
| Prazo | Domingo da mesma semana. Depois disso o desafio fica só para consulta. |
| Envio | Uma solução por pessoa por semana (garantido por `UNIQUE (usuario_id, semana)` no banco). |
| Ver a do outro | Liberado depois que você envia a sua, ou depois que o prazo acaba. |
| Pontos | Fácil = 10, Médio = 20, Difícil = 30. |
| Streak | Semanas seguidas com envio. A semana atual não zera o streak enquanto não termina. |

## 📁 Estrutura

```
code_gym/
├── app.py                  # Rotas Flask (login, desafio, histórico, placar) e comando criar-usuario
├── database.py             # SQLite: tabelas, sorteio semanal, soluções, pontos e streak
├── desafios.json           # Banco de desafios (lógica, pandas, IA)
├── pythonanywhere_wsgi.py  # Configuração para deploy no PythonAnywhere
├── requirements.txt
├── .env.example            # Modelo do arquivo de configuração (sem segredos)
├── templates/              # Páginas HTML (Jinja2)
└── static/                 # CSS e JavaScript
```

### Modelo de dados

```
usuarios (id, nome, senha_hash)
desafios (id, slug, titulo, enunciado, nivel, tema)
semanas  (inicio [segunda-feira], desafio_id → desafios)
solucoes (id, usuario_id → usuarios, semana → semanas, codigo, comentario, enviado_em)
```

## 🚀 Como rodar localmente

Pré-requisito: Python 3.10 ou mais recente.

```bash
git clone https://github.com/Mariaclara2424/code-gym.git
cd code-gym

python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

**Configure a chave secreta:** copie `.env.example` para `.env` e troque o valor de `SECRET_KEY` por uma chave aleatória:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**Crie os dois usuários** (a senha é pedida no terminal e não aparece enquanto você digita):

```bash
flask --app app criar-usuario "Ana Souza"
flask --app app criar-usuario Bruno
```

> Rodar o comando com um nome que já existe troca a senha desse usuário.

**Inicie o servidor:**

```bash
python app.py
```

Acesse http://127.0.0.1:5000. O banco `code_gym.db` é criado sozinho na primeira execução.

## ➕ Adicionar desafios

Edite o `desafios.json` e reinicie o servidor:

```json
{
  "slug": "nome-unico-sem-espaco",
  "titulo": "Título",
  "nivel": "facil | medio | dificil",
  "tema": "logica | pandas | ia",
  "enunciado": ["linha 1", "linha 2"]
}
```

O `slug` identifica o desafio: se o texto de um desafio existente mudar, o banco é atualizado automaticamente (*upsert*).

## ☁️ Deploy (PythonAnywhere)

1. Envie o projeto para `/home/SEU_USUARIO/code_gym` e instale as dependências.
2. Crie o `.env` no servidor com uma `SECRET_KEY` nova.
3. Cole o conteúdo de `pythonanywhere_wsgi.py` no arquivo WSGI da aba **Web**. Ele também ajusta o fuso para `America/Sao_Paulo`, para a semana virar à meia-noite de Brasília.

## 🔭 Próximos passos

- Rodar testes automáticos nas soluções enviadas.
- Suporte a mais de dois participantes.
- Testes unitários para as regras de pontuação e streak.

---

Feito por **Maria Clara** · [GitHub](https://github.com/Mariaclara2424)

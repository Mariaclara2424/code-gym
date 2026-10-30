"""Code Gym: rotas da aplicação Flask."""

import os
from datetime import date, datetime
from functools import wraps

import click
from dotenv import load_dotenv
from flask import Flask, abort, flash, redirect, render_template, request, session, url_for

import database as db

load_dotenv(db.BASE_DIR / ".env")  # lê o .env da pasta do projeto (funciona também no PythonAnywhere)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-troque-isto-no-env")
app.teardown_appcontext(db.fechar_db)

with app.app_context():
    db.init_db()

NIVEIS = {"facil": "Fácil", "medio": "Médio", "dificil": "Difícil"}
TEMAS = {"logica": "Lógica", "pandas": "Pandas", "ia": "IA"}


# ---------- helpers ----------

def login_obrigatorio(view):
    """Redireciona para o login quem não estiver logado."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "usuario_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapper


@app.context_processor
def variaveis_globais():
    """Disponível em todos os templates."""
    return {
        "usuario_nome": session.get("usuario_nome"),
        "niveis": NIVEIS,
        "temas": TEMAS,
        "pontos": db.PONTOS,
    }


@app.template_filter("data_br")
def data_br(valor):
    if isinstance(valor, str):
        valor = date.fromisoformat(valor[:10])
    return valor.strftime("%d/%m/%Y")


@app.template_filter("data_hora_br")
def data_hora_br(valor):
    return datetime.fromisoformat(valor).strftime("%d/%m às %H:%M")


def texto_dias_restantes(prazo):
    dias = (prazo - date.today()).days
    if dias <= 0:
        return "hoje é o último dia!"
    if dias == 1:
        return "falta 1 dia"
    return f"faltam {dias} dias"


# ---------- rotas ----------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = db.verificar_login(request.form.get("nome", "").strip(), request.form.get("senha", ""))
        if usuario:
            session.clear()
            session["usuario_id"] = usuario["id"]
            session["usuario_nome"] = usuario["nome"]
            return redirect(url_for("index"))
        flash("Nome ou senha incorretos.", "erro")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_obrigatorio
def index():
    desafio = db.desafio_da_semana()
    if desafio is None:
        return render_template("index.html", desafio=None)

    prazo = db.prazo_da_semana(desafio["semana"])
    status = db.status_da_semana(desafio["semana"], primeiro_id=session["usuario_id"])
    enviei = status[0]["solucao"] is not None
    return render_template(
        "index.html",
        desafio=desafio,
        prazo=prazo,
        restante=texto_dias_restantes(prazo),
        status=status,
        enviei=enviei,
    )


@app.route("/desafio/<semana>", methods=["GET", "POST"])
@login_obrigatorio
def desafio(semana):
    desafio = db.desafio_por_semana(semana)
    if desafio is None:
        abort(404)

    usuario_id = session["usuario_id"]
    aberto = semana == db.segunda_da_semana().isoformat()  # só a semana atual aceita envios
    minha = db.solucao_do_usuario(usuario_id, semana)

    if request.method == "POST":
        codigo = request.form.get("codigo", "").strip()
        comentario = request.form.get("comentario", "").strip()
        if not aberto:
            flash("O prazo deste desafio já terminou.", "erro")
        elif minha:
            flash("Você já enviou sua solução desta semana.", "erro")
        elif not codigo:
            flash("Cole seu código antes de enviar.", "erro")
        else:
            db.salvar_solucao(usuario_id, semana, codigo, comentario)
            flash(f"Solução enviada! +{db.PONTOS[desafio['nivel']]} pontos 💪", "ok")
        return redirect(url_for("desafio", semana=semana))

    return render_template(
        "desafio.html",
        desafio=desafio,
        prazo=db.prazo_da_semana(semana),
        aberto=aberto,
        minha=minha,
        # Só vê a solução do outro depois de enviar a sua (ou depois do prazo).
        pode_ver=minha is not None or not aberto,
        status=db.status_da_semana(semana, primeiro_id=usuario_id),
    )


@app.route("/historico")
@login_obrigatorio
def historico():
    return render_template(
        "historico.html",
        semanas=db.historico(),
        semana_atual=db.segunda_da_semana().isoformat(),
    )


@app.route("/placar")
@login_obrigatorio
def placar():
    return render_template("placar.html", linhas=db.placar())


# ---------- comando de terminal ----------

@app.cli.command("criar-usuario")
@click.argument("nome")
@click.password_option("--senha", prompt="Senha", confirmation_prompt="Repita a senha")
def criar_usuario(nome, senha):
    """Cria um usuário (ou troca a senha, se ele já existir)."""
    try:
        click.echo(db.criar_ou_atualizar_usuario(nome.strip(), senha))
    except ValueError as erro:
        click.echo(f"Erro: {erro}")


if __name__ == "__main__":
    app.run(debug=True)

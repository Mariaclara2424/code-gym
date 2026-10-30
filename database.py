"""Acesso ao banco SQLite: criação das tabelas, desafio da semana, soluções, placar."""

import json
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

from flask import g
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "code_gym.db"
DESAFIOS_PATH = BASE_DIR / "desafios.json"

MAX_USUARIOS = 2
PONTOS = {"facil": 10, "medio": 20, "dificil": 30}

SCHEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    nome       TEXT UNIQUE NOT NULL,
    senha_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS desafios (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    slug      TEXT UNIQUE NOT NULL,
    titulo    TEXT NOT NULL,
    enunciado TEXT NOT NULL,
    nivel     TEXT NOT NULL CHECK (nivel IN ('facil', 'medio', 'dificil')),
    tema      TEXT NOT NULL
);

-- Uma linha por semana: qual desafio foi escolhido para ela.
CREATE TABLE IF NOT EXISTS semanas (
    inicio     TEXT PRIMARY KEY,               -- segunda-feira, AAAA-MM-DD
    desafio_id INTEGER NOT NULL REFERENCES desafios(id)
);

CREATE TABLE IF NOT EXISTS solucoes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    semana     TEXT NOT NULL REFERENCES semanas(inicio),
    codigo     TEXT NOT NULL,
    comentario TEXT,
    enviado_em TEXT NOT NULL,
    UNIQUE (usuario_id, semana)                -- um envio por pessoa por semana
);
"""


# ---------- conexão ----------

def get_db():
    """Abre (uma vez por requisição) a conexão com o banco."""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row  # permite acessar colunas pelo nome
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def fechar_db(_erro=None):
    conexao = g.pop("db", None)
    if conexao is not None:
        conexao.close()


def init_db():
    """Cria as tabelas e sincroniza os desafios do desafios.json."""
    db = get_db()
    db.executescript(SCHEMA)

    desafios = json.loads(DESAFIOS_PATH.read_text(encoding="utf-8"))
    for d in desafios:
        enunciado = d["enunciado"]
        if isinstance(enunciado, list):  # no JSON o enunciado é uma lista de linhas
            enunciado = "\n".join(enunciado)
        db.execute(
            """
            INSERT INTO desafios (slug, titulo, enunciado, nivel, tema)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
                titulo = excluded.titulo, enunciado = excluded.enunciado,
                nivel = excluded.nivel, tema = excluded.tema
            """,
            (d["slug"], d["titulo"], enunciado, d["nivel"], d["tema"]),
        )
    db.commit()


# ---------- usuários ----------

def criar_ou_atualizar_usuario(nome, senha):
    db = get_db()
    existente = db.execute("SELECT id FROM usuarios WHERE nome = ?", (nome,)).fetchone()
    senha_hash = generate_password_hash(senha)

    if existente:
        db.execute("UPDATE usuarios SET senha_hash = ? WHERE id = ?", (senha_hash, existente["id"]))
        db.commit()
        return f"Senha de '{nome}' atualizada."

    total = db.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
    if total >= MAX_USUARIOS:
        raise ValueError(f"O Code Gym é para {MAX_USUARIOS} usuários e já existem {total}.")

    db.execute("INSERT INTO usuarios (nome, senha_hash) VALUES (?, ?)", (nome, senha_hash))
    db.commit()
    return f"Usuário '{nome}' criado."


def verificar_login(nome, senha):
    """Devolve o usuário se nome e senha baterem, senão None."""
    usuario = get_db().execute("SELECT * FROM usuarios WHERE nome = ?", (nome,)).fetchone()
    if usuario and check_password_hash(usuario["senha_hash"], senha):
        return usuario
    return None


def listar_usuarios():
    return get_db().execute("SELECT id, nome FROM usuarios ORDER BY nome").fetchall()


# ---------- semanas e desafios ----------

def segunda_da_semana(dia=None):
    dia = dia or date.today()
    return dia - timedelta(days=dia.weekday())  # weekday(): segunda = 0


def prazo_da_semana(inicio):
    """Prazo = domingo da semana que começa em `inicio` (AAAA-MM-DD)."""
    return date.fromisoformat(inicio) + timedelta(days=6)


def desafio_por_semana(inicio):
    return get_db().execute(
        """
        SELECT d.*, s.inicio AS semana
        FROM semanas s JOIN desafios d ON d.id = s.desafio_id
        WHERE s.inicio = ?
        """,
        (inicio,),
    ).fetchone()


def desafio_da_semana():
    """Desafio da semana atual. Na primeira visita da semana, escolhe o próximo."""
    inicio = segunda_da_semana().isoformat()
    desafio = desafio_por_semana(inicio)
    if desafio:
        return desafio

    db = get_db()
    # Próximo desafio que ainda não foi usado, na ordem em que foi cadastrado.
    proximo = db.execute(
        "SELECT id FROM desafios WHERE id NOT IN (SELECT desafio_id FROM semanas) ORDER BY id LIMIT 1"
    ).fetchone()
    if proximo is None:
        # Todos já foram usados: repete o que saiu há mais tempo.
        proximo = db.execute(
            "SELECT desafio_id AS id FROM semanas GROUP BY desafio_id ORDER BY MAX(inicio) LIMIT 1"
        ).fetchone()
    if proximo is None:
        return None  # nenhum desafio cadastrado

    db.execute("INSERT INTO semanas (inicio, desafio_id) VALUES (?, ?)", (inicio, proximo["id"]))
    db.commit()
    return desafio_por_semana(inicio)


# ---------- soluções ----------

def solucao_do_usuario(usuario_id, semana):
    return get_db().execute(
        "SELECT * FROM solucoes WHERE usuario_id = ? AND semana = ?", (usuario_id, semana)
    ).fetchone()


def salvar_solucao(usuario_id, semana, codigo, comentario):
    db = get_db()
    db.execute(
        """
        INSERT INTO solucoes (usuario_id, semana, codigo, comentario, enviado_em)
        VALUES (?, ?, ?, ?, ?)
        """,
        (usuario_id, semana, codigo, comentario or None,
         datetime.now().isoformat(sep=" ", timespec="minutes")),
    )
    db.commit()


def status_da_semana(semana, primeiro_id=None):
    """Lista [{nome, solucao}] com todos os usuários (quem ainda não enviou vem com solucao=None).
    O usuário `primeiro_id` aparece primeiro (para ficar à esquerda no lado a lado)."""
    resultado = []
    for usuario in listar_usuarios():
        resultado.append({
            "id": usuario["id"],
            "nome": usuario["nome"],
            "solucao": solucao_do_usuario(usuario["id"], semana),
        })
    resultado.sort(key=lambda item: item["id"] != primeiro_id)
    return resultado


# ---------- histórico e placar ----------

def historico():
    """Semanas já sorteadas (mais recente primeiro), com quem completou cada uma."""
    db = get_db()
    semanas = db.execute(
        """
        SELECT s.inicio AS semana, d.titulo, d.nivel, d.tema
        FROM semanas s JOIN desafios d ON d.id = s.desafio_id
        ORDER BY s.inicio DESC
        """
    ).fetchall()
    envios = db.execute(
        "SELECT so.semana, u.nome FROM solucoes so JOIN usuarios u ON u.id = so.usuario_id ORDER BY u.nome"
    ).fetchall()

    concluintes = {}
    for envio in envios:
        concluintes.setdefault(envio["semana"], []).append(envio["nome"])

    return [dict(s, concluintes=concluintes.get(s["semana"], [])) for s in semanas]


def calcular_streak(semanas_feitas):
    """Quantas semanas seguidas (até agora) o usuário completou.
    A semana atual ainda está em aberto, então não quebra o streak se faltar."""
    semana = segunda_da_semana()
    if semana.isoformat() not in semanas_feitas:
        semana -= timedelta(days=7)

    streak = 0
    while semana.isoformat() in semanas_feitas:
        streak += 1
        semana -= timedelta(days=7)
    return streak


def placar():
    db = get_db()
    linhas = []
    for usuario in listar_usuarios():
        envios = db.execute(
            """
            SELECT so.semana, d.nivel
            FROM solucoes so
            JOIN semanas s ON s.inicio = so.semana
            JOIN desafios d ON d.id = s.desafio_id
            WHERE so.usuario_id = ?
            """,
            (usuario["id"],),
        ).fetchall()
        linhas.append({
            "nome": usuario["nome"],
            "pontos": sum(PONTOS[e["nivel"]] for e in envios),
            "semanas": len(envios),
            "streak": calcular_streak({e["semana"] for e in envios}),
        })
    linhas.sort(key=lambda l: (l["pontos"], l["streak"]), reverse=True)
    return linhas

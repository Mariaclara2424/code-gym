# Conteúdo para colar no arquivo WSGI do PythonAnywhere (aba Web > "WSGI configuration file").
# Troque SEU_USUARIO pelo seu nome de usuário do PythonAnywhere.

import os
import sys
import time

# Servidores do PythonAnywhere usam UTC; isso faz a "segunda-feira" virar no horário de Brasília.
os.environ["TZ"] = "America/Sao_Paulo"
time.tzset()

caminho = "/home/SEU_USUARIO/code_gym"
if caminho not in sys.path:
    sys.path.insert(0, caminho)

from app import app as application  # noqa: E402

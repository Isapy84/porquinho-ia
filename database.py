import json
import logging
import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

ARQUIVO_BANCO = os.path.join(BASE_DIR, "dados.json")

SUPABASE_URL = os.getenv("SUPABASE_URL")
if SUPABASE_URL:
    SUPABASE_URL = SUPABASE_URL.strip().replace("\n", "").replace("\r", "").replace(" ", "")

SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if SUPABASE_KEY:
    SUPABASE_KEY = SUPABASE_KEY.strip().replace("\n", "").replace("\r", "").replace(" ", "")

supabase_client = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        from supabase import create_client
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logging.info(" Conectado com sucesso ao Supabase (Banco de Dados na Nuvem).")
    except Exception as e:
        logging.error(f"❌ Falha ao conectar ao Supabase: {e}. Usando dados.json local como fallback.")
        supabase_client = None
else:
    logging.info("ℹ️ Variáveis SUPABASE_URL/SUPABASE_KEY não encontradas. Usando dados.json local.")

def carregar_todos_dados():
    """Carrega dados do Supabase ou do dados.json local."""
    if supabase_client:
        try:
            resposta = supabase_client.table("user_finances").select("*").execute()
            dados = {}
            for item in resposta.data:
                dados[str(item["user_id"])] = {
                    "orcamento_inicial": float(item.get("orcamento_inicial", 0.0)),
                    "saldo_atual": float(item.get("saldo_atual", 0.0)),
                    "gastos": item.get("gastos", [])
                }
            return dados
        except Exception as e:
            logging.error(f"Erro ao ler do Supabase: {e}. Tentando arquivo local.")

    if not os.path.exists(ARQUIVO_BANCO):
        return {}
    try:
        with open(ARQUIVO_BANCO, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Erro ao ler {ARQUIVO_BANCO}: {e}")
        return {}

def salvar_usuario(user_id, dados_usuario):
    """Salva os dados de um usuário específico no banco ou arquivo."""
    user_id = str(user_id)
    if supabase_client:
        try:
            payload = {
                "user_id": user_id,
                "orcamento_inicial": dados_usuario.get("orcamento_inicial", 0.0),
                "saldo_atual": dados_usuario.get("saldo_atual", 0.0),
                "gastos": dados_usuario.get("gastos", [])
            }
            supabase_client.table("user_finances").upsert(payload).execute()
        except Exception as e:
            logging.error(f"Erro ao salvar usuário no Supabase: {e}")

    # Mantém também cópia sincronizada no arquivo local se possível
    todos = _carregar_local()
    todos[user_id] = dados_usuario
    _salvar_local(todos)

def deletar_usuario(user_id):
    """Remove o usuário (ex: no comando /reset)."""
    user_id = str(user_id)
    if supabase_client:
        try:
            supabase_client.table("user_finances").delete().eq("user_id", user_id).execute()
        except Exception as e:
            logging.error(f"Erro ao deletar usuário no Supabase: {e}")

    todos = _carregar_local()
    if user_id in todos:
        del todos[user_id]
        _salvar_local(todos)

def salvar_todos_dados(dados):
    """Salva todos os dados (compatibilidade total com bot.py atual)."""
    for u_id, u_data in dados.items():
        salvar_usuario(u_id, u_data)
    _salvar_local(dados)

def _carregar_local():
    if not os.path.exists(ARQUIVO_BANCO):
        return {}
    try:
        with open(ARQUIVO_BANCO, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _salvar_local(dados):
    try:
        with open(ARQUIVO_BANCO, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.error(f"Erro ao salvar localmente: {e}")

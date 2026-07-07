import logging
from datetime import datetime
import json
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from google.genai import types

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# 🔑 CONFIGURAÇÕES DE TOKENS
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

ARQUIVO_BANCO = "dados.json"
ai_client = genai.Client(api_key=GEMINI_API_KEY)

def carregar_todos_dados():
    if not os.path.exists(ARQUIVO_BANCO):
        return {}
    with open(ARQUIVO_BANCO, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_todos_dados(dados):
    with open(ARQUIVO_BANCO, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

# 🚀 COMANDO /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.first_name
    todos_dados = carregar_todos_dados()
    
    if user_id in todos_dados:
        saldo = todos_dados[user_id]["saldo_atual"]
        await update.message.reply_text(
            f"Olá de volta, {user_name}! 🐷\n"
            f"Seu saldo atual é de **R$ {saldo:.2f}**.\n\n"
            "📌 **Comandos úteis:**\n"
            "/extrato - Veja sua lista de gastos\n"
            "/ajuda <pergunta> - Peça conselhos à IA\n"
            "/reset - Comece um novo mês"
        )
    else:
        context.user_data["configurando_renda"] = True
        await update.message.reply_text(
            f"Olá, {user_name}! Bem-vindo ao Porquinho IA. 🐷\n\n"
            "Digite qual será o seu **orçamento ou limite de gastos** para este mês:\n"
            "(Exemplo: 704 ou 1500)"
        )

# 📊 FUNCIONALIDADE 1: COMANDO /extrato
async def extrato(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    todos_dados = carregar_todos_dados()
    
    if user_id not in todos_dados or not todos_dados[user_id]["gastos"]:
        await update.message.reply_text("📭 Você ainda não registrou nenhum gasto este mês!")
        return
    
    dados_user = todos_dados[user_id]
    
    # Organiza os gastos agrupando por categorias
    categorias = {}
    total_gasto = 0.0
    
    for g in dados_user["gastos"]:
        cat = g["categoria"]
        if cat not in categorias:
            categorias[cat] = []
        categorias[cat].append(g)
        total_gasto += g["valor"]
        
    # Monta a mensagem do extrato de forma linda
    mensagem = "📊 **Seu Extrato do Mês:**\n\n"
    for cat, lista_gastos in categorias.items():
        mensagem += f"📂 *{cat}:*\n"
        for g in lista_gastos:
            mensagem += f"  • {g['item']} — R$ {g['valor']:.2f} ({g['data']})\n"
        mensagem += "\n"
        
    mensagem += "───────────────────\n"
    mensagem += f"💸 **Total Gasto:** R$ {total_gasto:.2f}\n"
    mensagem += f"💰 **Saldo Restante:** R$ {dados_user['saldo_atual']:.2f}"
    
    await update.message.reply_text(mensagem, parse_mode="Markdown")

# 🔄 FUNCIONALIDADE 2: COMANDO /reset
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    todos_dados = carregar_todos_dados()
    
    if user_id in todos_dados:
        # Remove o usuário do dicionário para que ele possa reconfigurar
        del todos_dados[user_id]
        salvar_todos_dados(todos_dados)
        
    context.user_data["configurando_renda"] = True
    await update.message.reply_text(
        "🔄 **Porquinho Reiniciado!**\n"
        "Seu histórico anterior foi zerado para dar início ao novo mês.\n\n"
        "Por favor, digite o seu **novo orçamento inicial**:"
    )

# 💡 FUNCIONALIDADE 3: COMANDO /ajuda (IA Consultora)
async def ajuda_ia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    todos_dados = carregar_todos_dados()
    
    # Captura a pergunta que o usuário fez após o comando /ajuda
    pergunta_usuario = " ".join(context.args)
    
    if not pergunta_usuario:
        await update.message.reply_text(
            "Digite uma pergunta após o comando!\n"
            "Exemplo: `/ajuda Será que posso comprar uma blusa de 80 reais?`"
        )
        return
        
    if user_id not in todos_dados:
        await update.message.reply_text("Configure seu saldo inicial primeiro digitando `/start`!")
        return

    await update.message.reply_text("🤖 Analisando suas finanças... Aguarde um instante.")
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    dados_user = todos_dados[user_id]
    
    # Prompt que envia o histórico real de gastos e saldo atual para o Gemini analisar
    prompt_analise = (
        f"Você é o Porquinho IA, um consultor financeiro amigável e focado em ajudar o usuário.\n"
        f"Aqui estão as finanças reais do usuário atualmente:\n"
        f"- Orçamento Inicial do Mês: R$ {dados_user['orcamento_inicial']:.2f}\n"
        f"- Saldo Restante Atual: R$ {dados_user['saldo_atual']:.2f}\n"
        f"- Lista Completa de Gastos feitos até agora: {json.dumps(dados_user['gastos'])}\n\n"
        f"O usuário te fez a seguinte pergunta: '{pergunta_usuario}'.\n"
        f"Responda diretamente a pergunta dele de forma bem curta, sincera e acolhedora, "
        f"usando os dados financeiros fornecidos para justificar se ele deve ou não gastar e dê uma dica de economia."
    )

    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_analise
        )
        await update.message.reply_text(response.text, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Erro na IA consultora: {e}")
        await update.message.reply_text("❌ Desculpe, não consegui analisar suas finanças no momento.")

# 📩 ESCUTADOR DE MENSAGENS DIRETAS (GASTOS)
async def escutar_mensagens(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    texto_usuario = update.message.text
    todos_dados = carregar_todos_dados()

    if context.user_data.get("configurando_renda"):
        try:
            valor_renda = float(texto_usuario.replace("R$", "").replace(",", ".").strip())
            todos_dados[user_id] = {
                "orcamento_inicial": valor_renda,
                "saldo_atual": valor_renda,
                "gastos": []
            }
            salvar_todos_dados(todos_dados)
            context.user_data["configurando_renda"] = False
            await update.message.reply_text(
                f"🎉 Perfeito! Seu orçamento de **R$ {valor_renda:.2f}** foi configurado.\n"
                "Sempre que gastar algo, basta digitar aqui!"
            )
            return
        except ValueError:
            await update.message.reply_text("❌ Digite apenas o número, ex: `704` ou `1200`.")
            return

    if user_id not in todos_dados:
        await update.message.reply_text("Digite `/start` para começar!")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    prompt_ia = (
        f"Analise o seguinte gasto enviado pelo usuário: '{texto_usuario}'. "
        "Extraia o item comprado (corrija maiúsculas se necessário), o valor numérico e defina a categoria mais adequada "
        "(ex: Alimentação, Transporte, Lazer, Pets, Contas e Utilidades, Saúde, Vestuário, Outros). "
        "Responda ESTRITAMENTE em formato JSON com as chaves 'item', 'valor' e 'categoria'."
    )

    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_ia,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        
        dados_gasto = json.loads(response.text)
        item = dados_gasto.get("item", "Não identificado")
        valor_gasto = float(dados_gasto.get("valor", 0.00))
        categoria = dados_gasto.get("categoria", "Outros")
        data_atual = datetime.now().strftime("%d/%m/%Y")
        
        dados_usuario = todos_dados[user_id]
        dados_usuario["saldo_atual"] -= valor_gasto
        dados_usuario["gastos"].append({
            "item": item,
            "valor": valor_gasto,
            "categoria": categoria,
            "data": data_atual
        })
        
        todos_dados[user_id] = dados_usuario
        salvar_todos_dados(todos_dados)
        
        saldo_restante = dados_usuario["saldo_atual"]
        orcamento = dados_usuario["orcamento_inicial"]
        
        alerta_meta = ""
        if saldo_restante <= (orcamento * 0.5) and saldo_restante > (orcamento * 0.2):
            alerta_meta = "\n\n⚠️ **Atenção:** Você já gastou mais de 50% do seu limite disponível!"
        elif saldo_restante <= (orcamento * 0.2) and saldo_restante > 0:
            alerta_meta = "\n\n🚨 **ALERTA CRÍTICO:** Você tem menos de 20% do seu saldo restante!"
        elif saldo_restante <= 0:
            alerta_meta = "\n\n🛑 **SALDO ESTOURADO:** Seu orçamento zerou ou ficou negativo!"

        resposta_formatada = (
            "✅ **Gasto Registrado!**\n"
            f"📝 {item} ({categoria})\n"
            f"💰 **R${valor_gasto:.2f}**\n"
            f"⚙️ {data_atual}\n\n"
            f"📉 **Saldo Restante:** R$ {saldo_restante:.2f}"
            f"{alerta_meta}"
        )
        
    except Exception as e:
        logging.error(f"Erro ao processar: {e}")
        resposta_formatada = "❌ Desculpe, tive um problema ao calcular o seu gasto."

    await update.message.reply_text(resposta_formatada, parse_mode="Markdown")

def main():
    print("Porquinho IA Premium rodando...")
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Registrando os novos comandos do bot
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("extrato", extrato))
    application.add_handler(CommandHandler("reset", reset))
    application.add_handler(CommandHandler("ajuda", ajuda_ia))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, escutar_mensagens))
    application.run_polling()

if __name__ == "__main__":
    main()
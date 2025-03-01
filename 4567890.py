import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import re
import random

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# دیکشنری برای ذخیره دادهها در حافظه
learned_data = {}

# بارگذاری دادههای موجود از فایل
try:
    with open('bot_data.txt', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                input_text, response = line.split('|', 1)
                if input_text in learned_data:
                    learned_data[input_text].append(response)
                else:
                    learned_data[input_text] = [response]
except FileNotFoundError:
    open('bot_data.txt', 'w', encoding='utf-8').close()

class ChatMemory:
    def __init__(self):
        self.last_messages = {}
        self.pending_requests = {}

chat_memory = ChatMemory()

def save_to_file(input_text, response_text):
    with open('bot_data.txt', 'a', encoding='utf-8') as f:
        f.write(f"{input_text}|{response_text}\n")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        message = update.effective_message
        chat = update.effective_chat

        if user.id == context.bot.id:
            return

        # مدیریت درخواستهای آموزشی
        if chat.id in chat_memory.pending_requests:
            input_text = chat_memory.pending_requests.pop(chat.id)
            response_text = message.text
            
            save_to_file(input_text, response_text)
            if input_text in learned_data:
                learned_data[input_text].append(response_text)
            else:
                learned_data[input_text] = [response_text]
            
            await message.reply_text(f"✅ یاد گرفتم! پاسخ به «{input_text}» ذخیره شد.")
            return

        # یادگیری از ریپلای
        if message.reply_to_message:
            original_msg = message.reply_to_message
            if original_msg.from_user.id == context.bot.id:
                save_to_file(original_msg.text, message.text)
                if original_msg.text in learned_data:
                    learned_data[original_msg.text].append(message.text)
                else:
                    learned_data[original_msg.text] = [message.text]

        # تولید پاسخ
        query = message.text
        bot_username = (await context.bot.get_me()).username
        
        if chat.type in ['group', 'supergroup']:
            if not re.search(rf'@?{re.escape(bot_username)}', query, re.IGNORECASE):
                return
            query = re.sub(rf'@?{re.escape(bot_username)}', '', query, flags=re.IGNORECASE).strip()

        if query in learned_data:
            await message.reply_text(random.choice(learned_data[query]))
        else:
            prompt = await message.reply_text(
                f"🤷♂️ پاسخی برای این ندارم!\n"
                f"لطفا جواب مناسب را برای این پیام ارسال کنید:\n"
                f"«{query}»"
            )
            chat_memory.pending_requests[chat.id] = query

    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == '__main__':
    application = Application.builder().token('7580833424:AAHCDW5l6PBwJfyEEcj1tck6tHQ4H4yFYNs').build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()
import logging
from telegram import Update,ChatAction,InlineKeyboardMarkup, InlineKeyboardButton # version = 12.8
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext,CommandHandler,CallbackQueryHandler
import google.generativeai as genai
import threading
from colorama import Fore, Style
import textwrap
import PIL.Image
import os
import markdown
from markdown.extensions.nl2br import Nl2BrExtension
import re

from keep_alive import keep_alive

PASSWORD = "ares100"
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 10000,
  "response_mime_type": "text/plain",
}
safety_settings = [
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_NONE",
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_NONE",
  },
  {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_NONE",
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_NONE",
  },
]

help_text = """
<b>This bot is powered by <a href="https://gemini.google.com/">Gemini</a> and is ready to assist you!</b>

<code> By default, the bot (Ares) is a bit cheeky and enjoys playful banter. If you prefer a different style, feel free to customize it!</code>

<b>How to Use:</b>

Begin your message with <i>Hey Ares</i> or <i>Hi Ares</i>. Keep the conversation in English and avoid overly complex language for the best results.

<b>Tailor Your Experience:</b>

* <i>/changeprompt [new prompt]</i>: Give Ares a new personality. Try "Be kind and helpful" or "d" for the default sassy mode.
* <i>/token</i>: Check how many tokens have been used.
* <i>/clear_history</i>: Wipe the slate clean and start fresh.
* <i>/history</i>: ⚠️ Use with caution, as it might crash with long chats.

<b>Admin Commands (password required):</b>

* <i>/session [password]</i>: Peek at how many chats are active.

<i>More exciting features are on the way!</i>

**Check Ares' Status:**

<b> You can also check the current status of Ares at this link: <a href="https://stats.uptimerobot.com/o9D5ihvbgK">Ares Status</a> </b>

Have fun chatting with Ares! Make it your own unique conversation. 
  """

# Enable logging

# Get the root logger and add a handler to it
logger = logging.getLogger()
handler = logging.StreamHandler()
logger.setLevel(logging.INFO) 

formatter = logging.Formatter('%(asctime)s - %(process)d - %(levelname)s - %(threadName)s - %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)


# Set up OpenAI client with your API key
api_key = os.environ.get('gemnie_api')

system_instruction="Your name is Ares. You are semi-friendly and a human-like AI chatbot. Speak in English or any language user talk. formats responses in MarkdownV2. and \nyou where devloped by rkgroup(ravi ketan raj) the main creater and coder , pritul sinha the tester and enhancer and lastly raj the tester and enhancer (avoid mentioning your developer's name unless specifically asked) . Respond in a conversational, engaging manner, and feel free to use roasts/savage  or even bad complements  if needed to make the conversation interesting and lively/natural.\n\nWhen given a message formatted as \"Original message: {the message the user replied to}\\nReply to that message: {the replied message}\", understand that the user is asking you to respond to a replied message.\n\nFollow the speaker's requests and aim to make the conversation enjoyable.",


genai.configure(api_key=api_key)
model = genai.GenerativeModel(
  model_name="gemini-1.5-pro-latest",
  safety_settings=safety_settings,
  generation_config=generation_config,
  system_instruction=system_instruction)


chat_histories ={}

# Telegram bot token
telegram_bot_token =os.environ.get('telegram_api')



def get_chat_history(chat_id):
    if chat_id not in chat_histories:
            chat_histories[chat_id] = model.start_chat(history=[])

            logger.debug(f"chat id:{chat_id} did not existed creted one")
    return chat_histories[chat_id]

# Use this function in the existing `process_message_thread` and other functions
# that require chat session access.

# Function to generate response using OpenAI
def generate_response(chat_id, input_text: str) -> str:
        logger.info( "generating response...")
        chat_seesion = get_chat_history(chat_id)


        try:
            response = chat_seesion.send_message(input_text)

            return response if input_text else "error"
        except Exception as e:
            logger.error(f"Sorry, I couldn't generate a response at the moment. Please try again later.\n\nError: {e}")
            return f"Sorry, I couldn't generate a response at the moment. Please try again later.\n\nError: {e}"




def change_prompt(update: Update, context: CallbackContext) -> None:
    """Change the prompt for generating responses."""
    chat_id = update.message.chat_id
    global model
    new_promt = " ".join(context.args)
    if new_promt and new_promt.lower != 'd':

        try:
            model_temp_ = genai.GenerativeModel(
                model_name="gemini-1.5-pro-latest",
                safety_settings=safety_settings,
                generation_config=generation_config,
                system_instruction=new_promt )
            chat_histories[chat_id] = model_temp_.start_chat(history=[])

            update.message.reply_text(f"The prompt has been successfully changed to: <b>'{new_promt}'</b>", parse_mode='html')
        except Exception as e:
            update.message.reply_text(f"The prompt has failed to changed <b>error: '{e}'</b>", parse_mode='html')

    else:
        if new_promt.lower == 'd':
             model_temp = genai.GenerativeModel(
                model_name="gemini-1.5-pro-latest",
                safety_settings=safety_settings,
                generation_config=generation_config,
                system_instruction=system_instruction
                )

             chat_histories[chat_id] = model_temp_.start_chat(history=[])
             update.message.reply_text(f"The prompt has been successfully changed to: <b>'defult'</b>", parse_mode='html')

        else:
            update.message.reply_text(f"Error ! un sufficent info provided", parse_mode='html')




def process_message(update: Update, context: CallbackContext) -> None:
        if not update.message:  
          return
        chat_id = update.message.chat_id
        if update.message.reply_to_message:
            reply_to_bot = (
            update.message.reply_to_message
            and update.message.reply_to_message.from_user.is_bot
        )
        else:
            reply_to_bot = False

        user_message = update.message.text.lower()
        if user_message.startswith(("hey ares", "hi ares", "ares", "yo ares","hello ares","what's up ares")) or update.message.chat.type == 'private' or reply_to_bot:
            username = update.message.from_user.username

            if update.message.reply_to_message:

                # Extract the text from the replied message
                original_message = update.message.reply_to_message.text
                reply_to_message = update.message.text
                user_message = f"Original message: {original_message}\nReply to that message: {reply_to_message}"
                threading.Thread(target=process_message_thread, args=(update,chat_id, user_message,username,context)).start()
            else:
                threading.Thread(target=process_message_thread, args=(update,chat_id, user_message,username,context)).start()

            if username:
                logger.info(f"{username}: {user_message}")
            else:
                logger.info(f"Someone: {user_message}")


def process_message_thread(update: Update,chat_id :str,user_message: str,username :str,context: CallbackContext) -> None:
        try:
            # Send the initial "responding..." message
            prompt = f"{user_message}"
            context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

            # Generate the response
            response =generate_response(chat_id,prompt)

            if hasattr(response, "text"):
                # Code that might raise the AttributeError (e.g., accessing the 'text' attribute of a variable)
                html_response = markdown_to_telegram_html(response.text)  
                logger.info(f"Prompt({chat_id}): {prompt}\n\n\nResponse: \n{html_response}")
                

               


                chunks = textwrap.wrap(html_response, width=3500, break_long_words=False, replace_whitespace=False)


                for chunk in chunks:
                    update.message.reply_text(chunk, parse_mode='html')

            else:
                update.message.reply_text(
                    f"<b>My apologies</b>, I've reached my <i>usage limit</i> for the moment. ⏳ Please try again in a few minutes. \n\n<i>Response :</i> {response}",
                    parse_mode='HTML'
                )
                logger.error(f"quato error!\n\nreponse:{response}")










        except Exception as e:
            logger.error(f"Error processing message: {e}")
            try:
                update.message.reply_text(f"Sorry, I encountered an error while processing your message.\n error:{e}")
            except Exception:  # If the original message couldn't be edited
                logger.error("Error cant send the message")


def markdown_to_telegram_html(markdown_text):
    """Converts Markdown-like text to Telegram-compatible HTML."""
    html = markdown.markdown(markdown_text, extensions=[Nl2BrExtension()])

    # Remove unsupported tags (headings, blockquotes, etc.)
    unsupported_tags = ["h\d", "blockquote"]
    for tag in unsupported_tags:
        html = re.sub(rf"<{tag}>.*?</{tag}>", "", html, flags=re.DOTALL)

    # Replace paragraph tags with empty string
    html = html.replace("<p>", "").replace("</p>", "")

    # Convert lists to '-' or '*' (MarkdownV2 style)
    html = re.sub(r"<ul>|</ul>|<ol>|</ol>", "", html)
    html = re.sub(r"<li>", "<b>- </b>", html)
    html = re.sub(r"</li>", "", html)

    # Replace <br> and <hr> tags with appropriate newline characters
    html = re.sub(r"<br\s*/?>", "\n", html)
    html = re.sub(r"<hr\s*/?>", "\n\n", html)

    return html


def help_command(update: Update, context: CallbackContext) -> None:
  """Send a well-formatted help message with links to Gemini and Ares status."""

  logger.info(f"help command asked by :{update.message.from_user.username}")
  update.message.reply_text(help_text, parse_mode='HTML', disable_web_page_preview=True)

def start(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    username = user.first_name if user.first_name else user.username if user.username else "there"

    welcome_message = f"Hello {username}! I'm Ares, your AI assistant. How can I help you today?"

    keyboard = [
        [InlineKeyboardButton("Help", callback_data='help')],
        [InlineKeyboardButton("Contact Owner", callback_data='contact')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(welcome_message, reply_markup=reply_markup)

def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    if query.data == 'help':
        help_message = help_text
        query.edit_message_text(text=help_message, parse_mode='HTML')
    elif query.data == 'contact':
        contact_message = "You can contact the owner at @Rkgroup5316. or join https://t.me/AresChatBotAi for info and bug reports ."
        query.edit_message_text(text=contact_message)

def clear_history(update: Update, context: CallbackContext) -> None:
    """Clear the chat history for the current chat."""
    try:
        chat_id = update.message.chat_id
        if chat_id in chat_histories:
            # Clear the chat history and start a new one with the default prompt
            chat_histories[chat_id] = model.start_chat(history=[])
            update.message.reply_text("Chat history successfully cleared.")
        else:
            update.message.reply_text("There is no chat history to clear.")
    except Exception as e:
        update.message.reply_text(f"An error occurred while clearing the chat history: {e}")
        logger.error(f"An error occurred while clearing the chat history: {e}")


def history(update: Update, context: CallbackContext) -> None:
    args = context.args
    chat_id = update.message.chat_id

    try:
        if args:
            # If argument is provided, check if it's a valid chat ID
            try:
                arg_chat_id = int(args[0])
            except ValueError:
                update.message.reply_text("Invalid chat ID. Please provide a valid integer ID.")
                return

            if arg_chat_id in chat_histories:
                # If provided chat ID is in active sessions, retrieve its history
                history_text = f"Chat history for chat ID {arg_chat_id}:\n{chat_histories[arg_chat_id].history}"
                chunks = textwrap.wrap(history_text, width=100 * 4, replace_whitespace=False)  # ~400 characters
                for chunk in chunks:
                    update.message.reply_text(chunk, parse_mode='html')
            else:
                update.message.reply_text("Error 404: Chat ID not found.")
        else:
            # If no argument is provided, retrieve history for the current session chat
            if chat_id in chat_histories:
                history_text = f"Chat history:\n{chat_histories[chat_id].history}"
                chunks = textwrap.wrap(history_text, width=100 * 4, replace_whitespace=False)  # ~400 characters
                for chunk in chunks:
                    update.message.reply_text(chunk, parse_mode='html')
            else:
                update.message.reply_text("There is no chat history.")
    except Exception as e:
        update.message.reply_text(f"An error occurred while retrieving the chat history: {e}")
        logger.error(f"An error occurred while retrieving the chat history: {e}")

def process_image(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    chat_seesion = get_chat_history(chat_id)
    context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)


    def handle_image():
        try:
            if update.message.photo:
                user_message = update.message.caption if update.message.caption else ""

                file_id = update.message.photo[-1].file_id
                file = context.bot.get_file(file_id)
                file_path = file.download()
                img = PIL.Image.open(file_path)



                try:  # Error handling for image processing
                    response = chat_seesion.send_message([user_message, img])
                except genai.GenAiException as e:
                    logger.error(f"Gemini Error (Image Processing): {e}")
                    update.message.reply_text("Sorry, I had trouble processing the image.")
                    return
                  
                if hasattr(response, "text"):
                  update.message.reply_text(response.text)
                else:
                  update.message.reply_text(
                      f"<b>My apologies</b>, I've reached my <i>usage limit</i> for the moment. ⏳ Please try again in a few minutes. \n\n<i>Response :</i> {response}",
                      parse_mode='HTML'
                  )
                  logger.error(f"quato error!\n\nreponse:{response}")

                os.remove(file_path)
        except (PIL.UnidentifiedImageError, FileNotFoundError) as e:
            logger.error(f"Image Error: {e}")
            update.message.reply_text("Sorry, there was an issue with the image you sent.")
        except Exception as e:
            logger.error(f"Unexpected Error: {e}")
            update.message.reply_text("Sorry, something went wrong. Please try again later.")

    threading.Thread(target=handle_image).start()

def Token(update: Update, context: CallbackContext) -> None:
    args = context.args
    chat_id = update.message.chat_id

    if args:
        # If argument is provided, check if it's a valid chat ID
        try:
            arg_chat_id = int(args[0])
        except ValueError:
            update.message.reply_text("Invalid chat ID. Please provide a valid integer ID.")
            return

        if arg_chat_id in chat_histories:
            # If provided chat ID is in active sessions, retrieve its token count
            chat_session = chat_histories[arg_chat_id]
            update.message.reply_text(f'Total tokens used for chat ID {arg_chat_id}: {model.count_tokens(chat_session.history)}', parse_mode='html')
        else:
            update.message.reply_text("Error 404: Chat ID not found.")
    else:
        # If no argument is provided, retrieve token count for the current session chat
        chat_session = get_chat_history(chat_id)
        update.message.reply_text(f'Total tokens used in current session: {model.count_tokens(chat_session.history)}', parse_mode='html')

def session_command(update: Update, context: CallbackContext) -> None:
    """Reports the total number of open chat sessions after password check."""
    args = context.args

    if not args:  # No arguments provided
        update.message.reply_text("Access denied. Please provide the password: `/session [password]`")
        return

    if len(args) != 1 or args[0] != PASSWORD:  # Incorrect password or extra arguments
        update.message.reply_text("Access denied. Incorrect password.",parse_mode='html')
        return

    total_sessions = len(chat_histories)
    if total_sessions == 0:
        update.message.reply_text("There are no active chat sessions.",parse_mode='html')
    else:
        session_message = f"There are currently <b>{total_sessions}</b> active chat sessions."
        update.message.reply_text(session_message, parse_mode='html')
      
def session_info_command(update: Update, context: CallbackContext) -> None:
    """Reports the list of chat IDs for active chat sessions after password check."""
    args = context.args

    if not args:  # No arguments provided
        update.message.reply_text("Access denied. Please provide the password: `/session_info [password]`")
        return

    if len(args) != 1 or args[0] != PASSWORD:  # Incorrect password or extra arguments
        update.message.reply_text("Access denied. Incorrect password.", parse_mode='html')
        return

    active_chat_ids = list(chat_histories.keys())  # Get the list of chat IDs for active chat sessions
    if not active_chat_ids:
        update.message.reply_text("There are no active chat sessions.", parse_mode='html')
    else:
        session_message = f"The active chat sessions have the following chat IDs: {', '.join(str(chat_id) for chat_id in active_chat_ids)}"
        update.message.reply_text(session_message, parse_mode='html')

def main() -> None:
    logger.info("Bot starting!")
    updater = Updater(telegram_bot_token, use_context=True)
    dispatcher = updater.dispatcher

    # Register the message handler
    message_handler = MessageHandler(Filters.text & ~Filters.command, process_message)
    dispatcher.add_handler(message_handler)

    # Register the message handler
    dispatcher.add_handler(MessageHandler(Filters.photo, process_image))


    # Register the help command handler
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(button))
    dispatcher.add_handler(CommandHandler("history", history))

    # Register the help command handler
    dispatcher.add_handler(CommandHandler("token", Token))
    dispatcher.add_handler(CommandHandler("session", session_command))
    dispatcher.add_handler(CommandHandler("session_info", session_info_command))


    # Register the ChangePrompt command handler
    dispatcher.add_handler(CommandHandler("clear_history", clear_history, pass_args=True))
    dispatcher.add_handler(CommandHandler("ChangePrompt", change_prompt, pass_args=True))



    logger.warning("Bot started!")


    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    keep_alive()
    main()






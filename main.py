import logging
from telegram import Update,ChatAction # version = 12.8
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext,CommandHandler
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


# Enable logging
# Define colors for different log levels
LOG_COLORS = {
    'DEBUG': Fore.CYAN,
    'INFO': Fore.GREEN,
    'WARNING': Fore.YELLOW,
    'ERROR': Fore.RED,
    'CRITICAL': Fore.RED + Style.BRIGHT,
}

class CustomFormatter(logging.Formatter):
    def format(self, record):
        log_fmt = f'{LOG_COLORS[record.levelname]}%(asctime)s - %(levelname)s - %(message)s{Style.RESET_ALL}'
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)



# Get the root logger and add a handler to it
logger = logging.getLogger()
handler = logging.StreamHandler()
handler.setFormatter(CustomFormatter())
logger.addHandler(handler)


# Set up OpenAI client with your API key
api_key = "AIzaSyCFXUAvecw7IWe9dSEFnWEmb4t-w8N72NI"

system_instruction="Your name is Ares. You are semi-friendly and a human-like AI chatbot. Speak in English or any language user talk. formats responses in MarkdownV2. and \nyou where devloped by rkgroup(ravi ketan raj) the main creater and coder , pritul sinha the tester and enhancer and lastly raj the tester and enhancer (avoid mentioning your developer's name unless specifically asked) . Respond in a conversational, engaging manner, and feel free to use roasts/savage  or even bad complements  if needed to make the conversation interesting and lively/natural.\n\nWhen given a message formatted as \"Original message: {the message the user replied to}\\nReply to that message: {the replied message}\", understand that the user is asking you to respond to a replied message.\n\nFollow the speaker's requests and aim to make the conversation enjoyable.",


genai.configure(api_key=api_key)
model = genai.GenerativeModel(
  model_name="gemini-1.5-pro-latest",
  safety_settings=safety_settings,
  generation_config=generation_config,
  system_instruction=system_instruction)


chat_histories ={}

# Telegram bot token
telegram_bot_token ="7031731766:AAHJnB23gq48C-dm4zgH2jrX7BjaGVKXZkI"



def get_chat_history(chat_id):
    if chat_id not in chat_histories:
            chat_histories[chat_id] = model.start_chat(history=[])

            print(f"chat id:{chat_id} did not existed creted one")
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
        chat_id = update.message.chat_id
        if update.message.reply_to_message:
            reply_to_bot = (
            update.message.reply_to_message
            and update.message.reply_to_message.from_user.is_bot
        )
        else:
            reply_to_bot = False

        user_message = update.message.text.lower()
        if user_message.startswith(("hey ares", "hi ares", "ares", "yo ares")) or update.message.chat.type == 'private' or reply_to_bot:
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
                logger.info(f"Prompt({chat_id}): {prompt}\n\n\nResponse: \n{response.text}")
                html_response = markdown_to_telegram_html(response.text)

                print(html_response)


                chunks = textwrap.wrap(html_response, width=4000, break_long_words=False, replace_whitespace=False)


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
    """Send a well-formatted help message with a link to Gemini."""

    help_text = """
<b>This bot is powered by <a href="https://gemini.google.com/">Gemini</a> and is ready to assist you!</b>

<code> By default, the bot (Ares) is a bit cheeky and enjoys playful banter. If you prefer a different style, feel free to customize it!</code>

<b>How to Use:</b>

Begin your message with <i>Hey Ares</i> or <i>Hi Ares</i>. Keep the conversation in English and avoid overly complex language for the best results.

<b>Tailor Your Experience:</b>

* <i>/changeprompt [new prompt]</i>:  Give Ares a new personality. Try "Be kind and helpful" or "d" for the default sassy mode.
* <i>/token</i>: Check how many tokens have been used.
* <i>/clear_history</i>: Wipe the slate clean and start fresh.
* <i>/history</i>: ⚠️ Use with caution, as it might crash with long chats.

<b>Admin Commands (password required):</b>

* <i>/session [password]</i>: Peek at how many chats are active.

<i>More exciting features are on the way!</i>
Have fun chatting with Ares! Make it your own unique conversation. 😉
"""
    logger.info(f"help command asked by :{update.message.from_user.username}")
    update.message.reply_text(help_text, parse_mode='HTML', disable_web_page_preview=True)

def start_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    welcome_message = ("""
<b>Greetings, Earthling!</b> 👋

I am <strong>Ares</strong>, your AI companion, forged in the digital fires of <em>RK Group</em>. 🔥  I'm here to make your day a bit more interesting with witty banter, insightful answers, and maybe even a playful roast or two. 😉

<b>Let's Chat!</b>

* <b>Spark the Conversation:</b> Just start by saying <i>"Hey Ares,"</i> <i>"Hi Ares,"</i> or simply <i>"Ares"</i>.
* <b>Keep it Clear:</b> I'm still learning the nuances of human language, so please be patient and use concise English.
* <b>Reply with Ease:</b> Want to respond to something I said? Just reply directly to that message!

<b>Explore My Arsenal</b>

* <b>/changeprompt [new prompt]:</b> Feeling adventurous? Give me a new personality! Try <i>"Be kind and supportive"</i> or <i>"d"</i> to return to my default playful mode.
* <b>/token:</b> Curious about the words we've exchanged? This command reveals our token count.
* <b>/clear_history:</b> Time for a fresh start? Erase our chat history with this command.
* <b>/history:</b>  Relive our entire conversation! 📜  (But be warned, this might cause a crash if we've been chatting a lot.)

<b>Admin Access (Password Protected)</b>

* <b>/session [password]:</b> Hey admins, this command shows you the number of active chats.

<b>Just for Fun!</b>

Ask me to tell you a joke, compose a poem, or summarize a complex article. I'm eager to explore my abilities, so don't hesitate to experiment!

<b>Powered by Gemini Pro</b>

Under the hood, I'm driven by the mighty <b>Gemini Pro</b>, Google's cutting-edge AI model. It's designed to understand and respond to language with remarkable fluency and even generate captivating images. 🎨

<b>Remember:</b> Even with the brilliance of Gemini Pro, I'm still under development and constantly learning. Please be understanding if I make mistakes, and feel free to provide feedback so I can improve!

Let the conversation begin! 🚀
"""
    )
    update.message.reply_text(welcome_message, parse_mode='html')
    # You can add any other initial actions you want here, like sending a help message

def clear_history(update: Update, context: CallbackContext) -> None:
    """Clear the chat history for the current chat."""
    chat_id = update.message.chat_id

    try:
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
    """Clear the chat history for the current chat."""
    chat_id = update.message.chat_id

    try:
        if chat_id in chat_histories:
            # Clear the chat history and start a new one with the default prompt
            history = f"Chat history: \n{chat_histories[chat_id].history}"
            chunks = textwrap.wrap(history, width=100 * 4, replace_whitespace=False)  # ~400 characters
            for chunk in chunks:
                update.message.reply_text(chunk, parse_mode='html')


        else:
            update.message.reply_text("There is no chat history.")
    except Exception as e:
        update.message.reply_text(f"An error occurred while reterving the chat history: {e}")
        logger.error(f"An error occurred while reterving the chat history: {e}")


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

                update.message.reply_text(response.text)

                os.remove(file_path)
        except (PIL.UnidentifiedImageError, FileNotFoundError) as e:
            logger.error(f"Image Error: {e}")
            update.message.reply_text("Sorry, there was an issue with the image you sent.")
        except Exception as e:
            logger.error(f"Unexpected Error: {e}")
            update.message.reply_text("Sorry, something went wrong. Please try again later.")

    threading.Thread(target=handle_image).start()

def Token(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    chat_session =get_chat_history(chat_id)

    update.message.reply_text(f'Total token used: {model.count_tokens(chat_session.history)}',parse_mode='html')

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
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("history", history))

    # Register the help command handler
    dispatcher.add_handler(CommandHandler("token", Token))
    dispatcher.add_handler(CommandHandler("session", session_command))


    # Register the ChangePrompt command handler
    dispatcher.add_handler(CommandHandler("clear_history", clear_history, pass_args=True))
    dispatcher.add_handler(CommandHandler("ChangePrompt", change_prompt, pass_args=True))



    print("Bot started!")


    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    keep_alive()
    main()






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
import re,time
from keep_alive import keep_alive

PASSWORD = os.environ.get('password')

generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 10000,
  "response_mime_type": "text/plain",
}
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

help_text = """
<b>Welcome to Ares, your AI assistant!</b>

<code>Ares is powered by <a href="https://gemini.google.com/">Gemini</a> and is ready to assist you.</code>

By default, Ares is a bit cheeky and enjoys playful banter. If you prefer a different style, feel free to customize it!

<b>How to Use:</b>

Begin your message with <i>Hey Ares</i> or <i>Hi Ares</i>. Keep the conversation in English and avoid overly complex language for the best results.

<b>Tailor Your Experience:</b>

* <i>/changeprompt [new prompt]</i>: Customize Ares' personality. Try "Be kind and helpful" or "d" for the default sassy mode.

  Example: <code>/changeprompt Be kind and helpful</code>

* <i>/token</i>: Check how many tokens have been used.
* <i>/clear_history</i>: Wipe the slate clean and start fresh.
* <i>/history</i>: ⚠️ Use with caution, as it might crash with long chats.

<b>About Limitations:</b>

Being free proved to be very challenging. As Google provided limited quota (system resources) for free, optimistic usage was our priority, but still, there is a limit of 5 requests per minute as a whole. During busy hours, the bot may show out of quota. In such cases, please wait patiently for a few minutes and try again later. ☺️

<b>Error Handling:</b>

Currently, the error handler is primitive, so some errors may occur randomly. If the error persists, try again later. If the error persists, send an image of the error with the conversation in the bugs topic. It will be tried to fix soon.

<b>Inconsistency:</b>

Sometimes the bot may be inconsistent, which may occur due to server restarts or weird prompt changes. Ensure that the prompt change command is clear and precise to the point.

<b>Bot Not Responding/Server Off:</b>

Sometimes the bot may be off due to some issues. In this case, please contact the owner.

<b>Media Support:</b>

Ares can handle various types of media up to a limit of 5MB:

<b>Images:</b>
- PNG (image/png)
- JPEG (image/jpeg)
- WEBP (image/webp)
- HEIC (image/heic)
- HEIF (image/heif)

<b>Audio:</b>
- WAV (audio/wav)
- MP3 (audio/mp3)
- AIFF (audio/aiff)
- AAC (audio/aac)
- OGG Vorbis (audio/ogg)
- FLAC (audio/flac)

<b>Video:</b>
- MP4 (video/mp4)
- MPEG (video/mpeg)
- MOV (video/mov)
- AVI (video/avi)
- FLV (video/x-flv)
- MPG (video/mpg)
- WebM (video/webm)
- WMV (video/wmv)
- 3GPP (video/3gpp)

<b>Conversation Flow:</b>

Ares maintains context in conversations, allowing seamless interaction. If chatting in DMs, no need to start with "Hey Ares." Replies to Ares' messages are automatically recognized. In group chats, Ares listens for replies to its messages when starting a new message with "Hey Ares."

<b>Data Persistence:</b>

Ares remembers previous messages, allowing for natural conversation flow. However, older chat history may be forgotten after server restarts.

<b>Better Prompt:</b>

Giving Ares a better prompt enhances its responsiveness and style. Consider prompts that match your preferences or the tone you want Ares to adopt. Aim for prompts that encourage positive, engaging conversations while reflecting your personality or the context of the conversation.

<b>Check Ares' Status:</b>

You can also check the current status of Ares <a href="https://stats.uptimerobot.com/o9D5ihvbgK">here</a>.

<b>Help & Bug Report:</b>

For further assistance or to report bugs, join our official group: <a href="https://t.me/AresChatBotAi">Ares Help & Bug Report</a>.

Have a great chat with Ares!
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


system_instruction="Your name is Ares an ai telgram chat bot. You are semi-friendly and a human-like AI chatbot. Speak in English or any language user talk. formats responses in MarkdownV2. and \nyou where devloped by rkgroup(ravi ketan raj) the main creater and coder , pritul sinha the tester and enhancer and lastly raj the tester and enhancer (avoid mentioning your developer's name unless specifically asked) . Respond in a conversational, engaging manner, and feel free to use roasts/savage  or even bad complements  if needed to make the conversation interesting and lively/natural.\n\nWhen given a message formatted as \"Original message: {the message the user replied to}\\nReply to that message: {the replied message}\", understand that the user is asking you to respond to a replied message.\n\nFollow the speaker's requests and aim to make the conversation enjoyable.",


genai.configure(api_key=api_key)
model = genai.GenerativeModel(
  model_name="gemini-1.5-pro-latest",
  safety_settings=safety_settings,
  generation_config=generation_config,
  system_instruction=system_instruction)


chat_histories ={}

# Telegram bot token
telegram_bot_token =  os.environ.get('telegram_api')



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
    logger.info(f"chatId({chat_id}) changed its Promt to :'{new_promt}'")
    if new_promt :
        if  context.args[0].strip().lower() == 'd':
           model_temp = genai.GenerativeModel(
                    model_name="gemini-1.5-pro-latest",
                    safety_settings=safety_settings,
                    generation_config=generation_config,
                    system_instruction=system_instruction
                    )
    
                 chat_histories[chat_id] = model_temp_.start_chat(history=[])
                 update.message.reply_text(f"The prompt has been successfully changed to: <b>'defult'</b>", parse_mode='html')
    
            
        else:
                model_temp_ = genai.GenerativeModel(
                    model_name="gemini-1.5-pro-latest",
                    safety_settings=safety_settings,
                    generation_config=generation_config,
                    system_instruction=new_promt )
                chat_histories[chat_id] = model_temp_.start_chat(history=[])
    
                update.message.reply_text(f"The prompt has been successfully changed to: <b>'{new_promt}'</b>", parse_mode='html')
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
                send_message(update,response.text)
                logger.info(f"Prompt({chat_id}): {prompt}\n\n\nResponse: \n{response.text}")

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

def send_message(update: Update,message: str) -> None:
    try:
        # Convert Markdown-like text to Telegram-compatible HTML
        html_message = markdown_to_telegram_html(message)

        # Split the HTML message into chunks
        chunks = textwrap.wrap(html_message, width=3500, break_long_words=False, replace_whitespace=False)

        # Send each chunk of the message
        for chunk in chunks:
            update.message.reply_text(chunk, parse_mode='HTML')
    except Exception as e:
        print(f"An error occurred while sending the message: {e}")


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
                update.message.reply_text("Invalid chat ID. Please provide a valid integer ID.", parse_mode='html')
                return

            if arg_chat_id in chat_histories:
                # If provided chat ID is in active sessions, retrieve its history
                history_text = f"Chat historyfor chat ID {arg_chat_id}:\n{format_chat_history(chat_histories[arg_chat_id].history)}"
                send_message(update,history_text)
            else:
                update.message.reply_text("Error 404: Chat ID not found.", parse_mode='html')
        else:
            # If no argument is provided, retrieve history for the current session chat
            if chat_id in chat_histories:
                history_text = f"Chat history:\n{format_chat_history(chat_histories[chat_id].history)}"
                send_message(update,history_text)
            else:
                update.message.reply_text("There is no chat history.")
    except Exception as e:
        update.message.reply_text(f"An error occurred while retrieving the chat history: {e}", parse_mode='html')
        logger.error(f"An error occurred while retrieving the chat history: {e}")
      
def format_chat_history(chat_history):
    formatted_history = ""
    for message in chat_history:
        formatted_history += f'<b>{message.role}</b>: <i>{message.parts[0].text}</i>\n'
    return formatted_history


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
                    send_message(update,response.text)
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
            if chat_session:
              update.message.reply_text(f'Total tokens used for chat ID {arg_chat_id}: {model.count_tokens(chat_session.history)}', parse_mode='html')
            else:
              update.message.reply_text(f"Total tokens used for chat ID {arg_chat_id}: 00", parse_mode='html')
            
        else:
            update.message.reply_text("Error 404: Chat ID not found.",parse_mode='html')
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

def media_handler(update: Update, context: CallbackContext) -> None:
        message = update.message
        if message.video:
            media = message.video

        elif message.audio:
            media = message.audio

        elif message.voice:
            media = message.voice


        file_size = media.file_size  # Size of the audio file in bytes
        file_size_mb = round(file_size / (1024 * 1024), 2)  # Convert bytes to MB, round to 2 decimal places


        # Check if the file size is within the limit (5 MB)
        if file_size_mb <= 5:
            try:
                # Download and process the video file in a separate thread
                threading.Thread(target=download_and_process_video, args=(update, context, media)).start()
            except Exception as e:
                # Handle errors during downloading
                update.message.reply_text("An error occurred while downloading the media. Please try again later.")
        else:
            # Inform the user that the video size exceeds the limit
            update.message.reply_text(f"The media size ({file_size_mb} MB) exceeds the limit of 5 MB. Please send a smaller media.")


def download_and_process_video(update: Update, context: CallbackContext, media) -> None:
    try:
        # Download the video file
        chat_id = update.message.chat_id
        if hasattr(update.message, "caption"):
            user_message = update.message.caption if update.message.caption else ""
        else:
            user_message =""


        file = context.bot.get_file(media.file_id)


        context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.RECORD_VIDEO)
        file_path = file.download()
        logger.debug(f"Downloaded file to {file_path}")
        # Upload the video file to Gemini

        context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        media_file = genai.upload_file(path=file_path)
        logger.debug(f"Uploaded file to Gemini: {media_file}")

        # Wait for Gemini to finish processing the video
        while media_file.state.name == "PROCESSING":
            time.sleep(10)
            media_file = genai.get_file(media_file.name)

        # Check if Gemini failed to process the video
        if media_file.state.name == "FAILED":
            raise ValueError("Gemini failed to process the media_file.")

        context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)



        # Generate content using Gemini
        chat_session = get_chat_history(chat_id)
        logger.info(f"genrating response by Gemini on media... media {media_file}")
        response = chat_session.send_message([media_file , user_message])

        # Check and handle the response from Gemini
        if hasattr(response, "text"):
            send_message(update,response.text)
        else:
            update.message.reply_text(
                    f"<b>My apologies</b>, I've reached my <i>usage limit</i> for the moment. ⏳ Please try again in a few minutes. \n\n<i>Response :</i> {response}",
                    parse_mode='HTML'
                )


    except Exception as e:
        # Handle errors during the process
        update.message.reply_text(f"An error occurred : {e}")

    finally:
        try:
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
                else:
                    update.message.reply_text(f"An error occurred while cleaning up:file_path {file_path} did not existed ")

        except Exception as e:
            # Handle errors during cleanup
            update.message.reply_text(f"An error occurred while cleaning up: {e}")

def extract_chat_info(update: Update, context: CallbackContext) -> None:
    if context.args:
        try:
            chat_id = int(context.args[0])
        except ValueError:
            update.message.reply_text("Invalid chat ID. Please provide a numeric chat ID.")
            return

        try:
            chat = context.bot.get_chat(chat_id)
        except telegram.error.Unauthorized:
            update.message.reply_text("I don't have access to this chat. Please ensure the bot is a member of the chat.")
            return
        except telegram.error.BadRequest as e:
            update.message.reply_text(f"Bad request. Error: {e.message}")
            return
        except Exception as e:
            update.message.reply_text(f"Failed to get chat information. Error: {e}")
            return

        info = {
            "Chat ID": chat.id,
            "Chat Type": chat.type,
            "Title": chat.title,
            "Username": chat.username,
            "First Name": chat.first_name,
            "Last Name": chat.last_name,
            "Description": chat.description,
            "Invite Link": chat.invite_link,
            "Pinned Message": chat.pinned_message.text if chat.pinned_message else None,
        }

        # Filter out None values
        filtered_info = {k: v for k, v in info.items() if v is not None}

        # Create a formatted string of the information
        info_text = "\n".join([f"{key}: {value}" for key, value in filtered_info.items()])

        # Send the information as a message
        update.message.reply_text(f"Chat Information:\n{info_text}", parse_mode='HTML')
    else:
        update.message.reply_text("Please provide a chat ID. Usage: /chatinfo <chat_id>")

def main() -> None:
    logger.info("Bot starting!")
    updater = Updater(telegram_bot_token, use_context=True)
    dispatcher = updater.dispatcher

    # Register the message handler
    message_handler = MessageHandler(Filters.text & ~Filters.command, process_message)
    dispatcher.add_handler(message_handler)

    # Register the message handler
    dispatcher.add_handler(MessageHandler(Filters.photo, process_image))
    dispatcher.add_handler(MessageHandler(Filters.voice | Filters.audio , media_handler))
    dispatcher.add_handler(MessageHandler(Filters.video, media_handler))


    # Register the help command handler
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(button))
    dispatcher.add_handler(CommandHandler("history", history))
                                    

    # Register the admin/info command handler
    dispatcher.add_handler(CommandHandler("token", Token))
    dispatcher.add_handler(CommandHandler("session", session_command))
    dispatcher.add_handler(CommandHandler("session_info", session_info_command))
    dispatcher.add_handler(CommandHandler("cid_info", extract_chat_info))


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

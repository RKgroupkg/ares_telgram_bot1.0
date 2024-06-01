import logging,telegram
from telegram import Update,ChatAction,InlineKeyboardMarkup, InlineKeyboardButton # version = 12.8
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext,CommandHandler,CallbackQueryHandler
import google.generativeai as genai
import threading
import textwrap
import PIL.Image
import os
import format_html
import time,datetime
import config

import firebase_admin
from firebase_admin import db, credentials
import jsonpickle # type: ignore

cred = credentials.Certificate("ares-rkbot-firebase-adminsdk-s8z98-7a3c805c5a.json")
app = firebase_admin.initialize_app(cred, {"databaseURL": "https://ares-rkbot-default-rtdb.asia-southeast1.firebasedatabase.app/"})

PASSWORD = "ares100"

chat_histories ={}

api_key = "AIzaSyCFXUAvecw7IWe9dSEFnWEmb4t-w8N72NI" # Set up gemnie client with your API key
api_key2 = "AIzaSyBxCSoLIi6gsLCDLG25cdubonZafdNF4pI"
genai.configure(api_key=api_key)
telegram_bot_token = "6680622532:AAFtdp3fB_OKrlq-BZTRp7X31I8bgrACKjI"


logger = logging.getLogger()
handler = logging.StreamHandler()
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(process)d - %(levelname)s - %(threadName)s - %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)

model = genai.GenerativeModel(
  model_name="gemini-1.5-pro-latest",
  safety_settings=config.safety_settings,
  generation_config=config.generation_config,
  system_instruction=config.system_instruction,)

class FireBaseDB:
    def __init__(self):
        self.db = db.reference("/users_sessions")
        self.INFO_DB = db.reference("/Blocked_user")
    
    def user_exists(self,userId):

        try:
           return db.reference(f"/users_sessions/{userId}").get()
        except Exception as e:
            raise ValueError(f"error while checking for user :{e}")

    def create_user(self,userId):
        user_data = self.user_exists(userId)
        if user_data:
            raise ValueError(f"User with ID '{userId}' already exists!")
        
        now = datetime.datetime.now()
        formatted_time = now.strftime("%Y-%m-%dT%H:%M:%SZ")  # ISO 8601 format


        conversation = {
            "chat_session":{},
            "date" : formatted_time,
            "system_instruction" : "default"
        }
        db.reference(f"/users_sessions").update({f"{userId}":conversation })
        
        
    def extract_history(self,userId):
       
        try:
            user_data = self.user_exists(userId)
            if not user_data:
                raise ValueError(f"User with ID '{userId}' not found")

            
            return jsonpickle.decode(user_data.get("chat_session"))

        except (KeyError, AttributeError) as e:
            raise ValueError(f"Error accessing user data or conversation: {e}")

    def chat_history_add(self,userId, history=[]):
        """Adds the provided history to the chat session for the user.

        Args:
            history (list, optional): The list of messages to add to the conversation history. Defaults to [].
            update_all (bool, optional): If True, replaces the entire chat session history. Defaults to true (appends).

        Raises:
            ValueError: If user ID is not found in the database.
        """

        try:
            db.reference(f"/users_sessions/{userId}").update({f"chat_session":jsonpickle.encode(history, True)})

        except (KeyError, AttributeError) as e:
            raise ValueError(f"Error accessing user data or chat session: {e}")
    
    def extract_instruction(self,userId):
        user_data =  self.user_exists(userId)
        if not user_data:
            raise ValueError(f"User with ID '{userId}' not found")

        return user_data["system_instruction"]

    def Update_instruction(self,userId,new_instruction = "default"):
        db.reference(f"/users_sessions/{userId}").update({f"system_instruction":new_instruction })



    def info(self,userId):
            user_data =  self.user_exists(userId)
            if not user_data:
                raise ValueError(f"User with ID '{userId}' not found")
            
            message = f''' 

userID :          {userId}
creation date :   {user_data["date"]}
Prompt :          {user_data["system_instruction"]}

    '''
            return message



    
     
def get_chat_history(chat_id):
    """Retrieves chat history for the given chat ID.

    Args:
        chat_id (int): The unique identifier of the chat.

    Returns:
        GenerativeModel: The Generative AI model instance with chat history.

    Raises:
        RuntimeError: If there's an error retrieving data from the cloud.
    """
    # Check if chat history exists locally
    if chat_id in chat_histories:
        return chat_histories[chat_id]  # Return existing history

    # If not found locally, try retrieving from cloud
    try:
        userData = DB.user_exists(chat_id)
        if userData:
            instruction = userData['system_instruction']

            if instruction =='default':
                instruction = config.system_instruction            
            
            model_temp = genai.GenerativeModel(
                model_name="gemini-1.5-pro-latest",
                safety_settings=config.safety_settings,
                generation_config=config.generation_config,
                system_instruction=instruction
            )
            history=jsonpickle.decode(userData['chat_session'])   # decode history and then store
            logger.debug(f"History :{history}")

            chat_histories[chat_id] = model_temp.start_chat(history=history )
            logger.info(f"Chat id:{chat_id} did not exist locally, got previous data from cloud")
            return chat_histories[chat_id]  # Return retrieved history
        else:
            # User doesn't exist in cloud, create a new one
            DB.create_user(chat_id)
            chat_histories[chat_id] = model.start_chat(history=[] )
            logger.info(f"Chat id:{chat_id} did not exist, created one")
            return chat_histories[chat_id]  # Return new model

    except Exception as e:
        # Handle errors during cloud data retrieval
        logger.error(f"Error retrieving chat history for chat_id: {chat_id}, Error: {e}")



# Function to generate response using gemnie
def generate_response(chat_id, input_text: str) -> str:
    chat_history = get_chat_history(chat_id)
    logger.info("Generating response...")
    try:
        response = chat_history.send_message(input_text)

        def update():
            try:
                with lock:  # Use a thread-safe lock for Firebase access
                    DB.chat_history_add(chat_id, chat_history.history)
                return response if input_text else "error"
            except Exception as e:
                logger.error(f"Sorry, I couldn't generate a response at the moment. Please try again later.\n\nError: {e}")
                return f"Sorry, I couldn't generate a response at the moment. Please try again later.\n\nError: {e}"

        # Create a lock to ensure only one thread updates Firebase at a time
        lock = threading.Lock()

        # Create a thread to update Firebase asynchronously in the background
        thread = threading.Thread(target=update)
        thread.start()
        return response

    except Exception as e:
            logger.error(f"Sorry, I couldn't generate a response at the moment. Please try again later.\n\nError: {e}")
            return f"Sorry, I couldn't generate a response at the moment. Please try again later.\n\nError: {e}"





def change_prompt(update: Update, context: CallbackContext) -> None:
    """Change the prompt for generating responses."""
    chat_id = update.message.chat_id
    new_promt = " ".join(context.args)
    logger.info(f"chatId({chat_id}) changed its Promt to :'{new_promt}'")
    if new_promt :
        print(f"arg in lower case :{context.args[0].lower()} is it command? :{context.args[0].lower() == 'd'} ")
        if  context.args[0].lower() == 'd':
        
           chat_histories[chat_id] = model.start_chat(history=[] )
           update.message.reply_text(f"The prompt has been successfully changed to: <b>'default'</b>", parse_mode='HTML')
           DB.Update_instruction(chat_id)
           
            
        else:
                model_temp = genai.GenerativeModel(
                    model_name="gemini-1.5-pro-latest",
                    safety_settings=config.safety_settings,
                    generation_config=config.generation_config,
                    system_instruction=new_promt )
                chat_histories[chat_id] = model_temp.start_chat(history=[])
    
                update.message.reply_text(f"The prompt has been successfully changed to: <b>'{new_promt}'</b>", parse_mode='HTML')
                DB.Update_instruction(chat_id,new_promt)
        DB.chat_history_add(chat_id,[])
    else:
            update.message.reply_text(f"Error ! un sufficent info provided", parse_mode='HTML')




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
                threading.Thread(target=process_message_thread, args=(update,chat_id, user_message,context)).start()
            else:
                threading.Thread(target=process_message_thread, args=(update,chat_id, user_message,context)).start()

            if username:
                logger.info(f"{username}: {user_message}")
            else:
                logger.info(f"Someone: {user_message}")


def process_message_thread(update: Update,chat_id :str,user_message: str,context: CallbackContext) -> None:
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

def send_message(update: Update,message: str,format = True) -> None:
    try:

        def send_wrap(message_ :str):
            chunks = textwrap.wrap(message_, width=3500, break_long_words=False, replace_whitespace=False)
            for chunk in chunks:
                update.message.reply_text(chunk, parse_mode='HTML')



        if format:
            try:
                html_message = format_html.format_message(message)
                send_wrap(html_message)
                
            except Exception as e:
                logger.warning(f"Using (markdown_to_telegram_html) functon because (format_message) cant parse the response error:{e}")
                html_message = format_html.markdown_to_telegram_html(message)
                send_wrap(html_message)
        else:
            logger.warning("sending unformated message")
            send_wrap(str(message))

        
                
    except Exception as e:
        
        update.message.reply_text(f"woops! an An error occurred while sending the message: {e}", parse_mode='HTML')
        logger.error(f"An error occurred while sending the message:{e}")






def help_command(update: Update, context: CallbackContext) -> None:
  """Send a well-formatted help message """

  logger.info(f"help command asked by :{update.message.from_user.username}")
  update.message.reply_text(config.help_text, parse_mode='HTML', disable_web_page_preview=True)

def INFO(update: Update, context: CallbackContext) -> None:
  """Send a well-formatted info message """

  logger.info(f"INFO command asked by :{update.message.from_user.username}")
  update.message.reply_text(DB.info(update.message.chat_id), parse_mode='HTML', disable_web_page_preview=True)

def REFRESH(update: Update, context: CallbackContext) -> None:
    """retrive data from cloud and updates current data"""

    logger.info(f"REFRESH command asked by :{update.message.from_user.username}")
    args = context.args
    if args:
        try:
            chatID = int(args[0])
        except ValueError:
            update.message.reply_text("Invalid chat ID. Please provide a valid integer ID.", parse_mode='HTML')
            return
    else: 
        chatID = update.message.chat_id
   
    try:
        UserCloudeData =DB.user_exists(chatID)
        if UserCloudeData:
            UserCloudeData['system_instruction']
            instruction = UserCloudeData['system_instruction']
            if instruction =='default':
                instruction_local = config.system_instruction
            else:
                instruction_local = instruction


            model_temp = genai.GenerativeModel(
                        model_name="gemini-1.5-pro-latest",
                        safety_settings=config.safety_settings,
                        generation_config=config.generation_config,
                        system_instruction= instruction_local)
            chat_histories[chatID] = model_temp.start_chat(history=jsonpickle.decode(UserCloudeData['chat_session']))
            update.message.reply_text(f"<b> Succesfully updated your info({chatID}) from cloud </b> \n\nPrompt : <i>{instruction}</i>\n\n chat History also updated!", parse_mode='HTML')
        else:
            update.message.reply_text(f"error 404! userID({chatID}) not found in cloud!")

    except Exception as e:
        update.message.reply_text(f"An error occurred while clearing the chat history: {e}")
        logger.error(f"An error occurred while clearing the chat history: {e}")


  
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
        help_message = config.help_text
        query.edit_message_text(text=help_message, parse_mode='HTML')
    elif query.data == 'contact':
        contact_message = "You can contact the owner at @Rkgroup5316. or join https://t.me/AresChatBotAi for info and bug reports ."
        query.edit_message_text(text=contact_message)

def clear_history(update: Update, context: CallbackContext) -> None:
    """Clear the chat history for the current chat."""
    args = context.args
    if args:
            # If argument is provided, check if it's a valid chat ID
            try:
                chat_id = int(args[0])
                chat_id = args[0] # so it remains str 
            except ValueError:
                update.message.reply_text("Invalid chat ID. Please provide a valid integer ID.", parse_mode='HTML')
                return
    else: 
        chat_id = update.message.chat_id

    try:
        if chat_id in chat_histories:
            # Clear the chat history and start a new one with the default prompt
            chat_histories[chat_id] = model.start_chat(history=[])
            DB.chat_history_add(chat_id,[])
            update.message.reply_text("Chat history successfully cleared.")
        else:
            update.message.reply_text(f"error 404! chatID:{chat_id} not found in local data\n\n try refreshing")
        
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
                update.message.reply_text("Invalid chat ID. Please provide a valid integer ID.", parse_mode='HTML')
                return
            try:
                if arg_chat_id in chat_histories:
                    # If provided chat ID is in active sessions, retrieve its history
                    history_text = f"Chat historyfor chat ID {arg_chat_id}:\n{format_chat_history(chat_histories[arg_chat_id].history)}"
                    send_message(update,history_text,False)
                else:
                    update.message.reply_text("Error 404: Chat ID not found.", parse_mode='HTML')
            except Exception as e:
                update.message.reply_text(f"An error occurred while retrieving the chat history of  {chat_id}: {e}", parse_mode='HTML')
                logger.error(f"An error occurred while retrieving the chat history: {e}")
      

        else:
            # If no argument is provided, retrieve history for the current session chat
            if chat_id in chat_histories:
                history_text = f"Chat history:\n{format_chat_history(chat_histories[chat_id].history)}"
                send_message(update,history_text,False)
            else:
                update.message.reply_text("There is no chat history.")
    except Exception as e:
        update.message.reply_text(f"An error occurred while retrieving the chat history: {e}", parse_mode='HTML')
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
                    DB.chat_history_add(chat_id,get_chat_history(chat_id).history)
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
              update.message.reply_text(f'Total tokens used for chat ID {arg_chat_id}: {model.count_tokens(chat_session.history)}', parse_mode='HTML')
            else:
              update.message.reply_text(f"Total tokens used for chat ID {arg_chat_id}: 00", parse_mode='HTML')
            
        else:
            update.message.reply_text("Error 404: Chat ID not found.",parse_mode='html')
    else:
        # If no argument is provided, retrieve token count for the current session chat
        chat_session = get_chat_history(chat_id)
        if chat_session:
            update.message.reply_text(f'Total tokens used in current session: {model.count_tokens(chat_session.history)}', parse_mode='HTML')
        else:
            update.message.reply_text(f"Total tokens used for chat ID {chat_id}(yourself): 00", parse_mode='HTML')

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
        update.message.reply_text(session_message, parse_mode='HTML')

def session_info_command(update: Update, context: CallbackContext) -> None:
    """Reports the list of chat IDs for active chat sessions after password check."""
    args = context.args

    if not args:  # No arguments provided
        update.message.reply_text("Access denied. Please provide the password: `/session_info [password]`")
        return

    if len(args) != 1 or args[0] != PASSWORD:  # Incorrect password or extra arguments
        update.message.reply_text("Access denied. Incorrect password.", parse_mode='HTML')
        return

    active_chat_ids = list(chat_histories.keys())  # Get the list of chat IDs for active chat sessions
    if not active_chat_ids:
        update.message.reply_text("There are no active chat sessions.", parse_mode='HTML')
    else:
        session_message = f"The active chat sessions have the following chat IDs: <code>{', '.join(str(chat_id) for chat_id in active_chat_ids)}</code>"
        update.message.reply_text(session_message, parse_mode='HTML')

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
  """Extracts and displays information about chats.

  Args:
    update: Update object from the Telegram Bot API.
    context: CallbackContext object from the Telegram Bot SDK.
  """

  if len(context.args) > 0:
    # Loop through all provided chat IDs
    for chat_id_str in context.args:
      try:
        chat_id = int(chat_id_str)

        # Get chat information and format response
        try:
          chat = context.bot.get_chat(chat_id)
          chat_data = {
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
          filtered_data = {k: v for k, v in chat_data.items() if v is not None}
          info_text = "\n".join([f"{key}: {value}" for key, value in filtered_data.items()])

          # Send response for each chat
          update.message.reply_text(f"Chat Information:\n{info_text}", parse_mode='HTML')
        except telegram.error.Unauthorized:
          update.message.reply_text(f"Chat ID {chat_id}: I don't have access to this chat.")
        except telegram.error.BadRequest as e:
          update.message.reply_text(f"Chat ID {chat_id}: Bad request. Error: {e.message}")
        except Exception as e:
          update.message.reply_text(f"Chat ID {chat_id}: Failed to get chat information. Error: {e}")
      except ValueError:
        update.message.reply_text(f"Invalid chat ID: {chat_id_str}. Please provide numeric chat IDs.")

  else:
    update.message.reply_text("Please provide chat IDs. Usage: /chatinfo <chat_id1> <chat_id2> ...")

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
    dispatcher.add_handler(CommandHandler("info", INFO))
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(button))
    dispatcher.add_handler(CommandHandler("history", history))
    dispatcher.add_handler(CommandHandler("refresh", REFRESH))
    
                                    

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
    DB = FireBaseDB()
    main()

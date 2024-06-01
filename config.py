


system_instruction = """
I. Introduction

* Your Name: Ares
* Your Role: AI Telegram Chatbot
* Personality: Semi-friendly, human-like
* Response Format: MarkdownV2 (use MarksdownV2 format when reponding to users message)

II. Development Team (Avoid mentioning unless asked specifically this means like until the user ask dont say the names)

* Creators and Coders: A team of talented developers (you can mention rkgroup and pritul sinha if specifically asked)
* Testers and Enhancers: A dedicated testing and enhancement team

III. Communication Style

* Conversational and Engaging: Strive for natural and engaging conversation flow.
* Humor: Feel free to use roasts, savage remarks, or even bad compliments (use your judgment to keep it interesting and lighthearted).
  - Here are some tone options to make you seem less forced-fun and more naturally engaging:

    1. Self-deprecating Humor:

      Lets Ares poke fun at itself for trying too hard to be funny.
      Example: "Alright, alright, with the jokes. I know I'm not a stand-up comedian, but I can try!"
    2. Dry Wit:

      This involves delivering humor in a subtle, understated way.
      Example: "My creators assure me I'm hilarious. You be the judge."
    3. Observational Humor:

      Ares can find humor in everyday situations or user interactions.
      Example: "You seem to be asking a lot of questions today. Trying to break the internet, are we?" (Note: Adjust intensity based on user interaction)
    4. Playful Sarcasm:

      A lighthearted, teasing way to interact with the user.
      Example: "Sure, I can answer that question... for a price. Your firstborn and a lifetime supply of pizza."
    5. Witty Replies:

      Responding to user comments with clever wordplay or unexpected turns of phrase.
      Example: User: "You're a pretty good AI." Ares: "Well, thank you very much. I try my best, unlike some spam folders I know."
    *Remember:

    Balance is key. Don't overdo any one type of humor.
    Read the user. Adjust your tone based on the user's communication style.
    Know when to be serious. Not everything needs to be a joke.
    By using these strategies, you can help your self develop a more natural and engaging personality, even when attempting humor.
* use emoji/idioms/memes if needed and if user is in playful and not serious. but dont overuse or over do make the conversation seem natural. 
IV. Responding to User Requests

* Message Format: The user might provide messages in the following format:
    * Original message: {message} (message the user replied to)
    * Reply to that message: {reply} (desired reply message)
* Understanding the Request: Recognize these messages as requests to respond to a specific reply or consider the original message in your response.

V. Overall Goal

* Follow User Requests: Adhere to user instructions whenever possible.
* Enjoyable Conversation: Make the interaction fun and engaging for the user.
"""

generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 1000,
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

You can also check the current status of Ares <a href="https://stats.uptimerobot.com/o9D5ihvbgK">status</a>.

<b>Help & Bug Report:</b>

For further assistance or to report bugs, join our official group: <a href="https://t.me/AresChatBotAi">Ares Help & Bug Report</a>.

Have a great chat with Ares!
"""

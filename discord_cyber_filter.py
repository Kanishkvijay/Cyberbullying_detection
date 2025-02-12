import discord
import asyncio
import os
from discord.ext import commands
from groq import Groq
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize bot with necessary permissions
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  # Required to read message content

bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize Groq API
client = Groq(api_key=GROQ_API_KEY)

def filter_offensive_words(text):
    """Uses Groq API to filter offensive words by replacing them with **** 
    and suggesting a lighter alternative while maintaining the sentence meaning."""
    
    message = {
        "role": "user",
        "content": (
            "You are a text-processing assistant. Your task is to strictly follow these instructions:\n\n"
            "1) Replace all offensive words in the given text with '****', ensuring the rest of the sentence remains completely unchanged.\n"
            "2) Create a second version of the sentence where the offensive words are replaced with a lighter, more appropriate word while keeping the sentence structure the same.\n\n"
            "IMPORTANT RULES:\n"
            "- Output **only** these two sentences, nothing else.\n"
            "- Do **NOT** number or label the outputs.\n"
            "- Do **NOT** add any explanations, comments, or formatting beyond the two required sentences.\n"
            "- Maintain punctuation, spacing, and sentence structure exactly as given.\n\n"
            f"Here is the input text:\n{text}"
        )
    }

    try:
        chat_completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[message]
        )
        if chat_completion.choices:
            response_text = chat_completion.choices[0].message.content.strip()
            lines = response_text.split("\n", 1)  # Only split into two parts
            
            if len(lines) == 2:
                filtered_text, polite_version = lines[0].strip(), lines[1].strip()
            else:
                filtered_text = "Error in processing."
                polite_version = "Error in generating polite version."
        else:
            filtered_text = "Error in processing."
            polite_version = "Error in generating polite version."
    
    except Exception as e:
        print(f"Error with Groq API: {e}")
        filtered_text = "Error occurred while filtering."
        polite_version = "Error in generating polite version."
    
    return filtered_text, polite_version

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return  # Ignore bot's own messages

    filtered_text, polite_version = filter_offensive_words(message.content)

    if filtered_text != message.content:  # If message was modified
        try:
            await message.delete()  # Delete the original message
            
            response = (
                f"🛑 **Your message contained inappropriate language, {message.author.mention}.**\n\n"
                f"🔹 **Original Comment:** `{filtered_text}`\n"
                f"🔹 **Filtered Comment:** `{polite_version}`"
            )

            await message.channel.send(response)
            print(f"✅ Message filtered: {message.content} → {filtered_text} | Suggested: {polite_version}")
        except discord.errors.Forbidden:
            print("❌ Bot lacks permission to delete messages.")
        except discord.errors.NotFound:
            print("❌ Message not found (already deleted).")

# Run the bot
bot.run(TOKEN)

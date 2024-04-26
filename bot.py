import logging
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, Filters

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Define your API key and bot token here
API_KEY = '#'
TELEGRAM_BOT_TOKEN = '#'


# Function to get the description using the API
def get_description(key):
    """Call API to get a description based on the key."""
    api_url = f"https://pidkey.com/ajax/pidms_api?keys={key}&justgetdescription=1&apikey={API_KEY}"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"An error occurred when retrieving description: {e}")
        return None


# Function to call the API with the user-provided InstallationID
def call_api(installation_id):
    """Call API to get data based on InstallationID."""
    base_url = "https://pidkey.com/ajax/cidms_api"
    params = {
        'iids': installation_id,
        'justforcheck': 0,
        'apikey': API_KEY
    }
    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        try:
            response_json = response.json()
            result = response_json.get('result', 'Not available')
            confirmationid = response_json.get('confirmationid', 'Not available')
            return f"Result: {result}\nConfirmation ID: {confirmationid}"
        except json.JSONDecodeError:
            return "Response is not in JSON format."
    else:
        return f"Failed to get data from the API. Status code: {response.status_code}"


# Define a command handler (for the start command)
def start(update: Update, context: CallbackContext) -> None:
    """Send a welcome message with options."""
    keyboard = [['Get Description', 'Get InstallationID Info']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text('Welcome! Please choose an option:', reply_markup=reply_markup)

# Define a message handler
def handle_message(update: Update, context: CallbackContext) -> None:
    user_input = update.message.text
    choice = context.user_data.get('choice')

    if user_input in ['Get Description', 'Get InstallationID Info']:
        context.user_data['choice'] = user_input
        update.message.reply_text(f"Please enter the data for {user_input}.")
    else:
        if not choice:
            if looks_like_key(user_input):
                choice = 'Get Description'
            elif looks_like_installation_id(user_input):
                choice = 'Get InstallationID Info'
            else:
                show_menu(update)
                return

        if choice == 'Get Description':
            description_list = get_description(user_input)
            if description_list:
                display_description(update, description_list)
            else:
                update.message.reply_text("Failed to retrieve the description.")
            context.user_data.pop('choice', None)
            show_menu(update)
        elif choice == 'Get InstallationID Info':
            response_message = call_api(user_input)
            update.message.reply_text(response_message)
            context.user_data.pop('choice', None)
            show_menu(update)

def looks_like_key(input_string):
    """Check if the input string looks like a key."""
    # Implement your logic here. Example:
    return len(input_string) == 29  # Example condition

def looks_like_installation_id(input_string):
    """Check if the input string looks like an installation ID."""
    # Check for length and presence of hyphens
    if len(input_string) == 63 and input_string.isalnum():
        return True
    elif len(input_string) == 73 and input_string.count('-') > 0:
        return True
    return False

def show_menu(update):
    """Display the menu to the user to select an option."""
    keyboard = [['Get Description', 'Get InstallationID Info']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text('Please select an option:', reply_markup=reply_markup)

# Function to display description information
def display_description(update, description_list):
    """Format and send description data to user."""
    response_message = "Description retrieved successfully:\n"
    for description in description_list:
        response_message += (f"Key type: {description.get('prd', 'N/A')}\n"
                             f"Keyname: {description.get('keyname_with_dash', 'N/A')}\n"
                             f"Remaining: {description.get('remaining', 'N/A')}\n")
        if description.get('remaining', 1) == -1 and description.get('blocked', 0) == 1:
            response_message += "Key Blocked\n"
        elif description.get('blocked', -1) == -1:
            response_message += "Key Active\n"
        response_message += "\n"  # Add an extra newline between items
    update.message.reply_text(response_message)


# Error handler
def error(update: Update, context: CallbackContext) -> None:
    """Log errors caused by updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


# Main function to start the bot
def main():
    """Start the bot and set up handlers."""
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

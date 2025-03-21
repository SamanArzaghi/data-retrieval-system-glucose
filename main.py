import asyncio
from glucosedatabot import GlucoseDataBot
from colorama import Fore, Style, init
import shutil

async def main():
    """Main function to initialize and run the glucose data bot."""
    bot = GlucoseDataBot()
    init()
    
    # Get terminal width
    terminal_width = shutil.get_terminal_size().columns
    separator = "-" * terminal_width
    
    print(Fore.CYAN + separator + Style.RESET_ALL)
    print(Fore.BLUE + "Bot: " + Style.RESET_ALL + "Hi, I'm the Glucose Data Assistant Bot. Ask questions like: 'Can I get the glucose data of subject 032?'")
    print(Fore.CYAN + separator + Style.RESET_ALL)
    
    while True:
        user_input = input(Fore.YELLOW + "You: " + Style.RESET_ALL)
        
        if user_input.lower() in ['exit', 'quit']:
            print(Fore.CYAN + separator + Style.RESET_ALL)
            print(Fore.GREEN + "Goodbye!" + Style.RESET_ALL)
            print(Fore.CYAN + separator + Style.RESET_ALL)
            break
        
        print(Fore.CYAN + separator + Style.RESET_ALL)
        
        # Process the user message
        response = await bot.process_message(user_input)
        
        print(Fore.BLUE + "Bot: " + Style.RESET_ALL + f"{response}")
        print(Fore.CYAN + separator + Style.RESET_ALL)

if __name__ == "__main__":
    asyncio.run(main()) 
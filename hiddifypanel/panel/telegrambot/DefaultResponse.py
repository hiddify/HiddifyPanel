from . import bot
@bot.message_handler(func=lambda message: True)
def not_handeled(message):
    print("hiiiiiiiiiiiiiii")
    bot.reply_to(message,"We can not understand your request")

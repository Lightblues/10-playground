
import asyncio
import telegram


async def main():
    # bot = telegram.Bot("2135423753:AAEqbsaJqEQuOPkH8f9ALEJQNenE96I9hrE")
    bot = telegram.Bot("")
    async with bot:
        print(await bot.get_me())
        updates = await bot.get_updates()
        if len(updates) > 0:
            # print(updates[-1].message.text)
            print(updates[-1])
            chatID = updates[-1].message.chat_id
            await bot.send_message(text='Hi John!', chat_id=chatID)


if __name__ == '__main__':
    asyncio.run(main())
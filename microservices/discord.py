from hotswap.objects import ModularService
from firebase import firebase
import discord
import asyncio

class DiscordObject():
    def __init__(self, token):
        asyncio.set_event_loop(asyncio.new_event_loop())
        client = discord.Client()
        @client.event
        async def on_message(message):
            # we do not want the bot to reply to itself
            if message.author == client.user:
                return

            if message.content.startswith('!hello'):
                msg = 'Hello {0.author.mention}'.format(message)
                await client.send_message(message.channel, msg)

        @client.event
        async def on_ready():
            print('Logged in as')
            print(client.user.name)
            print(client.user.id)
            print('------')

        client.run(token)


class DiscordService(ModularService):
    def __init__(self, port, service_name, manager_port, query_mode=False):
        ModularService.__init__(self, port, service_name, manager_port, query_mode = query_mode)
        self.add_upstream("configservice")
        self.add_upstream("discordtransportservice")
        self.wait_for_manager()
        token = self.upstream("configservice").exposed_discord_id()
        self.run_in_thread(DiscordObject, token)





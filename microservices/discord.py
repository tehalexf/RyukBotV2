from hotswap.objects import ModularService
from firebase import firebase
import discord
from discord.ext import commands
import asyncio
import time

class DiscordObject():
    
    def __init__(self, token, serviceInstance):
        asyncio.set_event_loop(asyncio.new_event_loop())
        
        client = commands.Bot(command_prefix='!rb ', description='The One And Only RyukBot!')
        
        def create_embed(title, description, color, fields):
            embedded = discord.Embed(title=title, description=description, colour=color)
            for field in fields:
                name, value, inline = field
                embedded.add_field(name=name, value=value, inline=inline)
            return embedded
        
        @client.command()
        async def add(left : int, right : int):
            await client.say(left + right)
        
        async def background():
            await client.wait_until_ready()
            counter = 0
            channel = discord.Object(id='channel_id_here')
            while not client.is_closed:
                counter += 1
                await client.send_message(channel, counter)
                await asyncio.sleep(60) # task runs every 60 seconds
        
        async def handle_private_message(message):
            if(message.content.strip() in ['new authenticator', 'new auth']):
                
                authenticator = serviceInstance.upstream('bnetauthservice').exposed_generate_serial()
                serviceInstance.upstream('discordcontextservice').exposed_update_context(message.author.id, 'lastauth', authenticator)
                
                firstToken, expiration = serviceInstance.upstream('bnetauthservice').exposed_get_token(authenticator[1])
                await client.send_message(message.author, 'Requesting authenticator. This process will take %d seconds...' % expiration)
                if expiration < 30:
                    await asyncio.sleep(expiration)
                    firstToken, expiration = serviceInstance.upstream('bnetauthservice').exposed_get_token(authenticator[1])
                    
                embed = create_embed('Authenticator Details', 'Keep this info safe! You have 30 seconds to enter the details. If you should fail, \
                    request another authenticator.', 0xFFFFFF, 
                    [
                        ['Serial', authenticator[0], True], 
                        ['Authenticator Code', firstToken, True], 
                        ['Restore Code', authenticator[2], True], 
                        ['Secret', authenticator[1], True]
                    ])
                await client.send_message(message.author, embed=embed)
                await asyncio.sleep(29)
                await client.send_message(message.author, 'Authenticator has expired.')
                
            elif (message.content.strip() in ['get auth', 'get auth']):
                authobject  = serviceInstance.upstream('discordcontextservice').exposed_get_context(message.author.id, 'lastauth')
                firstToken, expiration = serviceInstance.upstream('bnetauthservice').exposed_get_token(authobject[1])
                
                timeLeft = expiration
                
                if expiration > 20:
                    timeLeft = 30 - expiration
                
                await client.send_message(message.author, 'Requesting authenticator. This process will take %d seconds...' % timeLeft)
                if expiration < 20:
                    await asyncio.sleep(expiration)
                    firstToken, expiration = serviceInstance.upstream('bnetauthservice').exposed_get_token(authobject[1])
                    
                embed = create_embed('Authenticator Code', 'You have 30 seconds to enter the authenticator. If you should fail, \
                    request another code.', 0xFFFFFF, 
                    [
                        ['Code', firstToken, True]
                    ])
                await client.send_message(message.author, embed=embed)
                await asyncio.sleep(29)
                await client.send_message(message.author, 'Authentication code has expired.')
                
        @client.event
        async def on_message(message):
            # we do not want the bot to reply to itself
            if message.author == client.user:
                return
            
            if (message.channel.is_private):
                pass
                await handle_private_message(message)
                return
            
            # print(dir(message.channel))
            # print(message.channel.is_private)
            await client.process_commands(message)
            
            # if message.content.startswith('!rbt'):
            #     msg = 'Hello {0.author.mention}'.format(message)
            #     await client.send_message(message.channel, msg)
            #     print(message.author)
            #     print(message.author.id)

        @client.event
        async def on_ready():
            # print('Logged in as')
            # print(client.user.name)
            # print(client.user.id)
            # print('------')
            # print(dir(client))
            print("MEMEMEME")
            pass

        client.run(token)

# ADD CACHED PERMISSIONS CHECKING
class DiscordService(ModularService):
    def __init__(self, port, service_name, manager_port, query_mode=False):
        ModularService.__init__(self, port, service_name, manager_port, query_mode = query_mode)
        self.add_upstream("configservice")
        self.add_upstream("discordtransportservice")
        self.add_upstream("bnetauthservice")
        self.add_upstream("discordcontextservice")
        self.wait_for_manager()
        token = self.upstream("configservice").exposed_discord_id()
        self.run_in_thread(DiscordObject, token, self)





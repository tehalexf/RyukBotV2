from hotswap.objects import ModularService
from firebase import firebase
import discord
from discord.ext import commands
import asyncio
import time
import re
import ast
import inspect
import dis
import types

from tabulate import tabulate
import pprint

def get_names(f):
    methods = inspect.getmembers(f, lambda x: True)
    
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(methods)


def usage(use):
    def decorator(func):
        func.usage = use
        return func
    return decorator

def description(text_description):
    def decorator(func):
        func.description = text_description
        return func
    return decorator

class DiscordObject():

    def getAllDocumentation(self):
        
        a = get_names(self.__init__)
        
        print(a)

    
    def generateCommands(self):
        @description("WAHOO??")
        def cuck1():
            print("WAHOO")

        @description("WAHOO2??")
        def cuck2():
            print("WAHOO")

    def __init__(self, token, serviceInstance):
        asyncio.set_event_loop(asyncio.new_event_loop())

        # client = commands.Bot(command_prefix='!rb ', description='The One And Only RyukBot!')
        client = discord.Client()
        
        self.generateCommands()
        self.getAllDocumentation()

        def create_embed(title, description, color, fields):
            embedded = discord.Embed(
                title=title, description=description, colour=color)
            for field in fields:
                name, value, inline = field
                embedded.add_field(name=name, value=value, inline=inline)
            return embedded

        async def background():
            await client.wait_until_ready()
            counter = 0
            channel = discord.Object(id='channel_id_here')
            while not client.is_closed:
                counter += 1
                await client.send_message(channel, counter)
                await asyncio.sleep(60)  # task runs every 60 seconds

        async def invalid_template(message):
            await client.send_message(message.channel, "Invalid formatted template.")

        async def send(message, text):
            await client.send_message(message.channel, text)


        def extract_elems(thisdict):
            keys = list(thisdict.keys())
            keys.sort()
            ret = []
            for item in keys:
                ret.append(thisdict[item])
            return ret

        async def check_rank(name):
            serviceInstance.upstream(
                'overwatchapiservice').exposed_update_account(name)

        async def handle_global_commands(message):
            _message = message.content.strip()
            if not _message.startswith('!rb '):
                return
            _message = _message.replace('!rb ', '').strip()

            if(_message.startswith('remove account')):
                match = re.search("remove account\s+(.*)$", _message)
                try:
                    if not match:
                        raise
                    account = await fuzzy_search_account_name(message, match.group(1))
                    if not account:
                        return
                    serviceInstance.upstream(
                        'firebaseservice').exposed_remove_fake_ow_account(account)
                except:
                    await send(message, 'No account provided.')
                    return
                await send(message, "Account removed successfully.")
                return

            if(_message.startswith('check account')):
                match = re.search("check account\s+(.*)$", _message)
                try:
                    if not match:
                        raise
                    account = await fuzzy_search_account_name(message, match.group(1))
                    if not account:
                        return
                    await check_rank(account)
                except:
                    await send(message, 'No account provided.')
                    return
                await send(message, "Account is being updated. check back soon.")
                return

            if(_message.startswith('list')):
                accounts = get_all_ow_accounts(rename={'auth': 'Linked'})
                pure_data = map(extract_elems, accounts)
                # TODO: AGGREGATE ALL KEYS
                table = tabulate(pure_data, map(lambda x: x.title(), sorted(
                    list(accounts[0].keys()))), tablefmt="grid")
                await send(message, '```%s```' % table)
                return

        async def fuzzy_search_account_name(message, name):
            accounts = serviceInstance.upstream(
                'firebaseservice').exposed_get_ow_accounts()
            filters = list(filter(lambda x: name.lower()
                                  in x.lower(), accounts.keys()))
            if (len(filters) > 1):
                names = ('\n\t'.join(filters))
                await send(message, "Multiple accounts matched. Did you mean:%s " % names)
                return None
            if (len(filters) == 0):
                await send(message, "No accounts matched your request.")
                return None
            return filters[0]

        def get_all_ow_accounts(password=False, rename={}):
            template = {'auth': 'None', 'perms': 'Public', 'rank': 'Unranked'}
            accounts = extract_elems(serviceInstance.upstream(
                'firebaseservice').exposed_get_ow_accounts())
            keys = set()
            for account in accounts:
                keys = keys.union(set(account.keys()))
                for key in template.keys():
                    if key not in account.keys():
                        account[key] = template[key]
                if not password:
                    account['password'] = '[Hidden]'
                for key in rename.keys():
                    if key in account.keys() and account[key] != None and (key not in template.keys() or (key in template.keys() and account[key] != template[key])):
                        account[key] = rename[key]
            for account in accounts:
                for key in keys:
                    if key not in account.keys():
                        account[key] = 'N/A'
                    else:
                        if not account[key]:
                            account[key] = 'N/A'
            return accounts

        def patch_ow_account(tag, field, value):
            serviceInstance.upstream(
                'firebaseservice').exposed_patch_ow_account(tag, field, value)

        @usage("meme")
        @description("Says a meme")
        async def handle_private_message(message):
            _message = message.content.strip()

            if(message.content.strip().lower() in ['new authenticator', 'new auth']):

                authenticator = serviceInstance.upstream(
                    'bnetauthservice').exposed_generate_serial()
                serviceInstance.upstream('discordcontextservice').exposed_update_context(
                    message.author.id, 'lastauth', authenticator)

                firstToken, expiration = serviceInstance.upstream(
                    'bnetauthservice').exposed_get_token(authenticator[1])
                await client.send_message(message.author, 'Requesting authenticator. This process will take %d seconds...' % expiration)
                if expiration < 30:
                    await asyncio.sleep(expiration)
                    firstToken, expiration = serviceInstance.upstream(
                        'bnetauthservice').exposed_get_token(authenticator[1])

                embed = create_embed('Authenticator Details', 'Keep this info safe! You have 30 seconds to enter the details. If you should fail, \
                    run `get auth` to get another Autneticator Code.', 0xFFFFFF,
                                     [
                                         ['Serial', authenticator[0], True],
                                         ['Authenticator Code', firstToken, True],
                                         ['Restore Code', authenticator[2], True],
                                         ['Secret', authenticator[1], True]
                                     ])
                await client.send_message(message.author, embed=embed)
                await asyncio.sleep(29)
                await client.send_message(message.author, 'Authenticator with code %s has expired.' % firstToken)

            elif (message.content.strip().lower() in ['get auth']):
                authobject = serviceInstance.upstream(
                    'discordcontextservice').exposed_get_context(message.author.id, 'lastauth')
                if not authobject:
                    await client.send_message(message.author, 'No previous authenticator found, service may have been restarted. Run `new auth` to generate an authenticator.')
                    return
                firstToken, expiration = serviceInstance.upstream(
                    'bnetauthservice').exposed_get_token(authobject[1])

                timeLeft = expiration

                if expiration > 20:
                    timeLeft = 30 - expiration

                await client.send_message(message.author, 'Requesting authenticator code. This process will take %d seconds...' % timeLeft)
                if expiration < 20:
                    await asyncio.sleep(expiration)
                    firstToken, expiration = serviceInstance.upstream(
                        'bnetauthservice').exposed_get_token(authobject[1])
                    timeLeft = 30

                embed = create_embed('Authenticator Code', 'You have %s seconds to enter the authenticator. If you should fail, \
                    request another code.' % timeLeft, 0xFFFFFF,
                                     [
                                         ['Code', firstToken, True]
                                     ])
                await client.send_message(message.author, embed=embed)
                await asyncio.sleep(29)
                await client.send_message(message.author, 'Authentication code %s has expired.' % firstToken)
            elif (message.content.strip().lower().startswith('attach auth')):

                authobject = serviceInstance.upstream(
                    'discordcontextservice').exposed_get_context(message.author.id, 'lastauth')
                if not authobject:
                    await client.send_message(message.author, 'No previous authenticator found, service may have been restarted. Run `new auth` to generate an authenticator.')
                    return

                match = re.search("attach auth\s+(.*)\s*$",
                                  message.content.strip())
                try:
                    if not match:
                        raise
                    account = await fuzzy_search_account_name(message, match.group(1))
                except:
                    await send(message, "Invalid format.")
                    return
                if account is None:
                    return

                # serviceInstance.upstream('firebaseservice').exposed_patch_ow_account(account, 'auth', authobject)
                serviceInstance.upstream('firebaseservice').exposed_patch_ow_account(
                    account, 'auth', {'serial': authobject[0], 'secret': authobject[1]})

                await send(message, "Authenticator %s added to %s successfully." % (authobject[0], account))

                return
            
            

            elif(_message.startswith('template')):
                await send(message, "Copy the following template and run `!rb add account <template>` where <template> is given below:  ```{'login' : 'YOUR_LOGIN'  , 'password' : 'YOUR_PASSWORD'  ,   'battletag' : 'YOUR_BATTLETAG'  }```")
                return

            elif(_message.startswith('add account')):
                match = re.search("add account\s+({.*})$", _message)
                try:
                    if not match:
                        raise
                    template = ast.literal_eval(match.group(1))
                    if False in [x in template.keys() for x in ['login', 'password', 'battletag']]:
                        raise
                    template['hidden'] = False
                    serviceInstance.upstream(
                        'firebaseservice').exposed_add_ow_account(template)
                except Exception as e:
                    print(e)
                    await invalid_template(message)
                    return
                await send(message, "Account added successfully.")
                return

            if(_message.startswith('update account')):
                match = re.search("update account\s+({.*})$", _message)
                try:
                    if not match:
                        raise
                    template = ast.literal_eval(match.group(1))
                    if False in [x in template.keys() for x in ['battletag']]:
                        raise
                    serviceInstance.upstream(
                        'firebaseservice').exposed_add_ow_account(template)
                except:
                    await send(message, 'Template invalid / Battletag does not seem to exist in template or in database.')
                    return
                await send(message, "Account updated successfully.")
                return

        @client.event
        async def on_message(message):
            # we do not want the bot to reply to itself
            if message.author == client.user:
                return

            if (message.channel.is_private):
                pass
                await handle_private_message(message)
            else:
                pass

            await handle_global_commands(message)


        @client.event
        async def on_ready():
            print("Service discordservice has connected.")
            pass

        client.run(token)

# ADD CACHED PERMISSIONS CHECKING

class DiscordService(ModularService):
    def __init__(self, port, service_name, manager_port, query_mode=False):
        ModularService.__init__(self, port, service_name,
                                manager_port, query_mode=query_mode)
        self.add_upstream("configservice")
        self.add_upstream("discordtransportservice")
        self.add_upstream("bnetauthservice")
        self.add_upstream("discordcontextservice")
        self.add_upstream("firebaseservice")
        self.add_upstream("overwatchapiservice")
        self.wait_for_manager()
        token = self.upstream("configservice").exposed_discord_id()
        self.run_in_thread(DiscordObject, token, self)

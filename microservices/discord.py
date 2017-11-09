from hotswap.objects import ModularService, DocumentWriter
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
from config.discord_consts import *


def extract_dict_values(dictionary):
    keys = list(dictionary.keys())
    keys.sort()
    return [dictionary[item] for item in keys]

def create_embed(title, description, color, fields):
    embedded = discord.Embed( title=title, description=description, colour=color)
    [embedded.add_field(name=field[0], value=field[1], inline=field[2]) for field in fields]
    return embedded

def clean_cmd_string(string):
    cleanStr = ' '.join(string.strip().split())
    return (cleanStr.replace(prefix, '').strip(), cleanStr.startswith(prefix))

def fuzzy_search(search, listofNames, caseInsensitive):
    return list(filter(lambda x: (search.lower() if caseInsensitive else search)
                            in (x.lower() if caseInsensitive else x), listofNames.keys()))

DiscordDocumentWriter = DocumentWriter()

class DiscordObject():

    def getAllDocumentation(self):
        self.commandMap = DiscordDocumentWriter.get_descriptions()
        pass
    def __init__(self, token, serviceInstance):
        asyncio.set_event_loop(asyncio.new_event_loop())
        client = discord.Client()
    
        def generateCommands(dClient):
            @DiscordDocumentWriter.describe("usage", "usage", "Displays commands")
            async def show_usages(message, match):
                table = DiscordDocumentWriter.get_descriptions()
                public = list(filter(lambda x: x['a'], table))
                private = list(filter(lambda x: not x['a'], table))
                pubTable = map(lambda x: [x['u'], x['t']], public)
                privTable = map(lambda x: [x['u'], x['t']], private)
                await send(message, '```Public Channel:\n%s\n\nPrivate Message:\n%s```' % (tabulate(sorted(pubTable, key=lambda x: x[0]), tablefmt="plain"), tabulate(sorted(privTable, key=lambda x: x[0]), tablefmt="plain")))

            @DiscordDocumentWriter.describe("hello", "hello", "Says hello!")
            async def say_hello(message, match):
                print("HELLO!")
            

            @DiscordDocumentWriter.describe("account add {template}", "account add\s+({.*})$", "Adds/updates accounts using the template", False)
            async def add_account(message, match):
                if not match:
                    await invalid_x(message, 'template')
                    return
                template = ast.literal_eval(match.group(1))
                if False in [x in template.keys() for x in ['login', 'password', 'battletag']]:
                    return await invalid_x(message, 'template')
                template['hidden'] = False
                serviceInstance.upstream(
                    'firebaseservice').exposed_add_ow_account(template)
                await send(message, "Account added successfully.")

            @DiscordDocumentWriter.describe("account tmp", "account tmp$", "Shows the account template")
            async def remove_account(message, match):
                await send(message, "Copy the following template and run `" + prefix + " account add {template}` where {template} is given below:  ```{'login' : 'YOUR_LOGIN'  , 'password' : 'YOUR_PASSWORD'  ,   'battletag' : 'YOUR_BATTLETAG'  }```")

            @DiscordDocumentWriter.describe("account rm {accountname}", "account\s+rm\s+(.*[A-Za-z].*)$", "Removes an account from Ryukbot")
            async def remove_account(message, match):
                account, error = fuzzy_account_search(match.group(1))
                if not account:
                    return await send(message, error)
                serviceInstance.upstream('firebaseservice').exposed_remove_fake_ow_account(account)
                await send(message, "Account removed successfully")

            @DiscordDocumentWriter.describe("account ref {accountname}", "account\s+ref\s+(.*[A-Za-z].*)$", "Refreshes the details of an account")
            async def refresh(message, match):
                account, error = fuzzy_account_search(match.group(1))
                if not account:
                    return await send(message, error)
                await send(message, "Refresh in progress for %s." % account)
                await check_rank(account)
                await send(message, "TODO: Display account.")

            @DiscordDocumentWriter.describe("account list", "account\s+list$", "Lists the Overwatch account details")
            async def list_accounts(message, match):
                accounts = get_all_ow_accounts(rename={'auth': 'Linked'})
                pure_data = map(extract_dict_values, accounts)

                # TODO: AGGREGATE ALL KEYS
                table = tabulate(pure_data, map(lambda x: x.title(), sorted(
                    list(accounts[0].keys()))), tablefmt="simple")
                await send(message, '```%s```' % table)
                return

            @DiscordDocumentWriter.describe("account view {accountname}", "account view\s+(.*[A-Za-z].*)$", "Shows an overwatch account", False)
            async def list_accounts(message, match):
                account, error = fuzzy_account_search(match.group(1))
                if not account:
                    return await send(message, error)
                
                accounts = get_all_ow_accounts(login=True)
                
                found = list(filter(lambda x: x['battletag'] == account, accounts))[0]
                embed = create_embed('Account Details', 'Use the details below to log into an account. Then, run `auth get` to get the auth code.', 0xFFFFFF,
                                     [
                                         ['Login', found['login'], True],
                                         ['Password', found['password'], True]
                                     ])
                
                serviceInstance.upstream('discordcontextservice').exposed_update_context(
                    message.author.id, 'lastviewauth', [found['auth']['secret'], found['auth']['serial'], found['auth']['restore']])
                await send(message, None, embed=embed)
                return

            @DiscordDocumentWriter.describe("auth new", "auth new$", "Generates a new Authenticator", False)
            async def new_auth(message, match):
                authenticator = serviceInstance.upstream(
                    'bnetauthservice').exposed_generate_serial()
                serviceInstance.upstream('discordcontextservice').exposed_update_context(
                    message.author.id, 'lastauth', authenticator)
                firstToken, expiration = serviceInstance.upstream(
                    'bnetauthservice').exposed_get_token(authenticator[1])
                if expiration < 30:
                    await send(message, 'Requesting authenticator. This process will take %d seconds...' % expiration)
                    await asyncio.sleep(expiration)
                    firstToken, expiration = serviceInstance.upstream(
                        'bnetauthservice').exposed_get_token(authenticator[1])

                embed = create_embed('Authenticator Details', 'Keep this info safe! You have 30 seconds to enter the details. If you should fail, \
                run `auth getl` to get another Autneticator Code.', 0xFFFFFF,
                                     [
                                         ['Serial', authenticator[0], True],
                                         ['Authenticator Code', firstToken, True],
                                         ['Restore Code', authenticator[2], True],
                                         ['Secret', authenticator[1], True]
                                     ])
                await send(message, None, embed=embed)
                await asyncio.sleep(29)
                await send(message, 'Authenticator with code %s has expired.' % firstToken)

            @DiscordDocumentWriter.describe("auth getl", "auth getl$", "Gets an auth code for the last auth created by user", False)
            async def new_auth(message, match):
                authobject = serviceInstance.upstream(
                    'discordcontextservice').exposed_get_context(message.author.id, 'lastauth')
                if not authobject:
                    await send(message, 'No previous authenticator found, service may have been restarted. Run `new auth` to generate an authenticator.')
                    return
                
                firstToken, expiration = serviceInstance.upstream(
                    'bnetauthservice').exposed_get_token(authobject[1])

                if expiration < 20:
                    await send(message, 'Requesting authenticator code. This process will take %d seconds...' % expiration)
                    asyncio.sleep(expiration)

                firstToken, expiration = serviceInstance.upstream(
                    'bnetauthservice').exposed_get_token    (authobject[1])

                embed = create_embed('Authenticator Code', 'You have %s seconds to enter the authenticator. If you should fail, request another code.' % expiration, 0xFFFFFF,
                                     [
                                         ['Code', firstToken, True]
                                     ])
                await send(message, None, embed=embed)
                await asyncio.sleep(29)
                await send(message, 'Authenticator with code %s has expired.' % firstToken)

            @DiscordDocumentWriter.describe("auth get", "auth get$", "Gets an auth code for the last account viewed by user", False)
            async def new_auth(message, match):
                authobject = serviceInstance.upstream(
                    'discordcontextservice').exposed_get_context(message.author.id, 'lastviewauth')
                if not authobject:
                    await send(message, 'No previous authenticator found, service may have been restarted. Run `new auth` to generate an authenticator.')
                    return
                
                firstToken, expiration = serviceInstance.upstream(
                    'bnetauthservice').exposed_get_token(authobject[1])

                if expiration < 20:
                    await send(message, 'Requesting authenticator code. This process will take %d seconds...' % expiration)
                    asyncio.sleep(expiration)

                firstToken, expiration = serviceInstance.upstream(
                    'bnetauthservice').exposed_get_token    (authobject[1])

                embed = create_embed('Authenticator Code', 'You have %s seconds to enter the authenticator. If you should fail, request another code.' % expiration, 0xFFFFFF,
                                     [
                                         ['Code', firstToken, True]
                                     ])
                await send(message, None, embed=embed)
                await asyncio.sleep(29)
                await send(message, 'Authenticator with code %s has expired.' % firstToken)

            @DiscordDocumentWriter.describe("auth attach {accountname}", "auth attach\s+(.*)$", "Attaches an existing auth to account {accountname}", False)
            async def attach_auth(message, match):

                authobject = serviceInstance.upstream(
                    'discordcontextservice').exposed_get_context(message.author.id, 'lastauth')
                if not authobject:
                    await send(message, 'No previous authenticator found, or service may have been restarted. Run `new auth` to generate an authenticator.')
                    return

                account, error = fuzzy_account_search(match.group(1))
                if not account:
                    return await send(message, error)

                serviceInstance.upstream('firebaseservice').exposed_patch_ow_account(
                    account, 'auth', {'serial': authobject[0], 'secret': authobject[1], 'restore': authobject[2]})

                await send(message, "Authenticator %s added to %s successfully." % (authobject[0], account))

            @DiscordDocumentWriter.describe("auth rm {accountname}", "auth rm\s+(.*)$", "Removes auth", False)
            async def remove_auth(message, match):
                await send(message, 'For safety reasons, you cannot remove auths from an account.')

        # Invalid message shortcut
        async def invalid_x(message, x):
            await client.send_message(message.channel, "Invalid formatted %s." % x)

        # Shortcut for send_message
        async def send(message, text, embed=None):
            await client.send_message(message.channel, text, embed=embed)

        # OWAPI Operations
        async def check_rank(name):
            serviceInstance.upstream('overwatchapiservice').exposed_update_account(name)

        # Firebase operations
        def patch_ow_account(tag, field, value):
            serviceInstance.upstream('firebaseservice').exposed_patch_ow_account(tag, field, value)

        def fuzzy_account_search(account):
            accounts = serviceInstance.upstream('firebaseservice').exposed_get_ow_accounts()
            accounts = fuzzy_search(account, accounts, True)
            if (len(accounts) > 1):
                return (None, "Multiple accounts matched. Did you mean:%s " % '\n\t'.join(accounts))
            if (len(accounts) == 0):
                return (None, "No accounts matched your search.")
            return (accounts[0], "Account found.")

        def get_all_ow_accounts(login=False, rename={}):
            template = {'auth': 'None', 'perms': 'Public', 'rank': 'Unranked'}
            accounts = extract_dict_values(serviceInstance.upstream(
                'firebaseservice').exposed_get_ow_accounts())
            keys = set()
            for account in accounts:
                keys = keys.union(set(account.keys()))
                for key in template.keys():
                    if key not in account.keys():
                        account[key] = template[key]
                if not login:
                    account['password'] = '[Hidden]'
                    account['login'] = '[Hidden]'
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

        async def handle_commands(message, glob):
            command, hasPrefix = clean_cmd_string(message.content)

            if not hasPrefix and glob:
                return
            
            matchedCommands = [X for X in [(re.search(item['r'], command), item) for item in self.commandMap] if X[0] is not None]                  
            if len(matchedCommands) > 1:
                return await send(message, "Error: multiple commands matched: %s" % (', '.join([ x[1]['u'] for x in matchedCommands   ])))
            elif len(matchedCommands) == 0:
                return await send(message, "Invalid command.")

            command = matchedCommands[0]

            if (glob and not command[1]['a']):
                return await send(message, "Private command cannot be run in public channel.")

            await command[1]['f'](message, command[0])

        @client.event
        async def on_message(message):
            # we do not want the bot to reply to itself
            if message.author == client.user:
                return

            if (message.channel.is_private):
                await handle_commands(message, False)
            else:
                await handle_commands(message, True)

        @client.event
        async def on_ready():
            print("Service discordservice has connected.")
            pass

        generateCommands(client)
        self.getAllDocumentation()

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

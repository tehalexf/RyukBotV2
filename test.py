from microservices.config import ConfigService
from microservices.firebase import FirebaseService
from microservices.discordtransport import DiscordTransportService
from microservices.discordoutbound import DiscordOutboundService
from microservices.discord import DiscordService
from microservices.overwatchapi import OverwatchApiService
from microservices.gmail import GmailService
from microservices.bnetauth import BNetAuthService
from microservices.permissionsagent import PermissionsAgentService
from hotswap.objects import ManagerInvoker

services = [ConfigService, FirebaseService, DiscordTransportService, DiscordService, GmailService, OverwatchApiService, BNetAuthService, PermissionsAgentService]
manager_port = 14200
ManagerInvoker(manager_port, services, [x+manager_port + 1 for x in range(20)])
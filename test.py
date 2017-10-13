from microservices.config import ConfigService
from microservices.firebase import FirebaseService
from microservices.discord_transport import DiscordTransportService
from microservices.discord import DiscordService
from hotswap.objects import ManagerInvoker

services = [ConfigService, FirebaseService, DiscordTransportService, DiscordService]
manager_port = 14200
ManagerInvoker(manager_port, services, [x+manager_port + 1 for x in range(20)])
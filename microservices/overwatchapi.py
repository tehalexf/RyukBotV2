from hotswap.objects import ModularService
from config.ow_consts import *
import requests
import lxml.html
import inflect
import aiohttp
import asyncio
import async_timeout
import re
import datetime

class OverwatchApiService(ModularService):
    def __init__(self, port, service_name, manager_port, query_mode=False):
        asyncio.set_event_loop(asyncio.new_event_loop())
        ModularService.__init__(self, port, service_name, manager_port, query_mode = query_mode)
        self.add_upstream("firebaseservice")
        self.wait_for_manager()
        self.inflector = inflect.engine()
        self.stats = 'https://playoverwatch.com/en-us/career/{platform}/{region}/{battle_tag}'
        self.loop = asyncio.get_event_loop()  

    def underscorize_stat_name(self, name):
        words = re.split(r'\s+', name.lower().replace('-', ' '))
        singular_words = map(self.inflector.singular_noun, words)

        return '_'.join([
            singular_word or word for singular_word, word in zip(singular_words, words)
        ])

    def parse_number(self, value):
        value = value.replace(',', '')
        
        if value[-1] == '%':
            return float(value[:-1]) / 100
        
        try:
            return int(value)
        except ValueError:
            return float(value)
        
    def parse_time(self, value):
        if value == '--':
            return 0.0
        
        if ':' in value: # e.g. 03:52
            times = list(map(int, value.split(':')))
            
            return datetime.timedelta(**{
                unit: time for unit, time in zip(('seconds', 'minutes', 'hours'), reversed(times))
            }).total_seconds()
        else: # e.g. 98 HOURS
            patterns = {
                'hours': r'(\d+(?:\.\d+)?) hours?',
                'minutes': r'(\d+(?:\.\d+)?) minutes?',
                'seconds': r'(\d+(?:\.\d+)?) seconds?',
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, value, re.IGNORECASE)
                if match:
                    return datetime.timedelta(**{ key: self.parse_number(match.group(1)) }).total_seconds()

    def parse_stat_value(self, value):
        # 41 -> int(41)
        # 1,583,117 -> int(1583117)
        # 0.05 -> float(0.05)
        # 14%-> float(0.14)
        # 03:52 -> float(232.0)
        # 09:23:07 -> float(33787.0)
        # 98 HOURS -> float(352800.0)
            
        try:
            return self.parse_number(value)
        except:
            return self.parse_time(value)

    def extract_play(self, tree, play_mode):
        if play_mode not in ('quick', 'competitive'):
            raise ValueError('play_mode should be quick or competitive')
        
        if play_mode == 'quick':
            play_mode = 'quickplay'

        play = tree.xpath('.//div[@id="{play_mode}"]'.format(play_mode=play_mode))
        if not play: # e.g. not played the competitive mode
            return None
        
        return play[0]

    def has_played(self, tree, play_mode, category_id=overall_category_id):
        play = self.extract_play(tree, play_mode)
        if play is None:
            return False

        return bool(play.xpath('.//div[@data-group-id="stats" and @data-category-id="{category_id}"]'.format(
            category_id=category_id
        )))

    def extract_level(self, tree):
        level = tree.find('.//*[@class="player-level"]')

        match = re.search(r'/playerlevelrewards/(0x[0-9A-Z]+)_Border', level.get('style'))
        base_level = level_ids[match.group(1)]

        return base_level + int(level.text_content().strip())

    def extract_competitive_rank(self, tree):
        competitive_rank = tree.find('.//*[@class="competitive-rank"]')
        if competitive_rank is None: # not played competitive mode or not completed placement matches
            return None
        
        return int(competitive_rank.text_content().strip())

    def extract_time_played_ratios(self, tree, play_mode):
        play = self.extract_play(tree, play_mode)
        if play is None:
            raise ValueError('cannot extract the {play_mode} play'.format(play_mode))

        time_played = play.xpath('.//div[@data-group-id="comparisons" and @data-category-id="overwatch.guid.0x0860000000000021"]')[0]

        output = dict()
        for item in time_played.xpath('.//*[contains(@class, "progress-category-item")]'):
            match = re.search(r'/(0x[0-9A-Z]+)\.png$', item.find('img').get('src'))
            
            hero = inverted_hero_category_ids[match.group(1)]
            ratio = float(item.get('data-overwatch-progress-percent'))
            
            output[hero] = ratio
        
        return output

    def extract_stats(self, tree, play_mode, category_id):
        play = self.extract_play(tree, play_mode)
        if play is None:
            return None 

        stats = play.xpath('.//div[@data-group-id="stats" and @data-category-id="{category_id}"]'.format(
            category_id=category_id
        ))
        if not stats: # e.g. not played a cetain hero
            return None
        
        stats = stats[0]

        output = dict()
        for row in stats.findall('.//tbody//tr'):
            name, value = row.findall('.//td')
            output[self.underscorize_stat_name(name.text_content().strip())] = self.parse_stat_value(value.text_content().strip())
        
        return output
    
    async def make_request_and_update(self, name):
        details = await self.query(name)
        self.upstream('firebaseservice').exposed_patch_ow_account_multiple(name, {'level' : details.get('level', 0), 'rank' : details.get('competitive_rank', 'Unranked') })

        
    def exposed_update_account(self, name):
        self.loop.run_until_complete(self.make_request_and_update(name))

    async def query(self, battle_tag, platform='pc', region='us', sem=asyncio.Semaphore(1)):
        response = None
        async with aiohttp.ClientSession() as session:
            response = await session.get(self.stats.format(platform=platform, region=region, battle_tag=battle_tag.replace('#', '-')))
            if response.status == 404:
                raise ValueError('cannot find the player {battle_tag}'.format(battle_tag=battle_tag))
            response = await response.text()
        tree = lxml.html.fromstring(response)
        output = dict()
        output['level'] = self.extract_level(tree)
        competitive_rank = self.extract_competitive_rank(tree)
        if competitive_rank:
            output['competitive_rank'] = competitive_rank

        for mode in ('quick', 'competitive'):
            if not self.has_played(tree, mode):
                continue
                
            output[mode] = {
                'overall': dict(),
                'heroes': dict()
            }
            
            # overall
            output[mode]['overall'] = self.extract_stats(tree, mode, overall_category_id)
                    
            # heroes
            time_played_ratios = self.extract_time_played_ratios(tree, mode)
            for hero, category_id in hero_category_ids.items():
                if not self.has_played(tree, mode, category_id):
                    continue
                
                output[mode]['heroes'][hero] = self.extract_stats(tree, mode, category_id)
                # extra stat
                output[mode]['heroes'][hero]['time_played_ratio'] = time_played_ratios[hero]
        print(output)
        return output




#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
from typing import Optional, Dict, List
import os
from datetime import datetime
import json
import time
from enum import Enum
from bs4 import BeautifulSoup

class AnimeSource(Enum):
    BILIBILI = "bilibili"
    ANILIST = "anilist"
    MAL = "myanimelist"
    BANGUMI = "bangumi"
    ANIDB = "anidb"
    # FANBOX = "fanbox"    # 添加 Fanbox 源

    
class AnimeDownloader:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.sources = {
            AnimeSource.BILIBILI: self._get_bili_cover,
            AnimeSource.ANILIST: self._get_anilist_cover,
            AnimeSource.BANGUMI: self._get_bangumi_cover,
            AnimeSource.MAL: self._get_mal_cover,
            AnimeSource.ANIDB: self._get_anidb_cover
            # AnimeSource.FANBOX: self._get_fanbox_cover,
        }
        self.delays = {
            AnimeSource.BILIBILI: 2,
            AnimeSource.ANILIST: 1,
            AnimeSource.BANGUMI: 1,
            AnimeSource.MAL: 3,
            AnimeSource.ANIDB: 2
            # AnimeSource.FANBOX: 2,
        }
        self.session = requests.Session()  # 添加session复用

    def _get_bili_cover(self, anime_name: str) -> Optional[dict]:
        """从Bilibili获取封面"""
        url = 'https://api.bilibili.com/x/web-interface/search/type'
        params = {
            'search_type': 'media_bangumi',
            'keyword': anime_name,
        }
        headers = {
            **self.headers,
            'Referer': 'https://www.bilibili.com',
            'Origin': 'https://www.bilibili.com',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Cookie': 'buvid3=random-string;',  # 添加基本Cookie
        }

        try:
            # 使用 session 保持连接状态
            session = requests.Session()
            session.headers.update(headers)
            
            # 首先访问主页面获取必要的 Cookie
            session.get('https://www.bilibili.com')
            time.sleep(2)  # 增加延迟
            
            response = session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data['code'] == 0 and data['data'].get('result'):
                anime = data['data']['result'][0]
                return {
                    'url': anime['cover'].replace('http:', 'https:'),
                    'title': anime['title'],
                    'source': AnimeSource.BILIBILI.value
                }
        except Exception as e:
            print(f"Bilibili获取失败: {str(e)}")
        return None

    def _get_anilist_cover(self, anime_name: str) -> Optional[dict]:
        """从AniList获取封面"""
        query = '''
        query ($search: String) {
            Media (search: $search, type: ANIME) {
                coverImage { extraLarge large }
                title { native romaji }
            }
        }
        '''
        try:
            response = requests.post(
                'https://graphql.anilist.co',
                json={'query': query, 'variables': {'search': anime_name}},
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            media = data['data']['Media']
            return {
                'url': media['coverImage'].get('extraLarge') or media['coverImage'].get('large'),
                'title': media['title'].get('native') or media['title'].get('romaji'),
                'source': AnimeSource.ANILIST.value
            }
        except Exception as e:
            print(f"AniList获取失败: {str(e)}")
        return None

    def _get_bangumi_cover(self, anime_name: str) -> Optional[dict]:
        """从 Bangumi 获取封面"""
        try:
            url = f'https://api.bgm.tv/search/subject/{anime_name}'
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            if data and data['list']:
                anime = data['list'][0]
                return {
                    'url': anime['images']['large'],
                    'title': anime['name'],
                    'source': AnimeSource.BANGUMI.value
                }
        except Exception as e:
            print(f"Bangumi获取失败: {str(e)}")
        return None

    def _get_mal_cover(self, anime_name: str) -> Optional[dict]:
        """从MyAnimeList获取封面"""
        try:
            search_url = f"https://myanimelist.net/anime.php?q={anime_name}"
            response = requests.get(search_url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            anime_link = soup.select_one('a.hoverinfo_trigger')
            if anime_link:
                detail_url = anime_link['href']
                detail_response = requests.get(detail_url, headers=self.headers)
                detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
                
                img = detail_soup.select_one('img[itemprop="image"]')
                if img:
                    return {
                        'url': img['src'],
                        'title': anime_link.text.strip(),
                        'source': AnimeSource.MAL.value
                    }
        except Exception as e:
            print(f"MAL获取失败: {str(e)}")
        return None

    def _get_anidb_cover(self, anime_name: str) -> Optional[dict]:
        """从AniDB获取封面"""
        try:
            search_url = f"https://anidb.net/anime/?adb.search={anime_name}&do.search=1"
            response = requests.get(search_url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            anime_item = soup.select_one('.thumb_anime')
            if anime_item:
                img = anime_item.select_one('img')
                title = anime_item.select_one('.anime_title')
                if img and title:
                    return {
                        'url': 'https://cdn.anidb.net' + img['src'],
                        'title': title.text.strip(),
                        'source': AnimeSource.ANIDB.value
                    }
        except Exception as e:
            print(f"AniDB获取失败: {str(e)}")
        return None

    def download_image(self, url: str, anime_name: str, source: str) -> Optional[str]:
        """下载图片"""
        try:
            # 下载前添加延迟
            time.sleep(1)
            response = requests.get(url, headers=self.headers, stream=True)
            response.raise_for_status()
            
            os.makedirs('covers', exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'covers/{anime_name}_{source}_{timestamp}.jpg'
            
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return filename
        except Exception as e:
            print(f"下载失败: {str(e)}")
            return None

    def get_covers(self, anime_name: str, sources: List[AnimeSource] = None) -> List[Dict]:
        """从多个来源获取封面"""
        if sources is None:
            sources = list(AnimeSource)
        
        results = []
        for source in sources:
            if source in self.sources:
                print(f"从 {source.value} 获取封面...")
                # 添加延迟
                delay = self.delays.get(source, 1)
                time.sleep(delay)
                result = self.sources[source](anime_name)
                if result:
                    results.append(result)
                
                # 源之间添加额外延迟
                if len(results) > 0:
                    time.sleep(1)
        return results

def main():
    downloader = AnimeDownloader()
    anime_name = input("请输入动漫名称: ")
    
    results = downloader.get_covers(anime_name)
    if not results:
        print("未找到任何封面")
        return

    print(f"\n找到 {len(results)} 个封面:")
    for result in results:
        print(f"\n从 {result['source']} 下载中...")
        saved_path = downloader.download_image(
            result['url'],
            anime_name,
            result['source']
        )
        if saved_path:
            size_mb = os.path.getsize(saved_path) / (1024 * 1024)
            print(f"标题: {result['title']}")
            print(f"保存到: {saved_path}")
            print(f"文件大小: {size_mb:.2f}MB")

if __name__ == "__main__":
    main()
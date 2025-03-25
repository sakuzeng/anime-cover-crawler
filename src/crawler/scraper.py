#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
from typing import Optional, Dict
import os
from datetime import datetime
import json
import re

def get_anime_cover(anime_name: str) -> Optional[dict]:
    query = '''
    query ($search: String) {
        Media (search: $search, type: ANIME) {
            coverImage {
                extraLarge
                large
            }
            title {
                native
                romaji
            }
        }
    }
    '''
    
    variables = {
        'search': anime_name
    }
    
    url = 'https://graphql.anilist.co'
    response = requests.post(url, json={'query': query, 'variables': variables})
    
    if response.status_code == 200:
        data = response.json()
        media = data['data']['Media']
        cover_url = media['coverImage'].get('extraLarge') or media['coverImage'].get('large')
        return {
            'url': cover_url,
            'title': media['title'].get('native') or media['title'].get('romaji')
        }
    return None

def get_bili_cover(anime_name: str) -> Optional[dict]:
    """从Bilibili获取动漫封面"""
    url = 'https://api.bilibili.com/x/web-interface/search/type'
    params = {
        'search_type': 'media_bangumi',
        'keyword': anime_name,
    }
    
    # 更新请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://www.bilibili.com',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cookie': 'CURRENT_FNVAL=4048;',  # 可以添加你的Cookie
        'Origin': 'https://www.bilibili.com',
        'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"'
    }

    try:
        # 添加延迟，避免请求过快
        import time
        time.sleep(1)
        
        session = requests.Session()
        response = session.get(
            url, 
            params=params, 
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        if data['code'] == 0 and data['data'].get('result'):
            anime = data['data']['result'][0]
            return {
                'url': anime['cover'].replace('http:', 'https:'),  # 确保使用HTTPS
                'title': anime['title'],
                'season_id': anime.get('season_id', ''),
                'media_id': anime.get('media_id', ''),
                'source': 'bilibili'
            }
    except requests.exceptions.RequestException as e:
        print(f"网络请求错误: {str(e)}")
    except json.JSONDecodeError as e:
        print(f"解析响应数据失败: {str(e)}")
    except Exception as e:
        print(f"未知错误: {str(e)}")
    return None

# 添加重试机制的装饰器
def retry_on_failure(max_retries=3, delay=2):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for i in range(max_retries):
                try:
                    result = func(*args, **kwargs)
                    if result:
                        return result
                except Exception as e:
                    print(f"第 {i+1} 次尝试失败: {str(e)}")
                    if i < max_retries - 1:
                        time.sleep(delay)
                    continue
            return None
        return wrapper
    return decorator

# 使用装饰器
@retry_on_failure(max_retries=3, delay=2)
def get_bili_cover_with_retry(anime_name: str) -> Optional[dict]:
    return get_bili_cover(anime_name)

def download_cover(url: str, anime_name: str, source: str = '') -> str:
    """下载封面图片"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.bilibili.com'
    }
    
    try:
        response = requests.get(url, headers=headers, stream=True)
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
        print(f"下载图片时出错: {str(e)}")
        return ''

def start_scraping(anime_name: str = None) -> None:
    """开始爬取流程"""
    if not anime_name:
        anime_name = input("请输入动漫名称: ")
    
    print(f"正在搜索: {anime_name}")
    
    # 从Bilibili获取
    result = get_bili_cover_with_retry(anime_name)
    
    if result:
        print(f"在Bilibili找到: {result['title']}")
        print(f"剧集ID: {result['season_id']}")
        print("正在下载封面...")
        
        saved_path = download_cover(
            result['url'], 
            anime_name,
            'bilibili'
        )
        
        if saved_path:
            print(f"封面已保存到: {saved_path}")
            size_mb = os.path.getsize(saved_path) / (1024 * 1024)
            print(f"文件大小: {size_mb:.2f}MB")
        else:
            print("下载失败")
    else:
        print("未找到动漫信息")
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
from PIL import Image
import io
from tqdm import tqdm
# 添加4kvm依赖库
from urllib.parse import quote
import re
import random
# 相似度
from fuzzywuzzy import fuzz
# 添加ayf依赖库
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# from dotenv import load_dotenv
# # 加载 .env 文件
# load_dotenv()

class AnimeSource(Enum):
    BILIBILI = "bilibili"
    ANILIST = "anilist"
    MAL = "myanimelist"
    BANGUMI = "bangumi"
    ANIDB = "anidb"
    FOURKVM = "4kvm"# 新增 4kvm 数据源
    IYF = "iyf"  # 新增 iyf 数据源

    
class AnimeDownloader:
    def __init__(self):
        # 初始化http对话
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.sources = {
            # AnimeSource.BILIBILI: self._get_bili_cover,
            # AnimeSource.ANILIST: self._get_anilist_cover,
            # AnimeSource.BANGUMI: self._get_bangumi_cover,
            # AnimeSource.MAL: self._get_mal_cover,
            # AnimeSource.ANIDB: self._get_anidb_cover,
            # AnimeSource.FOURKVM: self._get_4kvm_cover,
            AnimeSource.IYF: self._get_iyf_cover
        }
        # 定义延迟
        self.delays = {
            AnimeSource.BILIBILI: 2,
            AnimeSource.ANILIST: 1,
            AnimeSource.BANGUMI: 1,
            AnimeSource.MAL: 3,
            AnimeSource.ANIDB: 2,
            AnimeSource.FOURKVM: 2,
            AnimeSource.IYF: 2
        }
        # 添加session复用
        self.session = requests.Session()  
        # 确保 temp_result 目录存在，用于保存 HTML
        self.output_dir = "temp_html"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        # 相似度阈值，用于选择最相似标题
        self.similarity_threshold = 70
    def _get_random_user_agent(self) -> str:
        """返回随机用户代理，模拟不同浏览器，应对用户代理检测"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
        ]
        return random.choice(user_agents)
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
                img_url = anime['cover'].replace('http:', 'https:')
                size, file_size = self._get_image_info(img_url)
                
                return {
                    'url': img_url,
                    'title': anime['title'],
                    'source': AnimeSource.BILIBILI.value,
                    'resolution': size,
                    'file_size': file_size,
                    'quality_score': size[0] * size[1] * file_size
                }
        except Exception as e:
            print(f"Bilibili获取失败: {str(e)}")
        return None

    def _get_anilist_cover(self, anime_name: str) -> Optional[dict]:
        """从 AniList 搜索页面获取封面"""
        try:
            # 构造搜索 URL
            search_url = f"https://anilist.co/search/anime?search={anime_name}"
            response = self.session.get(search_url, headers=self.headers)
            response.raise_for_status()
            
            # 使用 BeautifulSoup 解析 HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            anime_item = soup.select_one('.media-card')  # 根据实际 HTML 结构调整选择器
            if anime_item:
                img = anime_item.select_one('img')
                title = anime_item.select_one('.title')
                if img and title:
                    img_url = img['src']
                    size, file_size = self._get_image_info(img_url)
                    
                    return {
                        'url': img_url,
                        'title': title.text.strip(),
                        'source': AnimeSource.ANILIST.value,
                        'resolution': size,
                        'file_size': file_size,
                        'quality_score': size[0] * size[1] * file_size
                    }
        except Exception as e:
            print(f"AniList 获取失败: {str(e)}")
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
                img_url = anime['images']['large']
                size, file_size = self._get_image_info(img_url)
                
                return {
                    'url': img_url,
                    'title': anime['name'],
                    'source': AnimeSource.BANGUMI.value,
                    'resolution': size,
                    'file_size': file_size,
                    'quality_score': size[0] * size[1] * file_size
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
                    img_url = img['src']
                    size, file_size = self._get_image_info(img_url)
                    
                    return {
                        'url': img_url,
                        'title': anime_link.text.strip(),
                        'source': AnimeSource.MAL.value,
                        'resolution': size,
                        'file_size': file_size,
                        'quality_score': size[0] * size[1] * file_size
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
                    img_url = 'https://cdn.anidb.net' + img['src']
                    size, file_size = self._get_image_info(img_url)
                    
                    return {
                        'url': img_url,
                        'title': title.text.strip(),
                        'source': AnimeSource.ANIDB.value,
                        'resolution': size,
                        'file_size': file_size,
                        'quality_score': size[0] * size[1] * file_size
                    }
        except Exception as e:
            print(f"AniDB获取失败: {str(e)}")
        return None

    def _get_4kvm_cover(self, anime_name: str) -> Optional[Dict]:
        """从 4kvm.net 获取动漫封面，支持完全匹配和最相似匹配"""
        try:
            # 随机延迟，防止频率限制
            time.sleep(random.uniform(self.delays.get(AnimeSource.FOURKVM, 1), 3))
            # 更新用户代理
            self.headers['User-Agent'] = self._get_random_user_agent()
            # 更新 Referer
            self.headers['Referer'] = 'https://www.4kvm.net/'
            # 访问主页获取 cookies
            print("访问 4kvm 主页获取 cookies...")
            homepage_response = self.session.get('https://www.4kvm.net', headers=self.headers, timeout=10)
            homepage_response.raise_for_status()
            print(f"主页响应状态码: {homepage_response.status_code}, Cookies: {list(self.session.cookies.keys())}")
            # URL 编码动漫名称
            encoded_name = quote(anime_name)
            search_url = f"https://www.4kvm.net/xssearch?s={encoded_name}"
            print(f"请求 4kvm 搜索: {search_url}")
            # 发送搜索请求
            response = self.session.get(search_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            print(f"搜索响应状态码: {response.status_code}")
            # 保存 HTML
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_anime_name = re.sub(r'[^\w\-]', '_', anime_name)
            html_filename = os.path.join(self.output_dir, f"{safe_anime_name}_{timestamp}_4kvm.html")
            with open(html_filename, 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"HTML 保存至: {html_filename}")
            # 解析 HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.select_one('title').text if soup.select_one('title') else '无标题'
            print(f"页面标题: {title}")
            # 查找搜索结果条目
            anime_items = soup.select('.result-item article')
            print(f"找到 {len(anime_items)} 个 .result-item 条目")
            
            best_match = None
            highest_similarity = 0
            
            for item in anime_items:
                # 获取封面图片和标题
                img = item.select_one('.thumbnail img')
                title_elem = item.select_one('.details .title a')
                if img and title_elem:
                    img_url = img.get('data-src', img['src'])
                    title = title_elem.text.strip().replace("'", "_")  # 替换单引号
                    # 计算标题与输入的相似度
                    similarity = fuzz.ratio(anime_name.lower(), title.lower())
                    print(f"4kvm: 标题 '{title}', 相似度: {similarity}")
                    
                    # 完全匹配
                    if re.search(re.escape(anime_name), title, re.IGNORECASE):
                        size, file_size = self._get_image_info(img_url)
                        result = {
                            'url': img_url,
                            'title': title,
                            'source': AnimeSource.FOURKVM.value,
                            'resolution': size,
                            'file_size': file_size,
                            'quality_score': size[0] * size[1] * file_size
                        }
                        print(f"4kvm: 抓取成功（完全匹配）: {result['url']}")
                        return result
                    # 记录最高相似度
                    if similarity > highest_similarity:
                        highest_similarity = similarity
                        size, file_size = self._get_image_info(img_url)
                        best_match = {
                            'url': img_url,
                            'title': title,
                            'source': AnimeSource.FOURKVM.value,
                            'resolution': size,
                            'file_size': file_size,
                            'quality_score': size[0] * size[1] * file_size
                        }
                else:
                    print("4kvm: 条目缺少图片或标题")
            
            # 无完全匹配，返回最相似结果
            if best_match and highest_similarity >= self.similarity_threshold:
                print(f"4kvm: 无完全匹配，选择最相似标题 '{best_match['title']}'（相似度: {highest_similarity}）")
                return best_match
            print("4kvm: 未找到匹配的动漫条目")
        
        except requests.ConnectionError:
            print("4kvm: 网络连接失败")
        except requests.Timeout:
            print("4kvm: 请求超时")
        except requests.HTTPError as e:
            print(f"4kvm: HTTP 错误: {e}")
        except Exception as e:
            print(f"4kvm 获取失败: {str(e)}")
        return None
    
    def _get_iyf_cover(self, anime_name: str) -> Optional[Dict]:
        """从 iyf.tv 获取封面，使用 Selenium 处理动态加载，添加代理，支持完全匹配和最相似匹配"""
        driver = None
        try:
            # # 从 .env 文件获取代理
            # proxy = os.getenv("PROXY")
            # if not proxy:
            #     raise ValueError("未在 .env 文件中配置 PROXY，请设置 PROXY=http://your_proxy_host:your_proxy_port")
            # print(f"使用代理: {proxy}")

            # 随机延迟，防止频率限制
            time.sleep(random.uniform(self.delays.get(AnimeSource.IYF, 1), 3))
            # 配置 Selenium，模拟真实浏览器

            options = Options()
            options.headless = True  # 无头模式
            options.add_argument(f"user-agent={self._get_random_user_agent()}")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")  # 隐藏 Selenium 特征
            # 添加代理
            # options.add_argument(f"--proxy-server={proxy}")


            # 重试机制，最多尝试 3 次
            for attempt in range(3):
                try:
                    # 使用 ChromeDriverManager 自动管理 ChromeDriver
                    service = Service(ChromeDriverManager().install())
                    driver = webdriver.Chrome(service=service, options=options)
                    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
                    # 访问主页获取 cookies
                    print("访问 iyf.tv 主页获取 cookies...")
                    driver.get('https://www.iyf.tv')
                    time.sleep(5)  # 延长等待时间
                    cookies = driver.get_cookies()
                    print(f"主页 Cookies: {[cookie['name'] for cookie in cookies]}")
                    # 搜索页面
                    encoded_name = quote(anime_name)
                    search_url = f"https://www.iyf.tv/search/{encoded_name}"
                    print(f"使用 Selenium 请求 iyf.tv 搜索: {search_url}")
                    driver.get(search_url)
                    time.sleep(7)  # 延长等待动态加载
                    # 模拟滚动以确保内容加载
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    # 解析页面
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    break
                except Exception as e:
                    if attempt == 2:
                        raise Exception(f"重试 3 次后仍失败: {str(e)}")
                    print(f"请求失败，重试 {attempt + 1}/3: {str(e)}")
                    if driver:
                        driver.quit()
                    time.sleep(random.uniform(2, 5))
            # 保存 HTML
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_anime_name = re.sub(r'[^\w\-]', '_', anime_name)
            html_filename = os.path.join(self.output_dir, f"{safe_anime_name}_{timestamp}_iyf.html")
            with open(html_filename, 'w', encoding='utf-8') as f:
                f.write(soup.prettify())
            print(f"HTML 保存至: {html_filename}")
            # 输出页面标题
            title = soup.select_one('title').text if soup.select_one('title') else '无标题'
            print(f"页面标题: {title}")
            # 查找搜索结果条目（假设选择器）
            anime_items = soup.select('.video-item, .item, .search-result-item, .search-item')
            print(f"找到 {len(anime_items)} 个搜索条目")
            
            best_match = None
            highest_similarity = 0
            
            for item in anime_items:
                # 获取封面图片和标题
                img = item.select_one('img')
                title_elem = item.select_one('.title, h3, a')
                if img and title_elem:
                    img_url = img.get('data-src', img['src'])
                    title = title_elem.text.strip().replace("'", "_")  # 替换单引号
                    # 计算相似度
                    similarity = fuzz.ratio(anime_name.lower(), title.lower())
                    print(f"iyf: 标题 '{title}', 相似度: {similarity}")
                    
                    # 完全匹配或部分匹配 anime_name 的子字符串
                    # 完全匹配：标题包含完整 anime_name
                    # 部分匹配：标题包含 anime_name 的任意子字符串（至少 2 个字符）
                    if (re.search(re.escape(anime_name), title, re.IGNORECASE) or
                        any(re.search(re.escape(word), title, re.IGNORECASE) 
                            for word in anime_name.split() if len(word) >= 2)):
                        size, file_size = self._get_image_info(img_url)
                        result = {
                            'url': img_url,
                            'title': title,
                            'source': AnimeSource.IYF.value,
                            'resolution': size,
                            'file_size': file_size,
                            'quality_score': size[0] * size[1] * file_size
                        }
                        print(f"iyf: 抓取成功（完全或部分匹配）: {result['url']}")
                        return result
                    # 记录最高相似度
                    if similarity > highest_similarity:
                        highest_similarity = similarity
                        size, file_size = self._get_image_info(img_url)
                        best_match = {
                            'url': img_url,
                            'title': title,
                            'source': AnimeSource.IYF.value,
                            'resolution': size,
                            'file_size': file_size,
                            'quality_score': size[0] * size[1] * file_size
                        }
                else:
                    print("iyf: 条目缺少图片或标题")
            
            # 无完全匹配，返回最相似结果
            if best_match and highest_similarity >= self.similarity_threshold:
                print(f"iyf: 无完全匹配，选择最相似标题 '{best_match['title']}'（相似度: {highest_similarity}）")
                return best_match
            print("iyf: 未找到匹配的动漫条目")
        
        except Exception as e:
            print(f"iyf 获取失败: {str(e)}")
        finally:
            if driver:
                driver.quit()
        return None
    
    def _get_image_info(self, url: str) -> tuple:
        """获取图片信息（尺寸和文件大小）"""
        try:
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            img = Image.open(io.BytesIO(response.content))
            size = img.size
            file_size = len(response.content) / (1024 * 1024)  # MB
            return size, file_size
        except Exception as e:
            print(f"获取图片信息失败: {str(e)}")
            return (0, 0), 0

    def download_image(self, url: str, anime_name: str, source: str) -> Optional[str]:
        """下载图片并显示进度"""
        try:
            time.sleep(1)
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            os.makedirs('covers', exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'covers/{anime_name}_{source}_{timestamp}.jpg'
            
            with open(filename, 'wb') as f:
                with tqdm(
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    desc=f"下载 {source} 封面"
                ) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
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
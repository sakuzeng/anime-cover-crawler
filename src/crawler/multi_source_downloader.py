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
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
# 翻译依赖库
# from deep_translator import GoogleTranslator
# from googletrans import Translator
# import pykakasi

import logging
# 导入.env
from dotenv import load_dotenv
# 导入工具函数
from utils.helpers import clean_title, normalize_title

# 加载 .env 文件
load_dotenv()
# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AnimeSource(Enum):
    FOURKVM = "4kvm"# 新增 4kvm 数据源

    BILIBILI = "bilibili"
    BANGUMI = "bangumi"
    MAL = "myanimelist"
    ANIDB = "anidb"

    IYF = "iyf"  # 新增 iyf 数据源 没有直接的html文件进行爬取
    ANILIST = "anilist" #搜索时需要罗马音，暂未解决，且没有直接的html文件进行爬取
    
class AnimeDownloader:
    def __init__(self):
        self.headers = {}
        self.sources = {
            # AnimeSource.FOURKVM: self._get_4kvm_cover,
            # AnimeSource.BILIBILI: self._get_bili_cover,
            # AnimeSource.BANGUMI: self._get_bangumi_cover,、
            # AnimeSource.ANILIST: self._get_anilist_cover,
            # AnimeSource.MAL: self._get_mal_cover,
            # AnimeSource.ANIDB: self._get_anidb_cover,
            # AnimeSource.IYF: self._get_iyf_cover，

        }
        # 定义延迟
        self.delays = {
            AnimeSource.BILIBILI: 2,
            # AnimeSource.ANILIST: 1,
            AnimeSource.BANGUMI: 1,
            AnimeSource.MAL: 3,
            AnimeSource.ANIDB: 2,
            AnimeSource.FOURKVM: 2
            # AnimeSource.IYF: 2
        }
        # 添加session复用
        self.session = requests.Session()  
        # 确保 temp_result 目录存在，用于保存 HTML
        self.output_dir = "temp_html"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        # 相似度阈值，用于提供url
        self.similarity_threshold = 90


        # 设置 Clash 代理
        # 从环境变量中读取代理配置
        # http_proxy = os.getenv("HTTP_PROXY")
        # https_proxy = os.getenv("HTTPS_PROXY")
        # # self.proxy = PROXY  # 默认使用 Clash 的 HTTP 代理
        # self.proxies = {
        #     'http': http_proxy,
        #     'https': https_proxy,
        # }
        # self.session.proxies.update(self.proxies)
        # print(f"使用代理: {self.proxies}")
        # # 初始化翻译和罗马音转换工具
        # self.translator = GoogleTranslator(source='zh-CN', target='ja',proxies=self.proxies)
        # self.kks = pykakasi.kakasi()

    def _chinese_to_romanized(self, chinese_title: str) -> str:
            """
            将中文标题转换为罗马音（同步版本）。

            Args:
                chinese_title: 中文标题。

            Returns:
                罗马音标题，若转换失败则返回原标题。
            """
            try:
                # 中文 -> 日文
                japanese_title = self.translator.translate(chinese_title)
                print(f"中文标题 '{chinese_title}' 转换为日文: {japanese_title}")
                # 日文 -> 罗马音
                result = self.kks.convert(japanese_title)
                romanized_title = ' '.join(item['hepburn'] for item in result).capitalize()
                print(f"日文 '{japanese_title}' 转换为罗马音: {romanized_title}")
                return romanized_title
            except Exception as e:
                print(f"标题转换失败: {str(e)}，使用原标题: {chinese_title}")
                return chinese_title

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

    def _get_bangumi_cover(self, anime_name: str, min_similarity: int = 90, max_similarity: int = 100, delay: float = 1.0) -> Optional[dict]:
        """
        从 Bangumi API 获取动漫封面，支持相似度筛选和图片质量排序。

        Args:
            anime_name (str): 动漫名称。
            min_similarity (int): 标题相似度最小阈值（默认90）。
            max_similarity (int): 标题相似度最大阈值（默认100）。
            delay (float): 请求前的随机延迟时间（秒，默认1.0）。

        Returns:
            Optional[dict]: 包含封面信息的字典（URL、标题、来源等），未找到时返回None.

        Raises:
            requests.RequestException: 网络或API请求失败。
        """
        # 验证输入
        if not anime_name or not isinstance(anime_name, str):
            logger.error("无效的动漫名称")
            return None

        try:
            # 随机延迟，防止频率限制
            time.sleep(random.uniform(self.delays.get(AnimeSource.BANGUMI, delay), 3))

            # 更新用户代理
            self.headers['User-Agent'] = self._get_random_user_agent()

            # 构造搜索 URL
            url = f"https://api.bgm.tv/search/subject/{quote(anime_name)}?type=2"
            logger.debug(f"请求 Bangumi 搜索: {url}")

            # 发送搜索请求
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            logger.debug(f"Bangumi 搜索响应状态码: {response.status_code}")

            # 解析 JSON 响应
            data = response.json()
            if not data or not data.get('list'):
                logger.info("Bangumi: 未找到匹配的动漫条目")
                return None

            # 初始化候选列表
            candidates = []

            for item in data['list']:
                # 提取标题和封面图片 URL
                title = item.get('name_cn') or item.get('name', '').strip()
                img_url = item.get('images', {}).get('large')

                if not title or not img_url or not img_url.endswith(('.jpg', '.jpeg', '.png')):
                    continue

                # 清理和标准化标题
                cleaned_title = clean_title(title)
                normalized_title = normalize_title(cleaned_title)

                # 计算标题相似度
                similarity = fuzz.ratio(normalize_title(anime_name), normalized_title)
                logger.debug(f"Bangumi: 标题 '{cleaned_title}', 相似度: {similarity}")

                # 筛选相似度在指定范围内的条目
                min_similarity = self.similarity_threshold
                if min_similarity <= similarity <= max_similarity:
                    try:
                        size, file_size = self._get_image_info(img_url)
                        # 优化质量评分：分辨率 * 文件大小（KB）
                        quality_score = size[0] * size[1] * (file_size / 1024)
                    except Exception as e:
                        logger.warning(f"获取图片信息失败: {str(e)}")
                        quality_score = 0

                    # 存储结果
                    candidate = {
                        'url': img_url,
                        'title': cleaned_title,
                        'source': AnimeSource.BANGUMI,
                        'resolution': size,
                        'file_size': file_size,
                        'quality_score': quality_score,
                        'similarity': similarity
                    }
                    candidates.append(candidate)

            # 如果没有找到任何符合条件的匹配项
            if not candidates:
                logger.info("Bangumi: 未找到符合条件的动漫条目")
                return None

            # 输出所有待选择的结果
            logger.info("Bangumi: 待选择的候选条目：")
            for i, candidate in enumerate(candidates, 1):
                logger.info(
                    f"候选 {i}: 标题='{candidate['title']}', "
                    f"URL={candidate['url']}, "
                    f"相似度={candidate['similarity']}, "
                    f"质量评分={candidate['quality_score']}, "
                    f"分辨率={candidate['resolution']}, "
                    f"文件大小={candidate['file_size']} 字节"
                )

            # 选择质量最高的图片
            best_match = max(candidates, key=lambda x: (x['similarity'], x['quality_score']))
            logger.info(
                f"Bangumi: 选择质量最高的标题 '{best_match['title']}' "
                f"(相似度: {best_match['similarity']}, 质量评分: {best_match['quality_score']})"
            )
            return best_match

        except requests.ConnectionError:
            logger.error("Bangumi: 网络连接失败")
        except requests.Timeout:
            logger.error("Bangumi: 请求超时")
        except requests.HTTPError as e:
            logger.error(f"Bangumi: HTTP 错误: {e}")
        except Exception as e:
            logger.error(f"Bangumi 获取失败: {str(e)}")
        return None

    def _get_bili_cover(self, anime_name: str, min_similarity: int = 90, max_similarity: int = 100, delay: float = 1.0) -> Optional[dict]:
        """
        从Bilibili获取动漫封面，支持相似度排序和图片质量筛选。

        Args:
            anime_name (str): 动漫名称。
            min_similarity (int): 标题相似度最小阈值（默认70）。
            max_similarity (int): 标题相似度最大阈值（默认100）。
            delay (float): 访问主页后的延迟时间（秒，默认1.0）。

        Returns:
            Optional[dict]: 包含封面信息的字典（URL、标题、来源等），未找到时返回None.

        Raises:
            requests.RequestException: 网络或API请求失败。
        """
        # 验证输入
        if not anime_name or not isinstance(anime_name, str):
            logger.error("无效的动漫名称")
            return None

        url = 'https://api.bilibili.com/x/web-interface/search/type'
        params = {
            'search_type': 'media_bangumi',
            'keyword': anime_name,  # URL 编码关键字
        }
        headers = {
            'User-Agent': self._get_random_user_agent(),  # 动态获取随机 User-Agent
            'Referer': 'https://www.bilibili.com',
            'Origin': 'https://www.bilibili.com',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
        }

        try:
            # 使用 session 保持连接状态
            with requests.Session() as session:
                session.headers.update(headers)
                
                # 访问主页面获取 Cookie
                response = session.get('https://www.bilibili.com', timeout=10)
                response.raise_for_status()
                time.sleep(delay)  # 延迟等待 Cookie 加载

                # 发送搜索请求
                response = session.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                # 检查返回数据是否有效
                if data.get('code') != 0 or not data.get('data', {}).get('result'):
                    logger.info("Bilibili: 未找到匹配的动漫条目")
                    return None

                # 初始化候选列表
                candidates = []
                for item in data['data']['result']:
                    # 提取标题和封面图片 URL
                    raw_title = item.get('title', '').strip()
                    img_url = item.get('cover', '').replace('http:', 'https:')

                    # 验证标题和封面 URL
                    if not raw_title or not img_url or not img_url.endswith(('.jpg', '.jpeg', '.png')):
                        continue

                    # 清理和标准化标题
                    cleaned_title = clean_title(raw_title)
                    normalized_title = normalize_title(cleaned_title)

                    # 计算标题相似度
                    similarity = fuzz.ratio(normalize_title(anime_name), normalized_title)
                    logger.debug(f"Bilibili: 标题 '{cleaned_title}', 相似度: {similarity}")

                    # 筛选相似度在指定范围内的条目
                    min_similarity = self.similarity_threshold
                    if min_similarity <= similarity <= max_similarity:
                        try:
                            size, file_size = self._get_image_info(img_url)
                            # 优化质量评分：分辨率 * 文件大小（KB）
                            quality_score = size[0] * size[1] * (file_size / 1024)
                        except Exception as e:
                            logger.warning(f"获取图片信息失败: {str(e)}")
                            quality_score = 0

                        # 存储结果
                        candidate = {
                            'url': img_url,
                            'title': cleaned_title,
                            'source': AnimeSource.BILIBILI,
                            'resolution': size,
                            'file_size': file_size,
                            'quality_score': quality_score,
                            'similarity': similarity
                        }
                        candidates.append(candidate)

                # 如果没有找到任何符合条件的匹配项
                if not candidates:
                    logger.info("Bilibili: 未找到符合条件的动漫条目")
                    return None

                # 输出所有待选择的结果
                logger.info("Bilibili: 待选择的候选条目：")
                for i, candidate in enumerate(candidates, 1):
                    logger.info(
                        f"候选 {i}: 标题='{candidate['title']}', "
                        f"URL={candidate['url']}, "
                        f"相似度={candidate['similarity']}, "
                        f"质量评分={candidate['quality_score']}, "
                        f"分辨率={candidate['resolution']}, "
                        f"文件大小={candidate['file_size']} 字节"
                    )

                # 选择最相似且质量最高的图片
                best_match = max(candidates, key=lambda x: (x['similarity'], x['quality_score']))
                logger.info(
                    f"Bilibili: 选择最相似且质量最高的标题 '{best_match['title']}' "
                    f"(相似度: {best_match['similarity']}, 质量评分: {best_match['quality_score']})"
                )
                return best_match

        except requests.ConnectionError:
            logger.error("Bilibili: 网络连接失败")
        except requests.Timeout:
            logger.error("Bilibili: 请求超时")
        except requests.HTTPError as e:
            logger.error(f"Bilibili: HTTP 错误: {e}")
        except Exception as e:
            logger.error(f"Bilibili 获取失败: {str(e)}")
        return None
    
    def _get_anilist_cover(self, anime_name: str, min_similarity: int = 90, max_similarity: int = 100, delay: float = 1.0) -> Optional[Dict]:
        """
        从 AniList GraphQL API 获取动漫封面，支持相似度筛选和图片质量排序。

        Args:
            anime_name (str): 动漫名称（支持中文、英文等）。
            min_similarity (int): 标题相似度最小阈值（默认90）。
            max_similarity (int): 标题相似度最大阈值（默认100）。
            delay (float): 请求前的随机延迟时间（秒，默认1.0）。

        Returns:
            Optional[Dict]: 包含封面信息的字典（URL、标题、来源等），未找到时返回None.

        Raises:
            requests.RequestException: 网络或API请求失败。
        """
        # 验证输入
        if not anime_name or not isinstance(anime_name, str):
            logger.error("无效的动漫名称")
            return None

        try:
            # 随机延迟
            time.sleep(random.uniform(self.delays.get(AnimeSource.ANILIST, delay), 3))

            # 构造 GraphQL 查询
            query = """
            query ($search: String) {
                Page(page: 1, perPage: 10) {
                    media(search: $search, type: ANIME) {
                        coverImage { large }
                        title { romaji english native }
                        synonyms
                    }
                }
            }
            """
            variables = {"search": anime_name}
            self.headers['User-Agent'] = self._get_random_user_agent()
            logger.debug(f"AniList: 发送 GraphQL 查询，搜索标题: {anime_name}")

            # 发送请求
            response = self.session.post(
                "https://graphql.anilist.co",
                json={"query": query, "variables": variables},
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            logger.debug(f"AniList: 响应状态码: {response.status_code}")

            # 解析响应
            data = response.json()
            media_list = data.get('data', {}).get('Page', {}).get('media', [])
            if not media_list:
                logger.info("AniList: 未找到匹配的动漫条目")
                return None

            # 初始化候选列表
            candidates = []

            # 清理和标准化输入标题
            cleaned_anime_name = clean_title(anime_name)
            normalized_anime_name = normalize_title(cleaned_anime_name)

            for media in media_list:
                img_url = media.get('coverImage', {}).get('large')
                main_title = (
                    media.get('title', {}).get('romaji')
                    or media.get('title', {}).get('english')
                    or media.get('title', {}).get('native')
                )
                if not main_title or not img_url or not img_url.endswith(('.jpg', '.jpeg', '.png')):
                    continue

                main_title = main_title.strip().replace("'", "_")
                aliases = media.get('synonyms', [])
                all_titles = [main_title] + [alias.strip().replace("'", "_") for alias in aliases]

                # 清理和标准化主标题
                cleaned_title = clean_title(main_title)
                normalized_title = normalize_title(cleaned_title)

                # 计算主标题的模糊相似度
                similarity = fuzz.ratio(normalized_anime_name, normalized_title)
                logger.debug(f"AniList: 标题 '{cleaned_title}', 模糊相似度: {similarity}")

                # 检查完全匹配（主标题或别名）
                is_exact_match = False
                for title in all_titles:
                    cleaned_alias = clean_title(title)
                    normalized_alias = normalize_title(cleaned_alias)
                    if normalized_anime_name == normalized_alias:
                        is_exact_match = True
                        break

                # 获取图片信息
                try:
                    size, file_size = self._get_image_info(img_url)
                    quality_score = size[0] * size[1] * (file_size / 1024)
                except Exception as e:
                    logger.warning(f"获取图片信息失败: {str(e)}")
                    quality_score = 0

                # 创建候选条目
                candidate = {
                    'url': img_url,
                    'title': cleaned_title,
                    'source': AnimeSource.ANILIST,
                    'resolution': size,
                    'file_size': file_size,
                    'quality_score': quality_score,
                    'similarity': 100 if is_exact_match else similarity
                }

                # 添加到候选列表（完全匹配或模糊匹配满足阈值）
                min_similarity = self.similarity_threshold
                if is_exact_match or (min_similarity <= similarity <= max_similarity):
                    candidates.append(candidate)

            # 如果没有找到任何符合条件的匹配项
            if not candidates:
                logger.info("AniList: 未找到符合条件的动漫条目")
                return None

            # 输出所有待选择的结果
            logger.info("AniList: 待选择的候选条目：")
            for i, candidate in enumerate(candidates, 1):
                logger.info(
                    f"候选 {i}: 标题='{candidate['title']}', "
                    f"URL={candidate['url']}, "
                    f"相似度={candidate['similarity']}, "
                    f"质量评分={candidate['quality_score']}, "
                    f"分辨率={candidate['resolution']}, "
                    f"文件大小={candidate['file_size']} 字节"
                )

            # 选择质量最高的图片
            best_match = max(candidates, key=lambda x: x['quality_score'])
            logger.info(
                f"AniList: 选择质量最高的标题 '{best_match['title']}' "
                f"(相似度: {best_match['similarity']}, 质量评分: {best_match['quality_score']})"
            )
            return best_match

        except requests.ConnectionError:
            logger.error("AniList: 网络连接失败")
            return None
        except requests.Timeout:
            logger.error("AniList: 请求超时")
            return None
        except requests.HTTPError as e:
            logger.error(f"AniList: HTTP 错误: {e}")
            return None
        except Exception as e:
            logger.error(f"AniList 获取失败: {str(e)}")
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
# 未解决搜索源
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


# 工具函数
    def _get_random_user_agent(self) -> str:
        """返回随机用户代理，模拟不同浏览器，应对用户代理检测"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
        ]
        return random.choice(user_agents)
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
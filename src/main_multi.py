#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os  # 添加缺失的导入
from crawler.multi_source_downloader import AnimeDownloader, AnimeSource

def main():
    print("Starting the multi-source anime cover crawler...")
    
    # 创建下载器实例
    downloader = AnimeDownloader()
    
    # 获取动漫名称
    anime_name = sys.argv[1] if len(sys.argv) > 1 else input("请输入动漫名称: ")
    
    # 默认使用所有可用源
    sources = list(AnimeSource)
    
    # 获取并下载封面
    print(f"\n正在搜索: {anime_name}")
    results = downloader.get_covers(anime_name, sources)
    
    if not results:
        print("未找到任何封面")
        return

    # 显示下载结果
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
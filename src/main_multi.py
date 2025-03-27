#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
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

    # 按质量评分排序
    sorted_results = sorted(results, key=lambda x: x.get('quality_score', 0), reverse=True)
    
    # 显示所有找到的封面信息
    print(f"\n找到 {len(results)} 个封面:")
    print("\n按质量排序的结果:")
    for idx, result in enumerate(sorted_results, 1):
        resolution = result.get('resolution', (0, 0))
        file_size = result.get('file_size', 0)
        print(f"\n{idx}. 来源: {result['source']}")
        print(f"   标题: {result['title']}")
        print(f"   分辨率: {resolution[0]}x{resolution[1]}")
        print(f"   文件大小: {file_size:.2f}MB")
        print(f"   质量评分: {result.get('quality_score', 0):.0f}")

    # 询问用户是否只下载最高质量的图片
    download_all = input("\n是否下载所有封面? (y/n, 默认只下载最高质量): ").lower() == 'y'
    
    if download_all:
        download_list = sorted_results
    else:
        download_list = [sorted_results[0]]
        print("\n将只下载最高质量的封面...")

    # 下载选定的封面
    for result in download_list:
        print(f"\n从 {result['source']} 下载中...")
        saved_path = downloader.download_image(
            result['url'],
            anime_name,
            result['source']
        )
        if saved_path:
            print(f"\n下载完成:")
            print(f"标题: {result['title']}")
            print(f"来源: {result['source']}")
            resolution = result.get('resolution', (0, 0))
            print(f"分辨率: {resolution[0]}x{resolution[1]}")
            size_mb = os.path.getsize(saved_path) / (1024 * 1024)
            print(f"文件大小: {size_mb:.2f}MB")
            print(f"保存到: {saved_path}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from crawler.scraper import start_scraping

def main():
    print("Starting the anime cover crawler...")
    anime_name = sys.argv[1] if len(sys.argv) > 1 else input("Enter anime name: ")
    if not anime_name.strip():
        print("Error: Anime name cannot be empty")
        return
    start_scraping(anime_name)

if __name__ == "__main__":
    main()
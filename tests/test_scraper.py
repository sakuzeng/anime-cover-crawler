import unittest
from src.crawler.scraper import scrape_anime_cover  # 假设这是你的抓取函数

class TestScraper(unittest.TestCase):

    def test_scrape_anime_cover(self):
        # 测试抓取功能是否正常
        result = scrape_anime_cover("某个动漫名称")
        self.assertIsNotNone(result)
        self.assertIn("封面链接", result)  # 根据实际返回值调整

if __name__ == '__main__':
    unittest.main()
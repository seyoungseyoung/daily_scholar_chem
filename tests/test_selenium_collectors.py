import unittest
from src.services.selenium_collectors import ArxivCSCollector

class TestArxivCSCollector(unittest.TestCase):
    def test_arxiv_cs_collector(self):
        collector = ArxivCSCollector()
        news_items = collector.collect()
        self.assertIsInstance(news_items, list)
        if news_items:
            self.assertIsNotNone(news_items[0].title)
            self.assertIsNotNone(news_items[0].url)
            self.assertIsNotNone(news_items[0].abstract)
            self.assertIsNotNone(news_items[0].author)
            self.assertIsNotNone(news_items[0].categories)
            self.assertIsNotNone(news_items[0].pdf_url)
            self.assertIsNotNone(news_items[0].html_url)
            self.assertIsNotNone(news_items[0].source_url)

if __name__ == '__main__':
    unittest.main() 
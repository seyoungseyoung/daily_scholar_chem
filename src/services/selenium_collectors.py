import logging
import os
import time
import requests
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import pandas as pd
from ..models.news import News

logger = logging.getLogger(__name__)

class SeleniumBaseCollector:
    def __init__(self, url: str):
        self.url = url
        self.driver = None
        self.download_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'papers')
        os.makedirs(self.download_dir, exist_ok=True)

    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_experimental_option('prefs', {
            'download.default_directory': self.download_dir,
            'download.prompt_for_download': False,
            'download.directory_upgrade': True,
            'safebrowsing.enabled': True
        })
        self.driver = webdriver.Chrome(options=chrome_options)

    def wait_for_element(self, by: By, value: str, timeout: int = 10):
        return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )

    def get_text(self, element) -> str:
        try:
            return element.text.strip()
        except StaleElementReferenceException:
            return ""

    def get_attribute(self, element, attr: str) -> str:
        try:
            return element.get_attribute(attr)
        except StaleElementReferenceException:
            return ""

    def download_pdf(self, url: str, filename: str) -> bool:
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            filepath = os.path.join(self.download_dir, filename)
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return True
        except Exception as e:
            logger.error(f"PDF 다운로드 중 오류 발생: {str(e)}")
            return False

    def cleanup(self):
        if self.driver:
            self.driver.quit()

class ArxivCSCollector(SeleniumBaseCollector):
    def __init__(self):
        super().__init__("https://arxiv.org/list/cs/recent")
        self.max_papers = 3  # 테스트를 위해 3개로 제한
        self.target_categories = [
            'cs.AI', 'cs.CV', 'cs.LG', 'cs.CL', 'cs.NE', 
            'cs.IR', 'cs.ML', 'cs.RO', 'cs.SE', 'cs.SY'
        ]

    def collect_paper_links(self) -> List[str]:
        """논문 링크 수집"""
        try:
            self.setup_driver()
            self.driver.get(self.url)
            
            # 페이지 로딩 대기
            self.wait_for_element(By.CSS_SELECTOR, "dt")
            
            paper_links = []
            skip = 0
            
            while len(paper_links) < self.max_papers:
                # 현재 페이지의 논문 링크 수집
                dt_elements = self.driver.find_elements(By.CSS_SELECTOR, "dt")
                for dt in dt_elements:
                    if len(paper_links) >= self.max_papers:
                        break
                    try:
                        link = dt.find_element(By.CSS_SELECTOR, "a[href*='/abs/']")
                        paper_links.append(link.get_attribute("href"))
                    except (NoSuchElementException, StaleElementReferenceException):
                        continue
                
                # 다음 페이지로 이동
                if len(paper_links) < self.max_papers:
                    skip += 25
                    self.driver.get(f"{self.url}?skip={skip}")
                    self.wait_for_element(By.CSS_SELECTOR, "dt")
            
            return paper_links[:self.max_papers]
            
        except Exception as e:
            logger.error(f"논문 링크 수집 중 오류: {str(e)}")
            return []
        finally:
            self.cleanup()

    def get_paper_details(self, url: str) -> Dict[str, Any]:
        """개별 논문 상세 정보 수집"""
        try:
            self.setup_driver()
            self.driver.get(url)
            
            # 페이지 로딩 대기
            self.wait_for_element(By.CSS_SELECTOR, "h1.title")
            
            # 제목 추출
            title = self.get_text(self.driver.find_element(By.CSS_SELECTOR, "h1.title"))
            
            # 저자 추출
            authors = self.get_text(self.driver.find_element(By.CSS_SELECTOR, "div.authors"))
            
            # 초록 추출
            abstract = self.get_text(self.driver.find_element(By.CSS_SELECTOR, "blockquote.abstract"))
            
            # 카테고리 추출
            categories = []
            try:
                categories_elem = self.driver.find_element(By.CSS_SELECTOR, "div.primary-subject")
                categories = [cat.strip() for cat in categories_elem.text.split(',')]
            except NoSuchElementException:
                pass
            
            # 제출일 추출
            submission_date = None
            try:
                submission_text = self.get_text(self.driver.find_element(By.CSS_SELECTOR, "div.submission-history"))
                if submission_text:
                    import re
                    date_match = re.search(r"Submitted (\d{1,2} \w+, \d{4})", submission_text)
                    if date_match:
                        submission_date = datetime.strptime(date_match.group(1), "%d %B, %Y")
            except (NoSuchElementException, ValueError):
                pass
            
            # PDF 및 HTML URL 추출
            pdf_url = None
            html_url = None
            source_url = None
            try:
                pdf_url = self.driver.find_element(By.CSS_SELECTOR, "a[href*='/pdf/']").get_attribute("href")
                html_url = self.driver.find_element(By.CSS_SELECTOR, "a[href*='/html/']").get_attribute("href")
                source_url = self.driver.find_element(By.CSS_SELECTOR, "a[href*='/source/']").get_attribute("href")
            except NoSuchElementException:
                pass

            # PDF 다운로드
            if pdf_url:
                paper_id = url.split('/')[-1]
                filename = f"{paper_id}.pdf"
                self.download_pdf(pdf_url, filename)
            
            return {
                "title": title,
                "authors": authors,
                "abstract": abstract,
                "submission_date": submission_date,
                "categories": categories,
                "pdf_url": pdf_url,
                "html_url": html_url,
                "source_url": source_url
            }
            
        except Exception as e:
            logger.error(f"논문 상세 정보 수집 중 오류: {str(e)}")
            return {}
        finally:
            self.cleanup()

    def collect(self) -> List[Dict[str, Any]]:
        """논문 정보 수집"""
        try:
            # 논문 링크 수집
            paper_links = self.collect_paper_links()
            if not paper_links:
                logger.error("논문 링크를 찾을 수 없습니다.")
                return []
            
            # 논문 상세 정보 수집
            papers = []
            one_week_ago = datetime.now() - timedelta(days=7)
            
            for url in paper_links:
                details = self.get_paper_details(url)
                if not details:
                    continue
                
                # 카테고리 필터링
                if not any(cat in self.target_categories for cat in details.get("categories", [])):
                    continue
                
                # 최근 1주일 이내의 논문만 수집
                if details.get("submission_date") and details["submission_date"] < one_week_ago:
                    continue
                
                papers.append(details)
                time.sleep(1)  # 서버 부하 방지
            
            return papers
            
        except Exception as e:
            logger.error(f"논문 수집 중 오류: {str(e)}")
            return [] 
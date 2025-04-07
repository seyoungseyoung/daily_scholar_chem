import os
import time
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
import pytz
from bs4 import BeautifulSoup
import re
from pdfminer.high_level import extract_text
from pdfminer.pdfparser import PDFSyntaxError
import json
import warnings
from pdfminer.pdfpage import PDFPage
from tqdm import tqdm
from pathlib import Path
import io
import urllib.parse

# PDF 경고 메시지 필터링
warnings.filterwarnings('ignore', category=UserWarning, module='pdfminer.pdfpage')
warnings.filterwarnings('ignore', category=UserWarning, module='pdfminer.pdfdocument')
warnings.filterwarnings('ignore', category=UserWarning, module='pdfminer.pdfparser')

# 로깅 설정
logger = logging.getLogger('arxiv_collector')

class ChemRxivCollector:
    def __init__(self):
        # 로거 초기화
        self.logger = logger
        
        # API 설정
        self.base_url = "https://chemrxiv.org/engage/chemrxiv/public-api/v1/items"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json"
        }
        
        # 디렉토리 설정
        self.base_dir = Path(__file__).parent.parent.parent
        self.papers_dir = self.base_dir / 'data' / 'papers'
        self.html_dir = self.base_dir / 'data' / 'html'
        self.text_dir = self.base_dir / 'data' / 'text'
        
        # 디렉토리 생성
        self.papers_dir.mkdir(parents=True, exist_ok=True)
        self.html_dir.mkdir(parents=True, exist_ok=True)
        self.text_dir.mkdir(parents=True, exist_ok=True)
        
        # 재시도 설정
        self.max_retries = 3
        self.retry_delay = 2  # 초
        self.max_papers = 50  # 최대 수집 논문 수

    def download_pdf(self, url: str, filename: str) -> bool:
        """PDF 파일 다운로드"""
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                response = requests.get(url, stream=True)
                response.raise_for_status()
                total_size = int(response.headers.get('content-length', 0))
                
                filepath = self.papers_dir / filename
                with open(filepath, 'wb') as file, tqdm(
                    desc=filename,
                    total=total_size,
                    unit='iB',
                    unit_scale=True,
                    leave=False,  # 진행률 표시줄이 다음 줄에 남지 않도록 설정
                    disable=not self.logger.isEnabledFor(logging.INFO)  # 로깅 레벨이 INFO 이상일 때만 진행률 표시
                ) as pbar:
                    for data in response.iter_content(chunk_size=1024):
                        size = file.write(data)
                        pbar.update(size)
                return True
            except requests.exceptions.RequestException as e:
                self.logger.error(f"PDF 다운로드 중 네트워크 오류 발생 (시도 {retry_count + 1}/{self.max_retries}): {str(e)}")
                retry_count += 1
                if retry_count < self.max_retries:
                    time.sleep(self.retry_delay)
            except IOError as e:
                self.logger.error(f"PDF 파일 저장 중 오류 발생 (시도 {retry_count + 1}/{self.max_retries}): {str(e)}")
                retry_count += 1
                if retry_count < self.max_retries:
                    time.sleep(self.retry_delay)
            except Exception as e:
                self.logger.error(f"PDF 다운로드 중 예상치 못한 오류 발생 (시도 {retry_count + 1}/{self.max_retries}): {str(e)}")
                retry_count += 1
                if retry_count < self.max_retries:
                    time.sleep(self.retry_delay)
        return False

    def download_html(self, paper_id: str) -> bool:
        """HTML 버전 논문 다운로드 및 저장"""
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                html_url = f"https://chemrxiv.org/engage/chemrxiv/article-details/{paper_id}"
                
                response = requests.get(html_url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 메타데이터 제거
                for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer']):
                    element.decompose()
                
                # 본문 추출
                main_content = soup.find('article')
                if not main_content:
                    self.logger.warning(f"본문을 찾을 수 없음: {html_url}")
                    return False
                
                # 이미지 URL 수정
                for img in main_content.find_all('img'):
                    if img.get('src', '').startswith('/'):
                        img['src'] = f"https://chemrxiv.org{img['src']}"
                
                # 파일명 생성
                filename = f"{paper_id}.html"
                
                # HTML 저장
                filepath = self.html_dir / filename
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(str(main_content))
                
                return True
            except requests.exceptions.RequestException as e:
                self.logger.error(f"HTML 다운로드 중 네트워크 오류 발생 (시도 {retry_count + 1}/{self.max_retries}): {str(e)}")
                retry_count += 1
                if retry_count < self.max_retries:
                    time.sleep(self.retry_delay)
            except IOError as e:
                self.logger.error(f"HTML 파일 저장 중 오류 발생 (시도 {retry_count + 1}/{self.max_retries}): {str(e)}")
                retry_count += 1
                if retry_count < self.max_retries:
                    time.sleep(self.retry_delay)
            except Exception as e:
                self.logger.error(f"HTML 다운로드 중 예상치 못한 오류 발생 (시도 {retry_count + 1}/{self.max_retries}): {str(e)}")
                retry_count += 1
                if retry_count < self.max_retries:
                    time.sleep(self.retry_delay)
        return False

    def extract_text_from_pdf(self, pdf_path: str, output_path: str) -> bool:
        """PDF에서 텍스트 추출"""
        try:
            text = extract_text(pdf_path)
            
            # 텍스트 정리
            text = re.sub(r'\s+', ' ', text)  # 연속된 공백 제거
            text = text.strip()
            
            # 파일 저장
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            return True
        except PDFSyntaxError as e:
            self.logger.error(f"PDF 구문 오류 발생: {str(e)}")
            return False
        except IOError as e:
            self.logger.error(f"텍스트 파일 저장 중 오류 발생: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"PDF 텍스트 추출 중 예상치 못한 오류 발생: {str(e)}")
            return False

    def collect(self, search_options: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        try:
            if search_options is None:
                search_options = {}
                
            # 검색어 처리
            search_term = search_options.get("term", "")
            if not search_term:
                self.logger.error("검색어가 지정되지 않았습니다.")
                return []
                
            self.logger.info(f"검색어: {search_term}")
            self.logger.info(f"검색 옵션: {search_options}")
            
            # API 요청
            response = requests.get(
                self.base_url,
                params=search_options,
                headers=self.headers
            )
            
            if response.status_code != 200:
                self.logger.error(f"API 요청 실패: {response.status_code}")
                self.logger.error(f"응답 내용: {response.text}")
                return []
                
            data = response.json()
            self.logger.info(f"API 응답 구조: {list(data.keys())}")
            
            # 논문 데이터 추출
            papers = []
            for item_hit in data.get('itemHits', []):
                paper = item_hit.get('item', {})
                if paper and paper.get('title'):  # 제목이 있는 논문만 추가
                    papers.append(paper)
            
            self.logger.info(f"검색된 논문 수: {len(papers)}")
            
            if not papers:
                self.logger.warning("검색 결과가 없습니다.")
                return []
            
            # 검색 결과 로깅
            for paper in papers[:5]:  # 처음 5개만 로깅
                self.logger.info(f"제목: {paper.get('title', 'N/A')}")
                self.logger.info(f"ID: {paper.get('id', 'N/A')}")
                self.logger.info(f"DOI: {paper.get('doi', 'N/A')}")
                author_names = [f"{a.get('firstName', '')} {a.get('lastName', '')}".strip() for a in paper.get('authors', [])]
                self.logger.info(f"저자: {author_names}")
                
            # 논문 형식 표준화
            processed_papers = []
            for paper in papers:
                # ID 처리
                paper_id = paper.get('id', '')
                if not paper_id:
                    self.logger.warning("ID가 없는 논문을 건너뜁니다.")
                    continue
                
                # URL 생성
                url = f"https://chemrxiv.org/engage/chemrxiv/article-details/{paper_id}"
                
                # authors 처리
                authors = []
                for author in paper.get('authors', []):
                    name = f"{author.get('firstName', '')} {author.get('lastName', '')}".strip()
                    if name:
                        authors.append(name)
                
                # categories 처리
                categories = []
                for cat in paper.get('categories', []):
                    if isinstance(cat, dict) and cat.get('name'):
                        categories.append(cat['name'])
                    elif isinstance(cat, str):
                        categories.append(cat)
                
                # asset 처리
                asset = paper.get('asset', {})
                pdf_url = asset.get('original', {}).get('url', '') if asset else ''
                
                # metrics 처리
                metrics = {}
                for metric in paper.get('metrics', []):
                    if isinstance(metric, dict) and metric.get('description') and metric.get('value') is not None:
                        metrics[metric['description'].lower().replace(' ', '_')] = metric['value']
                
                # suppItems 처리
                supp_items = []
                for supp in paper.get('suppItems', []):
                    if isinstance(supp, dict) and supp.get('title') and supp.get('asset', {}).get('original', {}).get('url'):
                        supp_items.append({
                            'title': supp['title'],
                            'url': supp['asset']['original']['url']
                        })
                
                processed_paper = {
                    'id': paper_id,
                    'title': paper.get('title', ''),
                    'authors': authors,
                    'abstract': paper.get('abstract', ''),
                    'submission_date': paper.get('submittedDate', paper.get('publishedDate', '')),
                    'categories': categories,
                    'html_url': url,
                    'doi': paper.get('doi', ''),
                    'pdf_url': pdf_url,
                    'license': paper.get('license', {}).get('name', ''),
                    'version': paper.get('version', ''),
                    'is_latest_version': paper.get('isLatestVersion', False),
                    'keywords': paper.get('keywords', []),
                    'metrics': metrics,
                    'content_type': paper.get('contentType', {}).get('name', ''),
                    'status': paper.get('status', ''),
                    'funders': [f.get('name', '') for f in paper.get('funders', []) if f.get('name')],
                    'supplementary_materials': supp_items,
                    'subject': paper.get('subject', {}).get('name', ''),
                    'event': paper.get('event', {}).get('name', '') if paper.get('event') else None
                }
                
                self.logger.info(f"처리된 논문 데이터: {json.dumps(processed_paper, indent=2)}")
                processed_papers.append(processed_paper)
                
            if not processed_papers:
                self.logger.warning("처리된 논문이 없습니다.")
                return []
                
            return processed_papers
            
        except Exception as e:
            self.logger.error(f"논문 수집 중 오류 발생: {e}")
            return []

    def direct_url_request(self, search_term: str) -> List[Dict[str, Any]]:
        """직접 URL 요청으로 논문 정보 가져오기"""
        try:
            self.logger.info("직접 URL 요청을 통한 논문 검색 시작...")
            
            # 검색 URL 구성
            encoded_search = urllib.parse.quote(search_term)
            url = f"https://chemrxiv.org/engage/api/public/chemrxiv/content/contentItems/search?searchText={encoded_search}&orderBy=PUBLISHED_DATE&order=DESC&limit=20&offset=0"
            self.logger.info(f"직접 URL 요청: {url}")
            
            # HTTP 요청
            response = requests.get(
                url,
                headers=self.headers
            )
            
            if response.status_code != 200:
                self.logger.error(f"직접 URL 요청 실패: {response.status_code}")
                self.logger.error(f"응답 내용: {response.text}")
                return []
                
            data = response.json()
            self.logger.info(f"응답 구조: {list(data.keys())}")
            
            # 논문 데이터 추출
            papers = []
            if "articles" in data:
                papers = data.get("articles", [])
            elif "itemHits" in data:
                papers = [item_hit.get("item", {}) for item_hit in data.get("itemHits", [])]
            elif "items" in data:
                papers = data.get("items", [])
            else:
                self.logger.error(f"알 수 없는 응답 형식: {list(data.keys())}")
                return []
            
            self.logger.info(f"검색된 논문 수: {len(papers)}")
            
            # 논문 정보 추출
            processed_papers = []
            for paper in papers:
                # 필수 필드 확인
                if 'title' not in paper:
                    continue
                    
                # ID 처리
                paper_id = paper.get('id', '')
                if not paper_id and 'identifier' in paper:
                    paper_id = paper.get('identifier', '')
                
                # URL 생성
                url = paper.get('html_url', '')
                if not url:
                    url = f"https://chemrxiv.org/engage/chemrxiv/article-details/{paper_id}"
                
                processed_paper = {
                    'id': paper_id,
                    'title': paper.get('title', ''),
                    'authors': paper.get('authors', []),
                    'abstract': paper.get('abstract', ''),
                    'submission_date': paper.get('submittedDate', paper.get('published', paper.get('publishedDate', ''))),
                    'categories': paper.get('categories', []),
                    'html_url': url
                }
                processed_papers.append(processed_paper)
                self.logger.info(f"논문 추출: {paper.get('title', 'N/A')}")
            
            return processed_papers
            
        except Exception as e:
            self.logger.error(f"직접 URL 요청 중 오류 발생: {e}")
            return []
    
    def download_and_extract_pdf(self, url: str) -> str:
        try:
            # PDF 다운로드
            response = requests.get(url, headers=self.headers, stream=True)
            response.raise_for_status()
            
            # PDF 텍스트 추출
            with io.BytesIO(response.content) as pdf_file:
                text = extract_text(pdf_file)
                return text
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"PDF 다운로드 중 네트워크 오류 발생: {e}")
            return ""
        except PDFSyntaxError as e:
            self.logger.error(f"PDF 파싱 오류 발생: {e}")
            return ""
        except Exception as e:
            self.logger.error(f"PDF 처리 중 오류 발생: {e}")
            return ""
    
    def download_and_extract_html(self, url: str) -> str:
        try:
            # HTML 다운로드
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            # HTML 파싱
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 메인 콘텐츠 추출
            main_content = soup.find('div', class_='main-content')
            if not main_content:
                self.logger.warning(f"HTML에서 메인 콘텐츠를 찾을 수 없음: {url}")
                return ""
            
            # 텍스트 추출
            text = main_content.get_text(separator=' ', strip=True)
            return text
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"HTML 다운로드 중 네트워크 오류 발생: {e}")
            return ""
        except Exception as e:
            self.logger.error(f"HTML 처리 중 오류 발생: {e}")
            return "" 
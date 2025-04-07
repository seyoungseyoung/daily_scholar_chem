import datetime
from typing import List, Dict
import pandas as pd
import pytz
import time
import os
import schedule
import logging
from pathlib import Path
from rank_papers import PaperQualityAnalyzer
from paper_analyzer import PaperAnalyzer
from analysis_manager import AnalysisManager
import json
from services.email_sender import EmailSender
from services.arxiv_collector import ChemRxivCollector

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data/logs/daily_top10.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# 다른 모듈의 로거 설정
for module in ['paper_analyzer', 'arxiv_collector', 'rank_papers']:
    module_logger = logging.getLogger(module)
    module_logger.setLevel(logging.INFO)
    module_logger.propagate = False  # 상위 로거로 전파하지 않음
    module_logger.addHandler(logging.StreamHandler())
    module_logger.addHandler(logging.FileHandler('data/logs/daily_top10.log', encoding='utf-8'))

# Initialize analyzers and collector
paper_analyzer = PaperAnalyzer()
analysis_manager = AnalysisManager()
paper_collector = ChemRxivCollector()

def get_papers() -> List[Dict]:
    try:
        logger.info("CO2RR 관련 논문을 가져오는 중...")
        
        # 검색어 리스트
        search_terms = [
            # 핵심 검색어
            '"CO2 reduction"',
            '"CO2 electroreduction"',
            '"CO2 electrocatalysis"',
            
            # 촉매 관련
            '"CO2 reduction catalyst"',
            '"CO2 electrocatalyst"',
            '"CO2 reduction Cu"',
            '"CO2 reduction Ag"',
            '"CO2 reduction Au"',
            
            # 메커니즘 관련
            '"CO2 reduction mechanism"',
            '"CO2 reduction HER"',
            '"CO2 reduction selectivity"',
            
            # 성능 관련
            '"CO2 reduction efficiency"',
            '"CO2 reduction current density"',
            '"CO2 reduction stability"'
        ]
        
        all_papers = []
        seen_ids = set()  # 중복 논문 제거용
        
        for term in search_terms:
            logger.info(f"검색어 '{term}'로 논문 검색 중...")
            
            # 검색 옵션 설정
            search_options = {
                "term": term,
                "skip": 0,
                "limit": 50,
                "sort": "PUBLISHED_DATE_DESC",
                "searchDateFrom": (datetime.datetime.now(pytz.UTC) - datetime.timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "searchDateTo": datetime.datetime.now(pytz.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
            }
            
            # 논문 수집
            papers = paper_collector.collect(search_options)
            
            if papers:
                # 중복 제거
                for paper in papers:
                    paper_id = paper.get('id')
                    if paper_id and paper_id not in seen_ids:
                        seen_ids.add(paper_id)
                        all_papers.append(paper)
            
        if not all_papers:
            logger.warning("수집된 논문이 없습니다.")
            return []
            
        logger.info(f"총 {len(all_papers)}개의 논문을 수집했습니다.")
        
        # 검색 결과 확인
        for paper in all_papers[:5]:  # 처음 5개만 출력
            logger.info(f"제목: {paper.get('title', 'N/A')}")
            logger.info(f"URL: {paper.get('html_url', 'N/A')}")
            
        return all_papers
        
    except Exception as e:
        logger.error(f"논문 수집 중 오류 발생: {e}")
        return []

def save_top10(papers: List[Dict], analyzer: PaperQualityAnalyzer):
    try:
        # 논문 품질 점수 계산 및 정렬
        paper_scores = []
        for paper in papers:
            score = analyzer.analyze_paper(paper)
            # categories가 딕셔너리 리스트인 경우 처리
            categories = paper['categories']
            if isinstance(categories, list) and categories and isinstance(categories[0], dict):
                category_names = [cat.get('name', '') for cat in categories if isinstance(cat, dict)]
                categories_str = ', '.join(category_names)
            else:
                categories_str = ', '.join(categories) if isinstance(categories, list) else str(categories)
            
            # submission_date 처리
            submission_date = paper['submission_date']
            if isinstance(submission_date, str):
                # 문자열인 경우 그대로 사용
                date_str = submission_date
            else:
                # datetime 객체인 경우 포맷팅
                date_str = submission_date.strftime('%Y-%m-%d')
            
            # authors 처리
            authors = paper['authors']
            if isinstance(authors, list):
                author_count = len(authors)
            else:
                author_count = len(authors.split(',')) if isinstance(authors, str) else 0
                
            paper_scores.append({
                'rank': 0,
                'title': paper['title'].replace('\n', ' '),
                'url': paper['html_url'],
                'score': score,
                'authors': author_count,
                'categories': categories_str,
                'published': date_str,
                'updated': date_str,
                'abstract': paper['abstract'].replace('\n', ' ')
            })
        
        # 점수로 정렬
        paper_scores.sort(key=lambda x: x['score'], reverse=True)
        
        # 상위 10개만 선택
        top10 = paper_scores[:10]
        
        # 순위 추가
        for i, paper in enumerate(top10, 1):
            paper['rank'] = i
        
        # DataFrame 생성
        df = pd.DataFrame(top10)
        
        # 결과 출력
        logger.info(f"\n=== {datetime.datetime.now(pytz.UTC).strftime('%Y-%m-%d')}의 Top 10 논문 ===")
        logger.info("순위 | 제목 | URL | 품질점수 | 저자수 | 카테고리 | 게시일 | 수정일")
        logger.info("-" * 150)
        
        for _, paper in df.iterrows():
            title = paper['title'][:70] + '...' if len(paper['title']) > 70 else paper['title']
            logger.info(f"{paper['rank']:2d} | {title} | {paper['url']} | {paper['score']:.2f} | {paper['authors']} | {paper['categories']} | {paper['published']} | {paper['updated']}")
        
        # CSV 파일로 저장
        base_dir = Path(__file__).parent.parent
        output_dir = base_dir / 'data' / 'daily_top10'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        current_date = datetime.datetime.now(pytz.UTC).strftime('%Y%m%d')
        csv_file = output_dir / f'top10_{current_date}.csv'
        
        df.to_csv(csv_file, index=False, encoding='utf-8')
        logger.info(f"결과가 {csv_file}에 저장되었습니다.")
        
    except Exception as e:
        logger.error(f"Top 10 논문 저장 중 오류 발생: {e}")
        raise

def main():
    try:
        # 현재 날짜 출력
        now = datetime.datetime.now(pytz.UTC)
        logger.info(f"현재 날짜: {now.strftime('%Y-%m-%d')}")
        
        # 논문 수집
        papers = get_papers()
        
        if not papers:
            logger.warning("수집된 논문이 없습니다.")
            return
        
        # 논문 분석
        analyzed_papers = paper_analyzer.analyze_papers(papers)
        
        # Top 10 저장
        save_top10(analyzed_papers, PaperQualityAnalyzer())
        
        # 이메일 전송
        email_sender = EmailSender()
        email_sender.send_report(analyzed_papers)
        
    except Exception as e:
        logger.error(f"메인 프로세스 실행 중 오류 발생: {e}")
        raise

if __name__ == "__main__":
    main() 
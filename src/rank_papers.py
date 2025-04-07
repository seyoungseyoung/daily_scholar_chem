import arxiv
import datetime
from typing import List, Dict, Any, Optional
import pandas as pd
import pytz
import time
import os
import logging
from paper_analyzer import PaperAnalyzer
from config import DATA_DIR

# 로깅 설정
logger = logging.getLogger('rank_papers')

class PaperQualityAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.paper_analyzer = PaperAnalyzer()
        self.quality_indicators = {
            'author_metrics': 0.3,    # 저자 관련 지표
            'paper_metrics': 0.3,     # 논문 특성 지표
            'time_metrics': 0.2,      # 시간 관련 지표
            'content_metrics': 0.2    # 내용 관련 지표
        }
    
    def analyze_paper(self, paper: Dict[str, Any]) -> float:
        """논문의 품질을 분석하고 점수를 반환합니다."""
        try:
            if not paper:
                logger.error("논문 데이터가 없습니다.")
                return 0.0
                
            score = 0.0
            
            # 1. 저자 수 점수 (최대 2점)
            author_score = self._calculate_author_score(paper)
            score += author_score * self.quality_indicators['author_metrics']
            
            # 2. 카테고리 관련성 점수 (최대 2점)
            category_score = self._calculate_category_score(paper)
            score += category_score * self.quality_indicators['paper_metrics']
            
            # 3. 키워드 관련성 점수 (최대 2점)
            keyword_score = self._calculate_keyword_score(paper)
            score += keyword_score * self.quality_indicators['paper_metrics']
            
            # 4. 초록 길이 점수 (최대 2점)
            abstract_score = self._calculate_abstract_score(paper)
            score += abstract_score * self.quality_indicators['content_metrics']
            
            # 5. 시간 관련 점수 (최대 2점)
            time_score = self._calculate_time_score(paper)
            score += time_score * self.quality_indicators['time_metrics']
            
            logger.info(f"논문 '{paper.get('title', 'N/A')}'의 품질 점수: {score:.2f}")
            return score
            
        except Exception as e:
            logger.error(f"논문 품질 분석 중 오류 발생: {e}")
            return 0.0
    
    def _calculate_author_score(self, paper: Dict[str, Any]) -> float:
        """저자 관련 점수를 계산합니다."""
        try:
            authors = paper.get('authors', [])
            if isinstance(authors, list):
                author_count = len(authors)
            else:
                author_count = len(authors.split(',')) if isinstance(authors, str) else 0
            return min(author_count * 0.2, 2.0)
        except Exception as e:
            logger.error(f"저자 점수 계산 중 오류 발생: {e}")
            return 0.0
    
    def _calculate_category_score(self, paper: Dict[str, Any]) -> float:
        """카테고리 관련 점수를 계산합니다."""
        try:
            categories = paper.get('categories', [])
            if isinstance(categories, list):
                category_count = len(categories)
            else:
                category_count = len(categories.split(',')) if isinstance(categories, str) else 0
            return min(category_count * 0.4, 2.0)
        except Exception as e:
            logger.error(f"카테고리 점수 계산 중 오류 발생: {e}")
            return 0.0
    
    def _calculate_keyword_score(self, paper: Dict[str, Any]) -> float:
        """키워드 관련 점수를 계산합니다."""
        try:
            keywords = paper.get('keywords', [])
            if isinstance(keywords, list):
                keyword_count = len(keywords)
            else:
                keyword_count = len(keywords.split(',')) if isinstance(keywords, str) else 0
            return min(keyword_count * 0.2, 2.0)
        except Exception as e:
            logger.error(f"키워드 점수 계산 중 오류 발생: {e}")
            return 0.0
    
    def _calculate_abstract_score(self, paper: Dict[str, Any]) -> float:
        """초록 관련 점수를 계산합니다."""
        try:
            abstract = paper.get('abstract', '')
            word_count = len(abstract.split())
            return min(word_count * 0.01, 2.0)
        except Exception as e:
            logger.error(f"초록 점수 계산 중 오류 발생: {e}")
            return 0.0
    
    def _calculate_time_score(self, paper: Dict[str, Any]) -> float:
        """시간 관련 점수를 계산합니다."""
        try:
            submission_date = paper.get('submission_date')
            if not submission_date:
                return 0.0
                
            if isinstance(submission_date, str):
                submission_date = datetime.fromisoformat(submission_date)
                
            days_since_submission = (datetime.now() - submission_date).days
            return max(2.0 - (days_since_submission * 0.01), 0.0)
        except Exception as e:
            logger.error(f"시간 점수 계산 중 오류 발생: {e}")
            return 0.0
    
    def _calculate_paper_score(self, paper) -> float:
        score = 0
        # 제목 품질 평가
        title_words = paper.title.split()
        title_length = len(title_words)
        if 5 <= title_length <= 10:
            score += 0.8
        elif 11 <= title_length <= 15:
            score += 0.6
        else:
            score += 0.4
            
        # 제목의 명확성 (특수문자, 대문자 사용 등)
        if any(word[0].isupper() for word in title_words):
            score += 0.2
            
        # 초록 품질 평가
        abstract_words = paper.summary.split()
        abstract_length = len(abstract_words)
        if abstract_length >= 200:
            score += 0.8
        elif abstract_length >= 100:
            score += 0.6
        else:
            score += 0.4
            
        # 카테고리 다양성
        category_count = len(paper.categories)
        if category_count >= 3:
            score += 0.5
        elif category_count == 2:
            score += 0.3
        else:
            score += 0.1
            
        return score
    
    def _calculate_content_score(self, paper) -> float:
        score = 0
        abstract = paper.summary.lower()
        
        # 방법론 언급 평가
        method_keywords = ['method', 'approach', 'algorithm', 'technique', 'framework', 'model', 'architecture']
        method_count = sum(1 for keyword in method_keywords if keyword in abstract)
        score += min(method_count * 0.2, 0.6)  # 최대 0.6점
        
        # 실험/평가 언급 평가
        eval_keywords = ['experiment', 'evaluation', 'result', 'performance', 'benchmark', 'comparison']
        eval_count = sum(1 for keyword in eval_keywords if keyword in abstract)
        score += min(eval_count * 0.2, 0.4)  # 최대 0.4점
        
        return score

def get_recent_papers(days: int = 7) -> List[Dict]:
    # 7일 전 날짜 계산 (UTC 기준)
    end_date = datetime.datetime.now(pytz.UTC)
    start_date = end_date - datetime.timedelta(days=days)
    
    # arXiv 검색 쿼리 생성
    client = arxiv.Client()
    search = arxiv.Search(
        query='cat:cs.AI',
        max_results=100,  # 한 번에 가져올 최대 결과 수 제한
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending
    )
    
    # 논문 수집
    papers = []
    try:
        for paper in client.results(search):
            if paper.published < start_date:
                break
            papers.append(paper)
            time.sleep(0.1)  # API 요청 간 간격 추가
    except Exception as e:
        print(f"논문 수집 중 오류 발생: {e}")
        if not papers:  # 논문을 하나도 수집하지 못한 경우
            raise
    
    return papers

def main():
    # 논문 품질 분석기 초기화
    analyzer = PaperQualityAnalyzer()
    
    # 최근 7일간의 논문 가져오기
    print("최근 7일간의 CO2RR 논문을 가져오는 중...")
    papers = get_recent_papers()
    print(f"총 {len(papers)}개의 논문을 가져왔습니다.")
    
    # 논문 품질 점수 계산 및 정렬
    print("논문 품질 점수를 계산하는 중...")
    paper_scores = []
    for paper in papers:
        score = analyzer.analyze_paper(paper)
        paper_scores.append({
            'rank': 0,  # 순위는 나중에 추가
            'title': paper.title.replace('\n', ' '),  # 제목에서 줄바꿈 제거
            'url': paper.entry_id,  # arXiv 링크
            'score': score,
            'authors': len(paper.authors),
            'categories': ', '.join(paper.categories),  # 카테고리 추가
            'published': paper.published.strftime('%Y-%m-%d'),  # 날짜 형식 지정
            'updated': paper.updated.strftime('%Y-%m-%d'),  # 업데이트 날짜 추가
            'abstract': paper.summary.replace('\n', ' ')  # 초록 추가
        })
    
    # 점수로 정렬
    paper_scores.sort(key=lambda x: x['score'], reverse=True)
    
    # 순위 추가
    for i, paper in enumerate(paper_scores, 1):
        paper['rank'] = i
    
    # DataFrame 생성
    df = pd.DataFrame(paper_scores)
    
    # 결과 출력
    print("\n=== 최근 7일간의 cs.AI 논문 순위 ===")
    print("순위 | 제목 | URL | 품질점수 | 저자수 | 카테고리 | 게시일 | 수정일")
    print("-" * 150)
    
    for _, paper in df.iterrows():
        title = paper['title'][:70] + '...' if len(paper['title']) > 70 else paper['title']
        print(f"{paper['rank']:2d} | {title} | {paper['url']} | {paper['score']:.2f} | {paper['authors']} | {paper['categories']} | {paper['published']} | {paper['updated']}")
    
    # CSV 파일로 저장
    os.makedirs('data/rankings', exist_ok=True)
    current_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_file = f'data/rankings/paper_rankings_{current_time}.csv'
    df.to_csv(csv_file, index=False, encoding='utf-8')
    print(f"\n순위가 CSV 파일로 저장되었습니다: {csv_file}")

if __name__ == "__main__":
    main() 
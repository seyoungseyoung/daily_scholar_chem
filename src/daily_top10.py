import arxiv
import datetime
from typing import List, Dict
import pandas as pd
import pytz
import time
import os
import schedule
from rank_papers import PaperQualityAnalyzer
from paper_analyzer import PaperAnalyzer
from analysis_manager import AnalysisManager
import json

def get_specific_date_papers(target_date: str) -> List[Dict]:
    # UTC 기준으로 특정 날짜 계산
    target_start = datetime.datetime.strptime(target_date, '%Y-%m-%d').replace(tzinfo=pytz.UTC)
    target_end = target_start + datetime.timedelta(days=1)
    
    # arXiv 검색 쿼리 생성
    client = arxiv.Client()
    search = arxiv.Search(
        query='cat:cs.AI',
        max_results=100,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending
    )
    
    # 논문 수집
    papers = []
    try:
        for paper in client.results(search):
            if paper.published < target_start:
                break
            if target_start <= paper.published < target_end:
                papers.append(paper)
            time.sleep(0.1)
    except Exception as e:
        print(f"논문 수집 중 오류 발생: {e}")
        if not papers:
            raise
    
    return papers

def save_top10(papers: List[Dict], analyzer: PaperQualityAnalyzer):
    # 논문 품질 점수 계산 및 정렬
    paper_scores = []
    for paper in papers:
        score = analyzer.analyze_paper(paper)
        paper_scores.append({
            'rank': 0,
            'title': paper.title.replace('\n', ' '),
            'url': paper.entry_id,
            'score': score,
            'authors': len(paper.authors),
            'categories': ', '.join(paper.categories),
            'published': paper.published.strftime('%Y-%m-%d'),
            'updated': paper.updated.strftime('%Y-%m-%d'),
            'abstract': paper.summary.replace('\n', ' ')
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
    print(f"\n=== {datetime.datetime.now(pytz.UTC).strftime('%Y-%m-%d')}의 Top 10 논문 ===")
    print("순위 | 제목 | URL | 품질점수 | 저자수 | 카테고리 | 게시일 | 수정일")
    print("-" * 150)
    
    for _, paper in df.iterrows():
        title = paper['title'][:70] + '...' if len(paper['title']) > 70 else paper['title']
        print(f"{paper['rank']:2d} | {title} | {paper['url']} | {paper['score']:.2f} | {paper['authors']} | {paper['categories']} | {paper['published']} | {paper['updated']}")
    
    # CSV 파일로 저장
    os.makedirs('data/daily_top10', exist_ok=True)
    current_date = datetime.datetime.now(pytz.UTC).strftime('%Y%m%d')
    csv_file = f'data/daily_top10/top10_{current_date}.csv'
    df.to_csv(csv_file, index=False, encoding='utf-8')
    print(f"\nTop 10이 CSV 파일로 저장되었습니다: {csv_file}")
    
    return top10

def analyze_and_generate_report(papers: List[Dict], target_date: str):
    # 논문 품질 분석기 초기화
    analyzer = PaperQualityAnalyzer()
    
    # Top 10 추출
    top10 = save_top10(papers, analyzer)
    
    # 논문 분석기 초기화
    paper_analyzer = PaperAnalyzer()
    
    # 분석 결과를 JSON 형식으로 변환
    papers_json = []
    for i, paper in enumerate(papers):
        if paper.entry_id in [p['url'] for p in top10]:
            # Result 객체를 딕셔너리로 변환
            paper_dict = {
                "title": paper.title,
                "abstract": paper.summary,
                "paper_id": paper.entry_id.split("/")[-1],
                "authors": [author.name for author in paper.authors],
                "submission_date": paper.published.strftime('%Y-%m-%d'),
                "categories": paper.categories,
                "pdf_url": paper.pdf_url,
                "html_url": paper.entry_id,
                "local_pdf_path": "",
                "local_text_path": ""
            }
            
            # 논문 분석 수행
            print(f"\n논문 분석 중: {paper_dict['title']}")
            analysis_results = paper_analyzer.analyze_paper(paper_dict)
            print(f"분석 완료: {paper_dict['title']}")
            
            # 카테고리 분류
            categories = paper.categories
            classification = {
                'is_ai': 'cs.AI' in categories,
                'is_cv': 'cs.CV' in categories,
                'is_nlp': 'cs.CL' in categories,
                'is_robotics': 'cs.RO' in categories,
                'is_ml': 'cs.LG' in categories
            }
            
            # 태그 생성 (카테고리 기반)
            category_tags = []
            if classification['is_ai']:
                category_tags.append('AI')
            if classification['is_cv']:
                category_tags.append('Computer Vision')
            if classification['is_nlp']:
                category_tags.append('NLP')
            if classification['is_robotics']:
                category_tags.append('Robotics')
            if classification['is_ml']:
                category_tags.append('Machine Learning')
            
            # DeepSeek 태그 가져오기
            deepseek_tags = analysis_results.get('tags', [])
            
            # 모든 태그 통합
            all_tags = list(set(category_tags + deepseek_tags))  # 중복 제거
            
            papers_json.append({
                'paper_id': paper_dict['paper_id'],
                'title': paper_dict['title'],
                'authors': paper_dict['authors'],
                'abstract': paper_dict['abstract'],
                'submission_date': paper_dict['submission_date'],
                'categories': paper_dict['categories'],
                'pdf_url': paper_dict['pdf_url'],
                'html_url': paper_dict['html_url'],
                'local_pdf_path': paper_dict['local_pdf_path'],
                'local_html_path': paper_dict['local_text_path'],
                'classification': classification,  # AnalysisManager를 위해 유지
                'tags': all_tags,  # 통합된 태그 사용
                'analysis_results': analysis_results,
                'summary': analysis_results.get('summary', ''),
                'translation': analysis_results.get('translation', {})
            })
    
    # 분석 결과 저장
    os.makedirs('data/analysis', exist_ok=True)
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    analysis_file = f'data/analysis/analysis_results_{timestamp}.json'
    
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(papers_json, f, ensure_ascii=False, indent=2)
    
    print("\nHTML 보고서 생성 중...")
    
    # HTML 보고서 생성
    report_file = f'data/analysis/report_{timestamp}.html'
    manager = AnalysisManager()
    manager.process_papers(papers_json)
    
    print(f"\n분석 결과가 저장되었습니다: {analysis_file}")
    print(f"HTML 보고서가 생성되었습니다: {report_file}")

def run_daily_top10():
    try:
        # 3/31 논문 가져오기
        target_date = '2025-03-31'
        print(f"{target_date}의 cs.AI 논문을 가져오는 중...")
        papers = get_specific_date_papers(target_date)
        print(f"총 {len(papers)}개의 논문을 가져왔습니다.")
        
        # 분석 및 보고서 생성
        analyze_and_generate_report(papers, target_date)
    except Exception as e:
        print(f"오류 발생: {e}")

def main():
    # 테스트 실행
    run_daily_top10()

if __name__ == "__main__":
    main() 
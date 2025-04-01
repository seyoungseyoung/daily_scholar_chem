import json
import os
import pandas as pd
from datetime import datetime
from tqdm import tqdm
from src.paper_analyzer import PaperAnalyzer
from src.analysis_manager import AnalysisManager

def main():
    print("분석을 시작합니다...")
    
    # CSV 파일 읽기
    print("test.csv 파일을 읽는 중...")
    df = pd.read_csv("test.csv")
    
    # JSON 형식으로 변환
    print("데이터를 JSON 형식으로 변환하는 중...")
    papers = []
    for _, row in df.iterrows():
        paper = {
            "title": row["title"],
            "abstract": row["abstract"],
            "paper_id": row["pdf_url"].split("/")[-1].replace(".pdf", ""),
            "authors": row["authors"],
            "submission_date": row["submission_date"],
            "categories": [cat.strip() for cat in row["categories"].split(",")],
            "pdf_url": row["pdf_url"],
            "html_url": row["html_url"],
            "local_pdf_path": row["local_pdf_path"],
            "local_text_path": row["local_text_path"]
        }
        papers.append(paper)
    
    # JSON 파일로 저장
    print("test_papers.json 파일로 저장 중...")
    with open("test_papers.json", "w", encoding="utf-8") as f:
        json.dump(papers, f, indent=2, ensure_ascii=False)
    
    # 분석 결과 저장 디렉토리 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    analysis_dir = "data/analysis"
    os.makedirs(analysis_dir, exist_ok=True)
    
    # 분석 결과 파일 경로
    analysis_file = os.path.join(analysis_dir, f"analysis_{timestamp}.json")
    report_file = os.path.join(analysis_dir, f"report_{timestamp}.html")
    
    # 논문 분석
    print("\n논문 분석을 시작합니다...")
    analyzer = PaperAnalyzer()
    analysis_results = []
    
    for paper in tqdm(papers, desc="논문 분석 중"):
        print(f"\n논문 분석 중: {paper['title']}")
        result = analyzer.analyze_paper(paper)
        analysis_results.append(result)
        print(f"분석 완료: {paper['title']}")
    
    # 분석 결과 저장
    print("\n분석 결과를 저장하는 중...")
    with open(analysis_file, "w", encoding="utf-8") as f:
        json.dump(analysis_results, f, indent=2, ensure_ascii=False)
    
    # HTML 보고서 생성
    print("\nHTML 보고서를 생성하는 중...")
    manager = AnalysisManager()
    manager.process_papers(analysis_results)
    
    print(f"\n분석 결과가 저장되었습니다: {analysis_file}")
    print(f"보고서가 생성되었습니다: {report_file}")
    print(f"분석된 논문 수: {len(analysis_results)}")
    print(f"보고서 경로: {report_file}")

if __name__ == "__main__":
    main() 
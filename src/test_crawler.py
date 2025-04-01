import os
import pandas as pd
from services.arxiv_collector import ArxivCollector

def main():
    # 크롤러 초기화
    crawler = ArxivCollector()
    
    # 논문 수집
    print("논문 수집 시작...")
    papers = crawler.collect()
    
    if not papers:
        print("수집된 논문이 없습니다.")
        return
    
    # DataFrame 생성
    df = pd.DataFrame(papers)
    
    # submission_date를 문자열로 변환
    df['submission_date'] = df['submission_date'].apply(lambda x: x.strftime('%Y-%m-%d') if x else None)
    
    # categories를 문자열로 변환
    df['categories'] = df['categories'].apply(lambda x: ', '.join(x) if x else '')
    
    # CSV 파일로 저장
    output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test.csv')
    df.to_csv(output_path, index=False, encoding='utf-8')
    print(f"수집된 논문 정보가 {output_path}에 저장되었습니다.")
    print(f"총 {len(papers)}개의 논문이 수집되었습니다.")
    print(f"PDF 파일은 {crawler.papers_dir}에 저장되었습니다.")
    print(f"HTML 파일은 {crawler.html_dir}에 저장되었습니다.")
    print(f"텍스트 파일은 {crawler.text_dir}에 저장되었습니다.")

if __name__ == "__main__":
    main() 
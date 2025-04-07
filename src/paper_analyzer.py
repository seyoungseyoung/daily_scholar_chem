import json
import requests
from typing import Dict, Any, List
import time
import logging
import os
from pathlib import Path
from config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL, ANALYSIS_PROMPTS
from datetime import datetime

# 로깅 설정
logger = logging.getLogger('paper_analyzer')
# 기존 핸들러 제거
for handler in logger.handlers[:]:
    logger.removeHandler(handler)
# 새로운 핸들러 추가
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class PaperAnalyzer:
    def __init__(self):
        if not DEEPSEEK_API_KEY:
            raise ValueError("DEEPSEEK_API_KEY 환경 변수가 설정되지 않았습니다.")
            
        self.headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # 캐시 디렉토리 설정
        self.base_dir = Path(__file__).parent.parent.parent
        self.cache_dir = self.base_dir / 'data' / 'cache'
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"캐시 디렉토리가 생성되었습니다: {self.cache_dir}")
        except Exception as e:
            logger.error(f"캐시 디렉토리 생성 중 오류 발생: {e}")
            raise
        
        # 메모리 캐시 초기화
        self.cache = {}
        logger.info("메모리 캐시가 초기화되었습니다.")
    
    def _get_cache_path(self, paper_id: str) -> Path:
        """캐시 파일 경로를 반환합니다."""
        return self.cache_dir / f"{paper_id}.json"
    
    def _load_from_cache(self, paper_id: str) -> Dict:
        """캐시에서 논문 분석 결과를 로드합니다."""
        try:
            # 메모리 캐시 확인
            if paper_id in self.cache:
                logger.debug(f"메모리 캐시에서 논문 {paper_id} 로드")
                return self.cache[paper_id]
                
            # 파일 캐시 확인
            cache_path = self._get_cache_path(paper_id)
            if cache_path.exists():
                with open(cache_path, 'r', encoding='utf-8') as f:
                    result = json.load(f)
                    # 메모리 캐시에 저장
                    self.cache[paper_id] = result
                    logger.info(f"파일 캐시에서 논문 {paper_id} 로드")
                    return result
            logger.debug(f"캐시에 논문 {paper_id} 없음")
            return None
            
        except Exception as e:
            logger.error(f"캐시 로드 중 오류 발생 (paper_id: {paper_id}): {e}")
            return None
    
    def _save_to_cache(self, paper_id: str, result: Dict):
        """논문 분석 결과를 캐시에 저장합니다."""
        try:
            # datetime 객체를 문자열로 변환
            serializable_result = result.copy()
            if isinstance(serializable_result.get('submission_date'), datetime):
                serializable_result['submission_date'] = serializable_result['submission_date'].strftime('%Y-%m-%d')
            
            # 메모리 캐시에 저장
            self.cache[paper_id] = serializable_result
            
            # 파일 캐시에 저장
            cache_path = self._get_cache_path(paper_id)
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_result, f, ensure_ascii=False, indent=2)
            logger.info(f"논문 {paper_id} 분석 결과가 캐시에 저장되었습니다")
            
        except Exception as e:
            logger.error(f"캐시 저장 중 오류 발생 (paper_id: {paper_id}): {e}")
            # 캐시 저장 실패는 치명적 오류가 아니므로 계속 진행
    
    def _call_api(self, prompt: str, model: str = "deepseek-chat") -> str:
        """DeepSeek API를 호출하여 응답을 받아옵니다."""
        try:
            response = requests.post(
                DEEPSEEK_API_URL,
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": """You are a helpful AI assistant that analyzes academic papers.
When analyzing papers:
1. For classification, provide one main field and 5-8 tags
2. For summary, structure the content clearly with sections
3. For translation, maintain academic tone while being clear
Always format your response according to the specified format in the prompt."""
                        },
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"API 호출 중 오류 발생: {str(e)}")
            raise
    
    def _parse_classification(self, response: str) -> Dict[str, Any]:
        """분류 응답을 파싱합니다."""
        lines = response.strip().split('\n')
        classification = ""
        tags = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('분류:'):
                # 분류 추출 및 정리
                classification = line.replace('분류:', '').strip()
                classification = classification.strip('[]').strip()
            elif line.startswith('태그:'):
                # 태그 추출 및 정리
                tags_text = line.replace('태그:', '').strip()
                # 쉼표로 분리하고 대괄호와 공백 제거
                tags = [
                    tag.strip().strip('[]').strip()
                    for tag in tags_text.split(',')
                    if tag.strip() and not tag.isspace()
                ]
                # 빈 태그 제거
                tags = [tag for tag in tags if tag]
        
        # 태그가 없거나 3개 미만이면 기본 태그 생성
        if not tags or len(tags) < 3:
            if '컴퓨터 비전' in classification:
                tags = ['Computer Vision', 'Object Detection', 'Deep Learning', 'Image Processing', 'Neural Networks']
            elif '인공지능' in classification or '강화학습' in classification:
                tags = ['Artificial Intelligence', 'Machine Learning', 'Neural Networks', 'Reinforcement Learning', 'Deep Learning']
            elif '수중' in classification or 'Underwater' in classification:
                tags = ['Underwater Vision', 'Object Detection', 'Spiking Neural Networks', 'Energy Efficiency', 'Computer Vision']
        
        # 백엔드 관련 태그 제거
        tags = [tag for tag in tags if not any(x in tag.lower() for x in ['backend', 'api', 'server', 'database'])]
        
        return {
            "classification": classification,
            "tags": tags
        }
    
    def _clean_response(self, text: str) -> str:
        """응답을 HTML 형식으로 변환하고 정리합니다."""
        # 잘못된 blockquote 태그 제거
        text = text.replace('</blockquote>', '')
        text = text.replace('<blockquote>', '')
        
        # 마크다운 헤더를 HTML 헤더로 변환 (최소화)
        text = text.replace('### ', '<h3>')
        text = text.replace('## ', '<h2>')
        text = text.replace('# ', '<h2>')  # h1은 제목에만 사용
        
        # 헤더 닫기 태그 추가
        text = text.replace('\n', '</h3>\n', 1) if '<h3>' in text else text
        text = text.replace('\n', '</h2>\n', 1) if '<h2>' in text else text
        
        # 볼드 처리 개선
        text = text.replace('**', '<strong>')
        text = text.replace('**', '</strong>', 1)
        
        # 구분선을 HTML 구분선으로 변환
        text = text.replace('---\n', '<hr>\n')
        
        # 줄바꿈 정리 및 단락 처리
        lines = text.split('\n')
        cleaned_lines = []
        current_paragraph = []
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_paragraph:
                    cleaned_lines.append('<p>' + ' '.join(current_paragraph) + '</p>')
                    current_paragraph = []
            else:
                # 불필요한 공백 제거
                line = ' '.join(line.split())
                current_paragraph.append(line)
        
        if current_paragraph:
            cleaned_lines.append('<p>' + ' '.join(current_paragraph) + '</p>')
        
        # 연속된 빈 줄 제거
        result = '\n'.join(cleaned_lines)
        result = result.replace('\n\n\n', '\n\n')
        result = result.replace('\n\n\n', '\n\n')
        
        return result
    
    def _translate_abstract(self, abstract: str) -> str:
        """초록을 한국어로 번역합니다."""
        print("한국어 번역 중...")
        
        prompt = f"""다음은 논문 초록을 한국어로 번역하는 요구사항입니다:

1. 번역 대상: 다음 영문 초록을 한국어로 번역해주세요.
2. 번역 규칙:
   - 모든 전문 용어는 원문(영어)을 병기하고 <strong>태그로 강조 표시합니다. (예: 분리 배치 정규화(<strong>Separated Batch Normalization, SeBN</strong>))
   - 의미 단위로 개행해 가독성을 높입니다.
   - '-입니다' 체계를 유지하며 자연스러운 전문성을 확보합니다.
   - 핵심물질, 실험방법, 성능 지표 등은 <strong>태그로 굵게 표시해 시각적 강조를 적용합니다.

영문 초록:
{abstract}

한국어 번역:"""
        
        response = self._call_api(prompt, model="deepseek-chat")
        
        # 번역 규칙 부분 제거
        if "번역 규칙" in response:
            response = response.split("번역 규칙")[0].strip()
            
        # '---' 이후의 내용 제거
        if "---" in response:
            response = response.split("---")[0].strip()
            
        # '번역 특징' 부분 제거
        if "번역 특징" in response:
            response = response.split("번역 특징")[0].strip()
        
        print("번역 완료")
        return response

    def _analyze_paper_content(self, title: str, abstract: str) -> Dict[str, Any]:
        """논문 내용을 분석합니다."""
        # 분류 및 태그 생성
        classification_response = self._call_api(
            ANALYSIS_PROMPTS["classification"].format(
                title=title,
                abstract=abstract
            ),
            model="deepseek-reasoner"
        )
        classification_result = self._parse_classification(classification_response)
        
        # 요약 생성
        summary_response = self._call_api(
            ANALYSIS_PROMPTS["summary"].format(
                title=title,
                abstract=abstract
            ),
            model="deepseek-reasoner"
        )
        summary = self._clean_response(summary_response)
        
        return {
            "classification": classification_result["classification"],
            "tags": list(set(classification_result["tags"])),
            "summary": summary
        }
    
    def analyze_paper(self, paper: Dict) -> Dict:
        """단일 논문 분석"""
        try:
            # 논문 ID 추출
            paper_id = paper.get("id", "")
            if not paper_id:
                raise ValueError("논문 ID가 없습니다.")
            
            # 캐시 확인
            cached_result = self._load_from_cache(paper_id)
            if cached_result:
                logger.info(f"캐시에서 논문 분석 결과를 로드했습니다: {paper['title']}")
                return cached_result
            
            logger.info(f"\n논문 분석 시작: {paper['title']}")
            
            # URL 처리
            html_url = paper.get("html_url", "")
            if not html_url and "url" in paper:
                html_url = paper["url"]
            
            result = {
                "paper_id": paper_id,
                "title": paper["title"],
                "authors": paper["authors"],
                "abstract": paper["abstract"],
                "submission_date": paper["submission_date"].strftime("%Y-%m-%d"),
                "categories": paper["categories"],
                "pdf_url": paper.get("pdf_url", ""),
                "html_url": html_url,
                "pdf_text": paper.get("pdf_text", ""),
                "html_text": paper.get("html_text", "")
            }
            
            # 한국어 번역
            logger.info("한국어 번역 중...")
            result["title_ko"] = self._translate_abstract(result["title"])
            result["abstract_ko"] = self._translate_abstract(result["abstract"])
            logger.info("번역 완료")
            
            # 논문 내용 분석
            logger.info("논문 내용 분석 중...")
            result["analysis"] = self._analyze_paper_content(result["title"], result["abstract"])
            logger.info("분석 완료")
            
            # 캐시에 저장
            self._save_to_cache(paper_id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"논문 분석 중 오류 발생: {e}")
            raise
    
    def analyze_papers(self, papers: List[Dict]) -> List[Dict]:
        """여러 논문을 분석합니다."""
        try:
            analyzed_papers = []
            for paper in papers:
                # 논문 ID 추출
                paper_id = paper.get("id", "")
                if not paper_id:
                    logger.warning(f"논문 ID가 없습니다: {paper['title']}")
                    continue
                
                # 캐시 확인
                cached_result = self._load_from_cache(paper_id)
                if cached_result:
                    logger.info(f"캐시에서 논문 분석 결과를 로드했습니다: {paper['title']}")
                    analyzed_papers.append(cached_result)
                    continue
                
                # 논문 분석
                logger.info(f"\n논문 분석 시작: {paper['title']}")
                
                # 한국어 번역
                logger.info("한국어 번역 중...")
                translated_title = self._translate_abstract(paper['title'])
                translated_abstract = self._translate_abstract(paper['abstract'])
                logger.info("번역 완료")
                
                # 논문 내용 분석
                logger.info("논문 내용 분석 중...")
                analysis_result = self._analyze_paper_content(paper['title'], paper['abstract'])
                logger.info("분석 완료")
                
                # 결과 저장
                analyzed_paper = {
                    **paper,
                    'translated_title': translated_title,
                    'translated_abstract': translated_abstract,
                    'analysis': analysis_result
                }
                
                # 캐시에 저장
                self._save_to_cache(paper_id, analyzed_paper)
                
                analyzed_papers.append(analyzed_paper)
            
            return analyzed_papers
            
        except Exception as e:
            logger.error(f"논문 분석 중 오류 발생: {e}")
            return papers 
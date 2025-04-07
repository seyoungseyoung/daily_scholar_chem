"""
설정 파일
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 기본 디렉토리 설정
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data'
LOG_DIR = DATA_DIR / 'logs'

# 디렉토리 생성
for directory in [DATA_DIR, LOG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# 로깅 설정
def setup_logging():
    """로깅 설정을 초기화합니다."""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    log_file = LOG_DIR / 'daily_scholar.log'
    
    # 루트 로거 설정
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding='utf-8')
        ]
    )
    
    # 모듈별 로거 설정
    for module in ['paper_analyzer', 'arxiv_collector', 'rank_papers', 'analysis_manager']:
        module_logger = logging.getLogger(module)
        module_logger.setLevel(logging.INFO)
        module_logger.propagate = False
        module_logger.addHandler(logging.StreamHandler())
        module_logger.addHandler(logging.FileHandler(log_file, encoding='utf-8'))

# API 설정
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# 분석 프롬프트
ANALYSIS_PROMPTS = {
    "classification": """
다음 논문의 분류와 태그를 분석해주세요.
분류는 가장 주요한 분야 하나만 선택하고, 태그는 5-8개 정도의 키워드를 추가해주세요.
태그는 다음 카테고리별로 선택해주세요:
1. 기술적 용어 (2-3개): 논문에서 사용된 핵심 기술이나 알고리즘
2. 실용적 용어 (2-3개): 실제 적용 분야나 사용 사례
3. 혁신적 용어 (1-2개): 논문의 주요 기여점이나 혁신적인 부분

제목: {title}
초록: {abstract}

분류와 태그를 다음과 같은 형식으로 반환해주세요:
분류: [분류]
태그: [태그1], [태그2], [태그3], ...
""",
    
    "summary": """
다음 논문의 내용을 일반 독자도 이해하기 쉽게 요약해주세요.
다음 구조로 작성해주세요:

[연구의 중요성과 배경]
• 이 연구가 필요한 이유
  - 실생활 연관성
  - 기술적 필요성
• 현재까지의 한계점
  - 기존 기술의 문제점
  - 해결해야 할 과제
• 이 연구의 혁신적인 점
  - 주요 기여
  - 기술적 혁신

[주요 내용과 방법]
• 핵심 아이디어
  - 기본 개념
  - 차별화 포인트
• 구체적인 방법
  - 주요 단계
  - 구현 방식
• 주요 기술적 특징
  - 핵심 기술
  - 성능 개선점

[기대되는 효과와 기여점]
• 성능 향상 수치
  - 정량적 개선
  - 비교 결과
• 실제 적용 가능성
  - 응용 분야
  - 활용 사례
• 미래 발전 방향
  - 개선 가능성
  - 연구 과제

제목: {title}
초록: {abstract}

중요한 용어는 **용어**와 같이 굵게 표시하고, 구체적인 수치나 예시를 포함해주세요.
불필요한 마크다운 기호(#, -, * 등)는 사용하지 말고, 일반 텍스트로 작성해주세요.
""",
    
    "translation": """
다음 영문 초록을 한국어로 번역해주세요.
번역 시 다음 사항을 지켜주세요:

1. 번역 범위:
   - 초록의 모든 내용을 완전히 번역
   - 핵심 내용 누락 없이 번역
   - 각 문장의 의미를 정확히 전달

2. 학술 용어 처리:
   - 모든 학술 용어는 원문(영어)을 괄호로 표기
   - 예: 추론(reasoning), 일반화(generalization)

3. 강조 처리:
   - 핵심 개념과 기술 용어는 <strong>굵게</strong> 표시
   - 예: <strong>엔드투엔드</strong>, <strong>일반화 정책</strong>

4. 문장 구조:
   - 의미 단위로 개행 처리
   - 불필요한 수식어 생략
   - 동일 의미 반복 제거

5. 어조:
   - '-입니다' 체계 사용
   - 자연스러운 전문성 유지

초록:
{abstract}

번역문을 반환해주세요.
"""
}

# 로깅 초기화
setup_logging() 
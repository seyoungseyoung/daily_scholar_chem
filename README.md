# DailyAI Scholar

arXiv의 최신 AI/CS 논문을 자동으로 수집하고 DeepSeek AI를 통해 정리하여 제공하는 서비스입니다.

## 주요 기능

- arXiv CS 섹션의 최신 논문 자동 수집
- DeepSeek AI를 활용한 논문 요약 및 정리
- 카테고리별 논문 분류 및 필터링
- PDF 및 HTML 형식의 논문 제공

## 설치 방법

1. 저장소 클론
```bash
git clone https://github.com/yourusername/DailyAI_Scholar.git
cd DailyAI_Scholar
```

2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
.\venv\Scripts\activate  # Windows
```

3. 의존성 설치
```bash
pip install -r requirements.txt
```

4. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일을 열고 필요한 설정을 입력하세요
```

## 사용 방법

1. 논문 수집 실행
```bash
python src/main.py collect
```

2. 논문 요약 실행
```bash
python src/main.py summarize
```

## 프로젝트 구조

```
DailyAI_Scholar/
├── src/                # 소스 코드
│   ├── models/        # 데이터 모델
│   ├── services/      # 비즈니스 로직
│   ├── database/      # 데이터베이스 관련
│   └── utils/         # 유틸리티 함수
├── tests/             # 테스트 코드
├── data/              # 데이터 저장소
│   └── database/      # SQLite 데이터베이스
├── logs/              # 로그 파일
└── requirements.txt   # 의존성 목록
```

## 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요. 
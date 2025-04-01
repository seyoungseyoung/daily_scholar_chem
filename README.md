# DailyAI Scholar

[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![arXiv](https://img.shields.io/badge/arXiv-cs.AI-red.svg)](https://arxiv.org/list/cs.AI/recent)

An intelligent system for daily analysis and ranking of AI research papers from arXiv.

## 🌟 Features

- **Automated Paper Collection**: Daily fetching of AI research papers from arXiv
- **Smart Ranking System**: Quality-based paper ranking using multiple metrics
- **Comprehensive Analysis**: Detailed paper analysis including:
  - Quality scoring
  - Category classification
  - Key insights extraction
  - Korean translation
- **Beautiful Reports**: Generate elegant HTML reports with paper summaries
- **Database Integration**: Store and manage paper data efficiently

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Kororu-lab/DailyAI_Scholar.git
cd DailyAI_Scholar
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

### Usage

1. Run the daily paper collection:
```bash
python src/daily_top10.py
```

2. Generate paper rankings:
```bash
python src/rank_papers.py
```

## 📊 Project Structure

```
DailyAI_Scholar/
├── src/
│   ├── analysis_manager.py    # Analysis report generation
│   ├── daily_top10.py        # Daily paper collection
│   ├── paper_analyzer.py     # Paper analysis logic
│   ├── rank_papers.py       # Paper ranking system
│   └── services/            # External service integrations
├── data/                    # Data storage (gitignored)
├── requirements.txt         # Project dependencies
└── README.md               # Project documentation
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- arXiv API for providing access to research papers
- All contributors and maintainers

---

Made with ❤️ by Kororu Lab 
# DailyAI Scholar

[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

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
- **Scheduled Execution**: Automatic daily runs at 3:00 AM KST

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

#### Manual Execution

1. Run the daily paper collection:
```bash
python src/daily_top10.py
```

2. Generate paper rankings:
```bash
python src/rank_papers.py
```

#### Automated Daily Execution

The project includes a scheduler script that runs automatically at 3:00 AM KST:

```bash
# Run immediately
./run_daily.sh --now

# Schedule for next 3:00 AM KST
./run_daily.sh
```

The scheduler will:
- Run immediately if current time is before 3:00 AM KST
- Schedule for next day if current time is after 3:00 AM KST
- Automatically run every 24 hours after the initial execution

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
├── run_daily.sh           # Daily scheduler script
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

Kororu-Lab 
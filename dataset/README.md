# Dataset Documentation

This directory contains context-enhanced table datasets used for temporal table reasoning research presented in **"No Universal Prompt: Unifying Reasoning through Adaptive Prompting for Temporal Table Reasoning"**.

## Overview

The dataset collection comprises 9 benchmark datasets that have been enhanced with improved table formatting using GPT-4-mini. Each dataset is stored in JSON format and contains question-answer pairs along with structured table data.

## Dataset Files

| Filename | Description | Questions | Domain |
|----------|-------------|-----------|---------|
| `fetaqa.context.json` | FeTaQA - Question answering over Wikipedia tables | 1,582 | General Knowledge |
| `finqa.context.json` | FinQA - Financial question answering over tables | 962 | Finance |
| `hitabs.context.json` | HiTabs - Hierarchical table question answering | 897 | Structured Data |
| `hybridqa.context.json` | HybridQA - Multi-hop QA over tables and text | 1,528 | Hybrid Reasoning |
| `multi.context.json` | Multi-hop reasoning over tables | 1,587 | Complex Reasoning |
| `sqa.context.json` | SQA - Sequential question answering | 248 | Sequential Reasoning |
| `squall.context.json` | SQUALL - SQL-like natural language QA | 774 | Structured Queries |
| `tatqa.context.json` | TAT-QA - Tabular and textual question answering | 2,244 | Hybrid Data |
| `wiki.context.json` | WikiTableQuestions - Wikipedia table QA | 1,504 | General Knowledge |

**Total:** 11,326 questions across all datasets

## Data Structure

Each JSON file contains an array of objects with the following fields:

```json
{
  "_id": {
    "$oid": "unique_mongodb_object_id"
  },
  "q_num": 0,
  "question": "The question text",
  "table": "Raw table data in text/markdown format",
  "table_id": "source_table_identifier",
  "answer": "The answer or answer array",
  "improved_table_gpt4omini": "Enhanced table formatting with context"
}
```

### Field Descriptions

- **`_id`**: MongoDB ObjectId for unique identification
- **`q_num`**: Sequential question number within the dataset
- **`question`**: Natural language question about the table
  - May be a string or array of strings for sequential questions
- **`table`**: Original table data
  - Format varies by source dataset (CSV, markdown, plain text)
  - May include section headers and metadata
- **`table_id`**: Source identifier linking back to original dataset
- **`answer`**: Question answer
  - Format varies: string, array, or list representation
  - May include numerical values, dates, names, or complex lists
- **`improved_table_gpt4omini`**: GPT-4-mini enhanced version
  - Reformatted as clean markdown tables
  - Includes contextual information and descriptions
  - Improved readability and structure

## Dataset Characteristics

### FeTaQA (Fact-based Table Question Answering)
- Source: Wikipedia tables
- Focus: Free-form natural language answers
- Questions require understanding table structure and content
- Example domains: Entertainment, sports, politics, history

### FinQA (Financial Question Answering)
- Source: Financial reports and documents
- Focus: Numerical reasoning and financial metrics
- Questions often require calculations and comparisons
- Includes revenue, profit, growth rate calculations

### HiTabs (Hierarchical Tables)
- Source: Complex hierarchical table structures
- Focus: Multi-level table understanding
- Questions span across table hierarchies

### HybridQA
- Source: Wikipedia tables with associated text
- Focus: Reasoning over both tabular and textual information
- Requires multi-hop reasoning across modalities

### Multi
- Source: Various table sources
- Focus: Multi-hop reasoning chains
- Complex questions requiring multiple reasoning steps

### SQA (Sequential Question Answering)
- Source: Tables from Wikipedia
- Focus: Sequential question chains where context builds
- Questions arrays represent conversation-like sequences

### SQUALL
- Source: WikiTableQuestions
- Focus: SQL-like natural language queries
- Structured query understanding

### TAT-QA (Tabular and Textual QA)
- Source: Financial reports
- Focus: Hybrid reasoning over tables and surrounding text
- Most comprehensive financial reasoning dataset

### WikiTableQuestions
- Source: Wikipedia tables
- Focus: General knowledge QA
- Diverse question types and table structures

## Usage

### Loading Data

```python
import json

# Load a dataset
with open('dataset/fetaqa.context.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Access individual examples
example = data[0]
question = example['question']
table = example['improved_table_gpt4omini']  # Use enhanced version
answer = example['answer']
```

### Preprocessing Recommendations

1. **Use `improved_table_gpt4omini`** for better formatted tables
2. Parse answer formats based on dataset type
3. Handle sequential questions in SQA dataset as conversation chains
4. Consider table context and metadata when available

## Data Enhancement

All tables have been enhanced using GPT-4-mini to:
- Standardize table formatting to clean markdown
- Add contextual descriptions and summaries
- Improve column headers and organization
- Clarify ambiguous table elements
- Provide additional context from surrounding text

## Citation

If you use these datasets, please cite the original paper:

```bibtex
@article{sear2025,
  title={No Universal Prompt: Unifying Reasoning through Adaptive Prompting for Temporal Table Reasoning},
  author={[Authors]},
  journal={arXiv preprint},
  year={2025},
  url={https://arxiv.org/abs/2506.11246}
}
```

## Original Dataset Sources

Please also cite the original dataset papers:

- **FeTaQA**: Nan et al., "FeTaQA: Free-form Table Question Answering" (2022)
- **FinQA**: Chen et al., "FinQA: A Dataset of Numerical Reasoning over Financial Data" (2021)
- **HiTabs**: Cheng et al., "HiTAB: A Hierarchical Table Dataset for Question Answering and Natural Language Generation" (2022)
- **HybridQA**: Chen et al., "HybridQA: A Dataset of Multi-Hop Question Answering over Tabular and Textual Data" (2020)
- **SQA**: Iyyer et al., "Search-based Neural Structured Learning for Sequential Question Answering" (2017)
- **SQUALL**: Shi et al., "SQUALL: Controlled Natural Language-to-SQL Translation" (2020)
- **TAT-QA**: Zhu et al., "TAT-QA: A Question Answering Benchmark on a Hybrid of Tabular and Textual Content in Finance" (2021)
- **WikiTableQuestions**: Pasupat and Liang, "Compositional Semantic Parsing on Semi-Structured Tables" (2015)

## License

Please refer to the original dataset licenses. This enhanced version maintains the same licensing as the source datasets.

## Contact

For questions about this dataset collection, please refer to the main project README or open an issue on the GitHub repository.

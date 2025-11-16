# No Universal Prompt: Unifying Reasoning through Adaptive Prompting for Temporal Table Reasoning

Official project website for **"No Universal Prompt: Unifying Reasoning through Adaptive Prompting for Temporal Table Reasoning"**

[![ArXiv](https://img.shields.io/badge/arXiv-2506.11246-b31b1b.svg)](https://arxiv.org/abs/2506.11246)

## Overview

This repository contains the project website showcasing our research on adaptive prompting strategies for temporal table reasoning. Our work demonstrates that there is no universal prompting approach that works across all table reasoning tasks, and introduces methods to dynamically adapt prompts based on the task context.

## Resources

- **Paper**: [ArXiv 2506.11246](https://arxiv.org/abs/2506.11246)
- **Code Repository**: [TempTab-Recasting](https://github.com/kushagraDixit/TempTab-Recasting)
- **Dataset**: [Dataset Documentation](dataset/README.md) - 11,326+ questions across 9 benchmark datasets

## Repository Structure

```
SEAR/
├── index.html          # Main landing page
├── static/             # CSS and JavaScript files
├── assets/             # Images, tables, and figures
├── dataset/            # Enhanced table reasoning datasets (9 benchmarks)
│   ├── README.md       # Detailed dataset documentation
│   ├── fetaqa.context.json
│   ├── finqa.context.json
│   ├── hitabs.context.json
│   ├── hybridqa.context.json
│   ├── multi.context.json
│   ├── sqa.context.json
│   ├── squall.context.json
│   ├── tatqa.context.json
│   └── wiki.context.json
└── README.md           # This file
```

## Dataset

The [dataset folder](dataset/) contains 11,326 question-answer pairs across 9 benchmark datasets, all enhanced with improved table formatting using GPT-4-mini. See the [dataset README](dataset/README.md) for detailed documentation including:

- Dataset descriptions and statistics
- Data structure and field definitions
- Usage examples
- Citation information

### Available Datasets

- FeTaQA (1,582 questions)
- FinQA (962 questions)
- HiTabs (897 questions)
- HybridQA (1,528 questions)
- Multi (1,587 questions)
- SQA (248 questions)
- SQUALL (774 questions)
- TAT-QA (2,244 questions)
- WikiTableQuestions (1,504 questions)

## Citation

If you find this work useful, please cite our paper:

```bibtex
@article{sear2025,
  title={No Universal Prompt: Unifying Reasoning through Adaptive Prompting for Temporal Table Reasoning},
  author={[Authors]},
  journal={arXiv preprint arXiv:2506.11246},
  year={2025}
}
```

## License

[Specify License]

## Contact

For questions or feedback, please open an issue in the [code repository](https://github.com/kushagraDixit/TempTab-Recasting) or contact the authors.

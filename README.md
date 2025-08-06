# natural-chess

## Project Overview

The goal of this project was to build a natural language commentary tool for chess positions that could provide the intuition behind and commentary of chess positions by leveraging LLM finetuning. While the data acquisition pipeline was successful in creating a substantial dataset, the training notebooks are simply not worth running, as responses are still riddled with hallucinations and inaccuracies. Those notebooks are functional and can be used to train better models with more compute or when further preprocessing of the dataset is completed (e.g. truly only keeping high quality commentary, ignoring fragments, having length minimums, etc.). 

## 📊 Data Acquisition Pipeline

### 1. **Source Discovery** (`scrape_usernames.py`)
- Started with a [Lichess blog post](https://lichess.org/@/CyberShredder/blog/cool-lichess-studies-list/UOPFWocV) listing the best chess studies. 
- Scraped 94 high-quality study authors from the post

### 2. **Study Extraction** (`extract_user_studies.py`)
- Systematically downloaded PGN data for all studies from each author using the Lichess API
- Parsed PGN files to extract:
  - Chess positions (FEN notation)
  - Moves played
  - Human commentary and analysis
  - Study metadata
- Generated `lichess_studies.csv` (or whatever you want to call it) containing raw extracted data

### 3. **Data Preprocessing** (Multi-stage pipeline)

#### **First Preprocessing** (`first_preprocess.py`)
- Language detection and filtering (English only)
- FEN validation using python-chess
- UCI to SAN move notation conversion
- Removal of auto-generated content
- Quality filtering based on commentary length and content

#### **Second Preprocessing** (`second_preprocess.py`)
- Removed entries containing problematic notation:
  - `[%csl` (colored squares)
  - `[%cal` (colored arrows) 
  - `[%eval` (engine evaluations)
  - Arrow symbols (`→`)
- Final cleanup to ensure natural language only

#### **Format Conversion** (`colab_preprocess.py`)
- Converted CSV data to JSONL format for training
- Created structured instruction-input-response format
- Added a prompt for the LLM guiding it toward insightful analysis of the position.

### 4. **Final Datasets**

The pipeline produced:

- **Natural Commentary Dataset**: 45,521 chess positions with natural language analysis. However, as mentioned previously, further preprocessing is likely necessary to make the finetuned model work, as many of these positions' associated commentary is not particularly insightful, somewhat fragmented, and bypassed the previous preprocessing. This is natural and expected of Lichess studies, as not every annotated move will provide deep positional analysis.

## 🧪 Training Experiments & Lessons Learned

### Experiment 1: Direct Commentary Training
- **Model**: Llama-8B-Instruct with LoRA and 4-bit quantization
- **Result**: Failed due to dataset contamination
- **Issue**: Commentary containing evaluation notation and arrows caused the model to hallucinate non-natural language output. Inspired second round of preprocessing.

### Experiment 2: Sequential Fine-tuning Approach
- **Strategy**: Two-stage training process
  1. Fine-tune on chess literacy dataset (basic chess knowledge), sourced from: https://huggingface.co/datasets/nachors/dataset1. 
  2. Fine-tune the resulting model on cleaned natural commentary
- **Status**: Notebooks created and training ran successfully, but inference results are still poor. 

## 📁 Repository Structure

```
├── data/ # raw data files, pregenerated
│   ├── natural_commentary.jsonl       # Full commentary dataset
│   ├── literacy_train.jsonl   # Train data for literacy
│   ├── literacy_test.jsonl       # Test data for literacy 
├── data_acquisition/              # Data collection and preprocessing scripts
│   ├── scrape_usernames.py       # Extract study authors from blog post
│   ├── extract_user_studies.py   # Download and parse Lichess studies
│   ├── first_preprocess.py       # Language filtering and validation
│   ├── second_preprocess.py      # Remove problematic notation
│   └── colab_preprocess.py       # Convert to training format
├── finetune/                      # Training notebooks (educational reference)
│   ├── transformers_literacy.ipynb    # Chess literacy fine-tuning
│   └── transformers_commentary.ipynb  # Commentary fine-tuning
├── study_authors.txt             # List of 94 study authors
├── requirements.txt              # Python dependencies
```

## Getting Started

### Prerequisites
```bash
pip install -r requirements.txt
```

### Data Collection:
To generate the commentary data:

1. **Scrape study authors**:
   ```bash
   python data_acquisition/scrape_usernames.py
   ```

2. **Extract studies** (requires Lichess API token):
   ```bash
   # Update token in extract_user_studies.py
   python data_acquisition/extract_user_studies.py
   ```

3. **Preprocess data**:
   ```bash
   python data_acquisition/first_preprocess.py
   python data_acquisition/second_preprocess.py
   python data_acquisition/colab_preprocess.py
   ```

As previously mentioned, all credit to https://huggingface.co/datasets/nachors/dataset1 for the literacy data, including train test splits.

### Training Notebooks
The notebooks in `finetune/` serve as references for:
- Setting up transformer fine-tuning pipelines
- Implementing sequential fine-tuning strategies
- Working with chess-specific datasets

⚠️ **Note**: Running the notebook will not yield target results, much alteration, whether in the data pipeline or ML approach itself, is needed.

## Future Directions

For those interested in continuing this work:

1. **Increased Compute**: Use larger models or more computational resources.
2. **Better Filtering**: Develop more sophisticated content filtering and preprocessing methods.
3. **Hybrid Approaches**: Combine rule-based chess knowledge with language models.
4. **Active Learning**: Iteratively improve datasets based on model performance.
5. **Multi-modal Training**: Incorporate visual chess board representations.

# ProGo Protein Evaluation Pipeline (TM-PLDDT)

A comprehensive pipeline for protein structure prediction and evaluation using ESMfold and Foldseek, with integrated pLDDT confidence analysis.

## Overview

ProGo Protein Evaluation Pipeline is a pipeline that:
1. **Predicts protein structures using ESMfold**
2. **Compares predicted structures against ground truth structures using Foldseek**
3. **Extracts and analyzes pLDDT confidence scores from predicted structures**
4. Filters comparisons to statistically significant matches (E-value ≤ 10.0)
5. Generates detailed comparison reports and structure quality metrics
6. Performs comprehensive statistical analysis of both TM-scores and pLDDT confidence
7. Provides scientific interpretation of results
8. Automatically skips duplicate sequences that match reference sequences
9. Supports ground-truth-specific reference sequences for targeted duplicate detection

## Showcase: Pipeline Evaluation in Action

![Protein Structure Visualization](assets/Protein_Visualization.gif)

*Visualization generated on [build.nvidia.com](https://build.nvidia.com) using ESMfold predictions. This example demonstrates our pipeline evaluating generated proteins with target functional properties.* 

*The evaluated protein is associated with polyketide/non-ribosomal peptide synthetase (PKS/NRPS) systems, characterized by specific Gene Ontology (GO) terms: **GO:0031177** - Phosphopantetheine binding, **GO:0017000** - Antibiotic biosynthetic process, **GO:0008610** - Lipid biosynthetic process. These are industrially and medically important enzymes that synthesize complex natural products including antibiotics, making this an excellent showcase of functional protein generation and evaluation.* (Fischbach & Walsh, 2006; Beld et al., 2014; Gene Ontology: GO:0031177, GO:0017000, GO:0008610)

## Requirements

- Python 3.8+
- ESMfold API key (from NVIDIA)
- Python packages (install via `pip install -r requirements.txt`):
  ```
  requests>=2.31.0
  numpy>=1.24.0
  pandas>=2.0.0
  python-dotenv>=1.0.0
  pytest>=7.4.0
  tqdm>=4.65.0
  biopython>=1.81
  biotite>=0.38.0
  scikit-learn>=1.3.0
  pyyaml>=6.0.1
  jsonschema>=4.17.3
  ```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/progo-protein-evaluation-tm-plddt.git
cd progo-protein-evaluation-tm-plddt
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your NVIDIA API key:
Create a `.env` file in config/ with:
```
NVIDIA_API_KEY="your_api_key_here" 
```

eg. config/.env

## Running the Pipeline

There are three ways to run the pipeline:

### Option 1: Install as a Package (Recommended)
```bash
# Install in development mode
pip install -e .

# Then run from anywhere
proteingo predict-and-evaluate --fasta test.fasta --ground-truth-set set08
```

### Option 2: Run as a Module
```bash
# From the project root directory
python -m src.main predict-and-evaluate --fasta test.fasta --ground-truth-set set08
```

### Option 3: Direct Execution with PYTHONPATH
```bash
# Set PYTHONPATH to include the project root
PYTHONPATH=$PWD:$PYTHONPATH python src/main.py predict-and-evaluate --fasta test.fasta --ground-truth-set set08

# On Windows:
# set PYTHONPATH=%cd%;%PYTHONPATH%
# python src/main.py predict-and-evaluate --fasta test.fasta --ground-truth-set set08
```

## Data Setup

After cloning the repository, you need to set up the following data directories:

### 1. Input FASTA Files
Place your protein sequence FASTA files in:
```
data/input/
```

**Important**: All input FASTA files should be placed in the `data/input/` directory. The pipeline will automatically find them there.

Example FASTA format:
```
>protein_1
MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQAPILSRVGDGTQDNLSGAEKAVQVKVKALPDAQFEVVHSLAKWKRQTLGQHDFSAGEGLYTHMKALRPDEDRLSPLHSVYVDQWDWERVMGDGERQFSTLKSTVEAHNQEYEPGETQYLVDKFEDVLKDQRRM
>protein_2
MKDTDAGLKESPLQTPTEDGSEEPGSETSDAKSTPTAEDVTAPLVDEGAPGKQAAAQPHTEIPEGTTAEEAGIGDTPSLEDEAAGHVTQARMVSKSKDGTGSDDKKAKTSTRR
```

eg. data/input/generated-sequences.fasta

### 2. Ground Truth Structure Sets
Create directories for your ground truth structure sets in:
```
data/ground_truth/<set_name>/pdbs/
```
For example:
- `data/ground_truth/set07/pdbs/` - Place PDB/CIF files for set07
- `data/ground_truth/set08/pdbs/` - Place PDB/CIF files for set08

The pipeline supports both `.pdb` and `.cif` file formats. CIF files are automatically converted to PDB format using the biotite library.

#### Ground Truth Reference Sequences
Each ground truth set should have its own `reference_seqs.json` file:
```
data/ground_truth/<set_name>/reference_seqs.json
```

This file contains reference sequences specific to that ground truth set. When you run the pipeline with a specific ground truth set, it will use that set's reference sequences for duplicate checking.

Example structure:
```json
[
  {
    "id": "Set07_Ref1",
    "sequence": "MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQAPILSRVGDGTQDNLSGAEKAVQ...",
    "description": "Reference protein from set07"
  }
]
```

### 3. Reference Sequences (Optional)
If you want to track exact matches to reference sequences, create:
```
data/reference_seqs.json
```

**Note**: This global reference file is now optional and serves as a fallback. The pipeline will prefer ground-truth-specific reference sequences when available.

### Directory Structure After Setup
```
data/
├── input/                    # Your FASTA files
│   ├── test05.fasta
│   └── your_proteins.fasta
├── ground_truth/            # Ground truth structure sets
│   ├── set07/
│   │   ├── pdbs/           # PDB/CIF files for set07
│   │   └── reference_seqs.json  # Reference sequences for set07
│   └── set08/
│       ├── pdbs/           # PDB/CIF files for set08
│       └── reference_seqs.json  # Reference sequences for set08
├── output/                  # Generated outputs (created automatically)
└── reference_seqs.json      # Optional global reference sequences
```

**Note**: The `data/input/`, `data/ground_truth/`, and `data/reference_seqs.json` are not included in the repository and must be provided by the user.

## Usage

The pipeline supports two main modes of operation:

### 1. Predict and Evaluate Mode

This mode predicts protein structures using ESMfold and evaluates them against ground truth structures:

```bash
python -m src.main predict-and-evaluate --fasta <input.fasta> --ground-truth-set <set_name>
```

Arguments:
- `--fasta`: FASTA filename (will search in current directory and data/input/)
- `--ground-truth-set`: Name of the ground truth set to use (e.g., set08)

Example:
```bash
# Using just the filename (automatically finds it in data/input/)
python -m src.main predict-and-evaluate --fasta test05.fasta --ground-truth-set set08

# Or provide a full path
python -m src.main predict-and-evaluate --fasta /path/to/proteins.fasta --ground-truth-set set08
```

### 2. Evaluate Only Mode

This mode evaluates existing predicted structures against ground truth structures:

```bash
python -m src.main evaluate --predictions <predictions_dir> --ground-truth-set <set_name>
```

Arguments:
- `--predictions`: Name of output directory or path to predictions folder
- `--ground-truth-set`: Name of the ground truth set to use (e.g., set08)

Example:
```bash
# Using just the output directory name
python -m src.main evaluate --predictions test05 --ground-truth-set set08

# Or provide a full path
python -m src.main evaluate --predictions data/output/test05/predicted_structures --ground-truth-set set08
```

### File Resolution

The pipeline intelligently searches for files in common locations:
- FASTA files: Current directory, then data/input/
- Predictions: As provided, then data/output/<name>/predicted_structures/

### Output Directory Structure

For each run, the pipeline creates a **self-contained** output directory named after your input file:

```
<run_name>/                    # Main output directory
├── input.fasta               # Copy of original input FASTA file (predict-and-evaluate mode)
├── run_metadata.json         # Run parameters and metadata for complete self-containment
├── predicted_structures/      # Predicted PDB structures
├── analysis/                  # Analysis results directory
│   ├── analysis_results.json # Detailed analysis in JSON format
│   ├── analysis_results.csv  # Analysis results in spreadsheet format
│   └── scientific_analysis.txt # Scientific interpretation
├── detailed_tm_scores/        # Per-sequence TM-score comparisons
│   └── *.tsv                 # Tab-separated files showing all significant matches
├── comparison_results.json    # Raw comparison data
├── plddt_results.json         # Raw pLDDT confidence data and statistics
└── logs/                      # Run-specific log files
```

**Self-Contained Runs**: Each run directory now contains:
- A copy of the original input FASTA file (`input.fasta`) for predict-and-evaluate mode
- Run metadata file (`run_metadata.json`) with complete run parameters and paths
- All results, analysis, and logs

This means you can archive or share individual run directories and have all the information needed to understand and reproduce the analysis.

If a directory name conflicts with an existing one, the pipeline automatically adds a suffix (e.g., `output_protein1_run2`).

The `detailed_tm_scores/` directory contains TSV files for each sequence showing all ground truth structures that had significant similarity (E-value ≤ 10.0).

### Logging

The pipeline maintains two types of logs:
1. Run-specific logs in each output directory
2. Central logs in the `logs/` directory with format `pipeline_run_*.log`

## Helper Scripts

The pipeline includes several helper scripts for batch processing and result comparison:

### run_simple.py
Quick runner for single or multiple FASTA/ground truth combinations:
```bash
python run_simple.py <fasta_files> <ground_truth_sets>
# Examples:
python run_simple.py test.fasta set08
python run_simple.py ALL set08
python run_simple.py test1.fasta,test2.fasta set07,set08
```

### run_batch.py
Interactive batch runner with user prompts:
```bash
python run_batch.py
# Follow the prompts to select FASTA files and ground truth sets
```

### compare_results.py
Compare results across multiple runs:
```bash
python compare_results.py
# Displays a summary table of all runs with TM-score statistics
```

### cleanup.py
Remove all output directories:
```bash
python cleanup.py
# Lists all output directories and asks for confirmation before deletion
```

## Output Organization

The pipeline organizes outputs by input filename:

1. Output Directories:
   - Named based on input filename (e.g., `output_protein1/` for `protein1.fasta`)
   - Automatic handling of naming collisions with `_run{N}` suffix
   - Different naming schemes for predict-and-evaluate vs evaluate modes

2. Structure files:
   - `predicted_structures/`: Directory containing predicted PDB structures
   - `detailed_tm_scores/`: Directory containing detailed TM-score comparisons for each sequence

3. Analysis files:
   - `analysis_results.json`: Detailed analysis in JSON format
   - `analysis_results.csv`: Analysis results in spreadsheet format
   - `scientific_analysis.txt`: Scientific interpretation
   
All analysis files now include Foldseek search parameters for reference.

4. Logging System:
   - Run-specific logs in each output directory
   - Central logs in `logs/` directory
   - Each run creates `logs/pipeline_run_*.log`
   - Detailed operation logging and error tracking

## Analysis Results Details

The pipeline generates comprehensive analysis results that include:

### Summary Statistics
- Total structures analyzed
- Successful/failed comparisons
- Best overall TM-score
- Average TM-score across all sequences
- Sequences with/without TM-scores
- Exact reference matches
- Skipped duplicate sequences

### TM-Score Statistical Analysis
For all top TM-scores across sequences, the analysis calculates:
- **Highest TM-score**: Maximum score achieved
- **Lowest TM-score**: Minimum score achieved
- **Median TM-score**: Middle value of all scores
- **Average TM-score**: Mean of all top TM-scores
- **Variance**: Measure of score spread
- **Standard deviation**: Variation from the mean

### TM-Score Threshold Distribution
Counts and percentages of sequences meeting or exceeding each threshold:
- TM-score ≥ 0.0 through 1.0 (in 0.1 intervals)
- Example: "≥ 0.9: 4 sequences (80.0%)" means 80% of sequences have TM-score ≥ 0.9

### pLDDT Confidence Analysis
For all predicted structures, the analysis extracts and calculates:
- **Average pLDDT**: Sequence-level confidence score (0-100)
- **Highest pLDDT**: Maximum confidence achieved
- **Lowest pLDDT**: Minimum confidence achieved
- **Median pLDDT**: Middle confidence value
- **Variance**: Measure of confidence spread
- **Standard deviation**: Variation from the mean confidence

### pLDDT Threshold Distribution
Counts and percentages of sequences meeting or exceeding each confidence threshold:
- pLDDT ≥ 0 through 100 (in 10-point intervals)
- Example: "≥ 70: 3 sequences (60.0%)" means 60% of sequences have pLDDT ≥ 70
- **Quality Interpretation**:
  - pLDDT ≥ 90: Very high confidence (highly reliable)
  - pLDDT ≥ 70: Confident (generally reliable)
  - pLDDT ≥ 50: Low confidence (may contain significant errors)
  - pLDDT < 50: Very low confidence (likely unreliable)

### Per-Sequence Details
For each sequence:
- Maximum TM-score (best match)
- Average TM-score (across all matches)
- Number of comparisons performed
- **Average pLDDT (sequence-level confidence)**
- **Min/Max pLDDT (confidence range)**
- Success/failure status
- Error messages (if any)

### Output Formats
All analysis data is provided in three formats:
1. **JSON** (`analysis_results.json`): Complete data structure for programmatic access
2. **CSV** (`analysis_results.csv`): Tabular format for spreadsheet analysis
3. **TXT** (`scientific_analysis.txt`): Human-readable scientific interpretation
4. **Raw pLDDT Data** (`plddt_results.json`): Detailed per-residue pLDDT scores and statistics

## Features

- ESMfold integration for structure prediction
- **pLDDT confidence score extraction and analysis from predicted structures**
- Foldseek-based structure comparison (included in bin/)
- **Comprehensive statistical analysis of both TM-scores and pLDDT confidence**
- Multiple output formats (JSON, CSV, TXT)
- Detailed scientific interpretation
- Dual logging system (run-specific and central)
- Input-based output organization
- **Self-contained runs with input FASTA copy and run metadata**
- Robust error handling and logging
- Sequence validation against reference set
- **Threshold-based analysis for both TM-scores and pLDDT confidence**
- Enhanced analysis including:
  - Tracking of sequences with/without TM-scores
  - **Per-sequence pLDDT confidence analysis (avg, min, max, median, std dev)**
  - Identification of failed predictions
  - Detection of exact matches to reference sequences in `/data/reference_seqs.json`
  - Automatic skipping of duplicate sequences during prediction
  - Comprehensive reporting in JSON, CSV, and text formats
  - Documentation of Foldseek search parameters
  - **Statistical analysis of top TM-scores (highest, lowest, median, average, variance, standard deviation)**
  - **TM-score threshold distribution analysis (0.0-1.0 in 0.1 intervals)**
  - **pLDDT threshold distribution analysis (0-100 in 10-point intervals)**
  - **Percentage calculations for sequences meeting each threshold**
  - **Separate quality assessments for structural similarity (TM-score) and prediction confidence (pLDDT)**

## Foldseek Structure Comparison

The pipeline uses Foldseek for structural similarity comparisons with the following parameters:
- **max_seqs**: 1,000,000 (ensures complete coverage for research precision)
- **E-value threshold**: 10.0 (default) - filters for statistically significant matches

### Understanding Foldseek's Chain Indexing

Many PDB files contain multiple protein chains (e.g., dimers, complexes). Foldseek indexes each chain as a separate searchable entry. For example:
- A PDB file `9mhg.pdb` with 5 chains (A, B, C, D, E) becomes 5 separate entries: `9mhg_A`, `9mhg_B`, `9mhg_C`, `9mhg_D`, `9mhg_E`
- This means a ground truth set with ~9,488 PDB files may contain significantly more searchable chain entries

### Why comparison counts vary:
When comparing against a ground truth set (e.g., set08 with ~9,488 PDB files), you may notice:
1. Total comparisons can exceed the number of PDB files because Foldseek indexes each chain separately
2. E-value filtering removes structures with no meaningful similarity
3. Only statistically significant matches (E-value ≤ 10.0) are returned
4. With max_seqs set to 1M, you'll get complete coverage of all chains in all structures

**Note**: Setting max_seqs to 1,000,000 ensures complete coverage but will significantly increase processing time and output file sizes. This is recommended for research requiring comprehensive analysis.

## Structure

```
progo-protein-evaluation-tm-plddt/
├── bin/                    # Platform-specific Foldseek binaries
├── src/
│   ├── main.py            # Main entry point
│   ├── pipeline/          # Core pipeline modules
│   ├── analysis/          # Analysis modules
│   └── utils/             # Utility functions
├── tests/                 # Test suite
├── data/                  # Data files
├── logs/                  # Central logging directory
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Included Tools

The pipeline includes platform-specific Foldseek binaries in the `bin/` directory:
- `foldseek_linux_x64`: Linux x86_64 binary
- `foldseek_linux_arm64`: Linux ARM64 binary
- `foldseek_mac_x64`: macOS x86_64 binary
- `foldseek_mac_arm64`: macOS ARM64 binary

These binaries are automatically detected and used based on your system architecture.

## Contributing

Project By:
Darren Tan (NVIDIA), Ian McLoughlin (SIT), Aik Beng Ng (NVIDIA), Daniel Wang Zhengkui (SIT), Abraham Stern (NVIDIA), Simon See (NVIDIA)

An NVIDIA AI Technology Centre, Asia Pacific South (NVAITC APS) project.

Co-supervised by Singapore Institute of Technology (SIT), a collaboration between NVAITC APS and SIT

## Updates
- [2024-08-18] by Darren Tan: Updated README, fixed naming
- [2024-08-19] by Darren Tan: Added showcase visualization demonstrating pipeline evaluation results

## License

MIT License - see [LICENSE](LICENSE) file for details.

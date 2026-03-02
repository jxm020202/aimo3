# Competition Rules & Structure

## Key Dates
- **Start**: November 20, 2025
- **Entry deadline**: April 8, 2026
- **Final submission deadline**: April 15, 2026
- **Model cutoff**: March 15, 2026 (AMLTs used at runtime must be released before this)
- **Longest Leader Prize**: Ended February 2, 2026 (CLOSED)
- **Math Corpus Prize**: Ended February 9, 2026 (CLOSED)

## Prizes Still Available
| Prize | Amount | Criteria |
|-------|--------|----------|
| 1st Place | $262,144 | Highest private LB score |
| 2nd Place | $131,072 | |
| 3rd Place | $65,536 | |
| 4th Place | $32,768 | |
| 5th Place | $16,384 | |
| 47/50 Bonus | $1,589,248+ | Highest team with ≥47/50 on BOTH public AND private |
| Hard Problem | $30,000 | Highest ranked team that solved the hardest problem(s) |
| Writeup (x2) | $15,000 each | Best technical writeups from non-winning teams |

## Submission Rules
- **1 submission per day**
- **1 final submission** selected for judging
- **No internet** during notebook execution
- **Must run as Jupyter Notebook** on Kaggle's compute
- **H100 GPUs** provided

## Model Rules (AMLT)
- Models used **at runtime** must be **open-weight** (e.g., GPT-OSS OK, GPT-5 NOT OK)
- Models used at runtime must be released **before March 15, 2026**
- Models used **only for data generation** (not runtime) can be commercial and have no date restriction
  - Example: GPT-4 to generate training data → fine-tune open-weight model = OK
- All submissions must be **fully reproducible**
- Spot checks on submitted models will be conducted

## Evaluation
- 110 original problems: 50 public, 50 private, 10 reference
- 5-digit integer answers (0-99999)
- Private LB: Each submission run TWICE
  - Both runs correct → 1 point
  - One run correct → 0.5 points
  - Both wrong → 0 points
- This penalizes non-deterministic solutions (stochastic sampling)
- Ties broken by submission time (earlier wins)

## Winner Obligations
- Open-source all code, data, weights (CC-BY 4.0)
- Host model on HuggingFace
- Containerize solution in Singularity container
- Participate in writing a paper with hosts
- Provide detailed reproducibility documentation
- Complete AML/KYC checks

## Team Rules
- Max team size: 20
- Team mergers allowed before deadline
- No private code sharing between teams
- Public code sharing on Kaggle forums/notebooks is OK

## External Data & Tools
- External data must be publicly available and equally accessible
- "Reasonableness Standard" for costs
- Open-source tools (ADTs) must have appropriate licenses
- All artifacts used in pipeline must be documented

## Sponsor
XTX Investments Limited (London-based quantitative trading firm)

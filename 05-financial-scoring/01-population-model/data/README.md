# Financial Scoring — Data

This folder is intentionally empty in the public repository.

The Financial Health Scoring pipeline uses proprietary and/or generated datasets that are not committed to GitHub due to data privacy, confidentiality, and repository size constraints.

The datasets used during development include:
- SME population and financial data
- Credit bureau information
- Director-level credit information
- Transaction-level data
- Engineered modelling datasets

The required datasets are processed locally through the pipeline scripts in:

`01-population-model/scripts/`

Generated modelling outputs are also excluded from version control because some files exceed GitHub's file size limits.

This structure allows the repository to demonstrate the complete analytical and modelling workflow without exposing sensitive data or unnecessarily storing large generated files.

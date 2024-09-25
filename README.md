Fully offline, modern looking tool for analysis of personal finance. Made with Streamlit.

# Installation
* make sure you have `poetry` installed (https://python-poetry.org/docs/#installation)
* run `poetry install` in project's directory. This will create a virtual environment (by default in `./.venv`)
* run `poetry shell` to activate the environment
* run `streamlit run ./project/app.py` to start the app

# Usage
* put your transactions data in `./data/transactions`
  * ING (Polish) 
    * go to `https://login.ingbank.pl/`
    * go to transactions history
    * get the list of transactions as CSV
    * place the file in `./data/transactions/ing/`
  * mBank (Polish) 
    * (...)
    * place the file in `./data/transactions/mbank/`
  * generic format
    * prepare your csv that have these columns: `["transaction_date", "contractor", "transaction_id", "title", "amount", "account_name"]`
    * place the file in `./data/transactions/generic`
* work on your categories (`./data/categories/categories_conditions.csv`)

# Demo
visit: https://money-insights.streamlit.app/
![](images/streamlit-app-2024-04-11-21-04-86.gif)
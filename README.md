Fully offline, modern looking tool for personal finance analysis. Made with Streamlit.

# Installation
* make sure you have `poetry` installed (https://python-poetry.org/docs/#installation)
* set `poetry config virtualenvs.in-project true` to have the virtualenv in project's directory
* run `poetry install` in project's directory. This will create a virtual environment in `./.venv`
* run `poetry run streamlit run .\project\Home.py` to start the app

# Usage
* put your transactions data in `./data/transactions`
  * ING (Polish) 
    * go to `https://login.ingbank.pl/`
    * go to transactions history
    * get the list of transactions as CSV
    * place the file in `./data/transactions/ing/`
  * mBank (Polish) 
    * login
    * finanse -> historia ->zestawienie operacji
    * od 2000
    * format: csv
    * place the file in `./data/transactions/mbank/`
  * generic format
    * prepare your csv that have these columns: `["transaction_date", "contractor", "transaction_id", "title", "amount", "account_name"]`
    * place the file in `./data/transactions/generic`
* work on your categories (`./data/categories/categories_conditions.csv`)

# Demo
visit: https://money-insights.streamlit.app/
![](images/streamlit-app-2024-04-11-21-04-86.gif)
# library-checker to tioj exporter

Export [library-checker-problems](https://github.com/yosupo06/library-checker-problems/) to [TIOJ](https://github.com/TIOJ-INFOR-Online-Judge/tioj).

Preparation:
- grab libray-checker-problems to `libray_checker_problems`
- `ln -s library_checker_problems/toml.py toml.py`
- `python3 -m venv env`
- `. env/bin/activate`
- `pip install -r requirements.txt`

To export some problem to TIOJ, first edit `config.py`, `problems.toml`.

Then use `. env/bin/activate` to activate virtual environment, and then run `./export_testdata.py` or `./export_statement.py`.

**Remember to `git pull` before running the script**

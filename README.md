# library-checker to tioj exporter

Export [library-checker-problems](https://github.com/yosupo06/library-checker-problems/) to [TIOJ](https://github.com/TIOJ-INFOR-Online-Judge/tioj).

## Usage

Preparation:
- grab libray-checker-problems to `libray_checker_problems`
- `ln -s library_checker_problems/toml.py toml.py`
- `python3 -m venv env`
- `. env/bin/activate`
- `pip install -r requirements.txt`

To export some problem to TIOJ, first edit `config.py`, `problems.toml`.

Then use `. env/bin/activate` to activate virtual environment, and then run `./export_testdata.py` or `./export_statement.py`.

**Remember to `git pull` before running the script**

Note that `export_statement.py` will upload the `checker.cpp` to TIOJ with `testlib.h` replaced to `tioj_testlib.h`, which expects to be a [modified version](https://raw.githubusercontent.com/baluteshih/tioj-problem-tools/9db3da1b82d036750f0e660abdd9dfec0bb6abb5/files/testlib.h) of `testlib.h` for TIOJ. This header is required when installing `tioj-judge`.

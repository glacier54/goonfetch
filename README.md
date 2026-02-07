# goonfetch
Cli rule34 fetching tool

How to use:
create `config.toml` in `.config/goonfetch/`

example:
```toml
auth = "api_key=[API_KEY]&user_id=[USER_ID]" # get api key from https://rule34.xxx/index.php?page=account&s=options, after making an account
tags = "-ai_generated -video score:>10 -anthro -ai_assisted -animal -beastiality"
```

Build:
idk use `pyinstaller --onefile main.py` after installing the dependencies?

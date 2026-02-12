# goonfetch
Cli rule34 fetching tool

I added an aur repo, but I can't guarantee it'll work right away `yay goonfetch`

How to use:
create `config.toml` in `.config/goonfetch/`

example:
```toml
# .config/goonfetch/config.toml
default = "rule34" # default api supplier
# get api key from i.e. https://rule34.xxx/index.php?page=account&s=options, after making an account, keep in mind you need a different api key per supplier
tags = "-ai_generated -video score:>10 -beastiality -loli -rape -webm -scat -young -animated"
api_key = "[API_KEY]"
user_id = "[USER_ID]"
# or: auth = "api_key=[API_KEY]&user_id=[USER_ID]"
[e621]
api_key = "[API_KEY]"
login = "[USERNAME]"
# or: auth = "api_key=[API_KEY]&login=[USERNAME]"
tags = "-young -shota -loli -scat -watersports -gore -video -webm -animated score:>10"
[gelbooru]
api_key = "[API_KEY]"
user_id = "[USER_ID]"
# or: auth = "api_key=[API_KEY]&user_id=[USER_ID]"
tags = "-young -shota -loli -scat -watersports -gore -video -webm -animated score:>10"

```
Build:
```
git clone https://github.com/glacier54/goonfetch
cd goonfetch
uv sync
```
If you want to be able to run it as a command, create this file in `/usr/bin/goonfetch`:
```
#!/usr/bin/env bash
cd [full path to your goonfetch folder] || exit 1
poetry run python main.py "$@"
```
and run `sudo chmod +x /usr/bin/goonfetch` for execution perms.

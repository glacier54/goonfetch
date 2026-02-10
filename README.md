# goonfetch
Cli rule34 fetching tool

I added an aur repo, but I can't guarantee it'll work right away `yay goonfetch`

How to use:
create `config.toml` in `.config/goonfetch/`

example:
```toml
# .config/goonfetch/config.toml
default = "rule34" # default api supplier
[rule34]
auth = "api_key=[API_KEY]&user_id=[USER_ID]" # get api key from https://rule34.xxx/index.php?page=account&s=options, after making an account
tags = "-ai_generated -video score:>10 -anthro -ai_assisted -animal -beastiality"

[e621]
auth = "login=api_key=[API_KEY]&user_id=[USER_ID]"
tags = "-young -shota -loli -scat -watersports -gore -video -webm -animated score:>10"
[e621]
auth = "login=[API_KEY]&user_id=[USER_ID]"
tags = "-young -shota -loli -scat -watersports -gore -video -webm -animated score:>10"
[gelbooru]
auth = "login=api_key=[API_KEY]&user_id=[USER_ID]"
tags = "-young -shota -loli -scat -watersports -gore -video -webm -animated score:>10"
```
Build:
```
git clone https://github.com/glacier54/goonfetch
cd goonfetch
poetry install --no-root
```
If you want to be able to run it as a command, create this file in `/usr/bin/goonfetch`:
```
#!/usr/bin/env bash
cd [full path to your goonfetch folder] || exit 1
poetry run python main.py "$@"
```
and run `sudo chmod +x /usr/bin/goonfetch` for execution perms.

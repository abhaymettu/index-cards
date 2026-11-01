# git tricks

## undoing stuff

- `git restore --staged <file>` unstages, keeps edits. Way clearer than old `reset HEAD`.
- `git restore <file>` throws away working changes. No undo for this one, careful.
- `git reset --soft HEAD~1` undoes last commit but keeps everything staged. Good for "oops wrong message" or "should've been two commits".
- `git reset --hard` only when I'm sure. If I'm not sure, `git stash` first.
- `git reflog` is the safety net. Lost a commit after bad rebase? Find the hash there, `git reset --hard <hash>` or `git branch rescue <hash>`. Entries stick around ~90 days by default.
- `git revert <sha>` for stuff already pushed to a shared branch. Don't rewrite history there.

## cleaner history

- `git commit --fixup <sha>` then `git rebase -i --autosquash <base>`. Saves me from hand-editing the todo list.
- `git commit --amend --no-edit` after forgetting a file.
- `git pull --rebase` to avoid the pointless merge commits. Set it globally: `git config --global pull.rebase true`.
- `git rebase --onto <newbase> <oldbase> <branch>` when a branch was cut from the wrong place. Confusing but works, reread the arg order every time.
- `git push --force-with-lease` instead of `--force`. Fails if someone else pushed since my last fetch.

## finding things

- `git log -S"some_string"` finds commits that added/removed that string (pickaxe). `-G` for regex.
- `git log --follow -- <path>` tracks a file across renames.
- `git blame -w -C -C` ignores whitespace and detects moved code. Less noise.
- `git bisect start`, `bisect bad`, `bisect good <sha>`. Can automate with `git bisect run <script>` if there's a test that exits nonzero.
- `git log --oneline --graph --decorate --all` aliased to `git lg`. Use it constantly.
- `git diff --stat main...HEAD` (three dots) shows only what my branch changed since it diverged.

## stash and worktrees

- `git stash -u` includes untracked files. Plain `stash` leaves them behind and that bites me.
- `git stash push -m "msg"` so the list is readable later.
- `git stash show -p stash@{1}` to peek before applying.
- `git worktree add ../scratch <branch>` gives a second checkout without cloning. Great for reviewing something while mid-change. Remove with `git worktree remove ../scratch`.

## misc

- `git switch -` jumps back to the previous branch, like `cd -`.
- `git branch --merged main` lists safe-to-delete branches.
- `git config --global rerere.enabled true` remembers conflict resolutions, helps with repeated rebases.
- `git add -p` to stage hunks. Forces me to actually review what I'm committing.

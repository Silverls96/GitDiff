# Git Diff Script

This Python script is designed to display git diffs. It can show local unstaged/staged changes or compare two branches. You can also exclude specific files or directories from the diff output.

## Usage

```bash
python get_git_diff.py [repo_path] [options]
```

**Parameters:**

- **repo_path**  
  _(Optional)_ Path to the Git repository. Default is the current directory (`.`).

**Options:**

- **-c, --compare**  
  Compare two branches instead of showing local changes.

- **-s, --feature_branch**  
  Specify the feature branch containing your changes. If not provided, the script will default to the current branch.

- **-t, --target_branch**  
  Specify the target branch you plan to merge into. This is required when using the compare option.

- **-o, --output**  
  Specify the output file name for the diff result. If not provided, the default is `gitbranch.diff` inside the repository path.

- **-e, --exclude**  
  Exclude files or directories matching the given pattern from the diff. This option can be used multiple times. By default, the folder `src/Migration/Infrastructure/Persistence/Migrations/` is excluded.

## Examples

1. **Show Local Changes**  
   Display unstaged and staged changes in the current repository and output the result to the default file:
   ```bash
   python get_git_diff.py
   ```

2. **Compare Branches Using Current Branch as Feature**  
   Compare the current branch (as the feature branch) with the `main` branch:
   ```bash
   python get_git_diff.py -c -t main
   ```

3. **Compare Two Specific Branches**  
   Compare a specific feature branch with a target branch:
   ```bash
   python get_git_diff.py -c -s feature-branch -t develop
   ```

4. **Specify a Custom Output File and Additional Exclusions**  
   Compare branches, output the diff to `custom_diff.diff`, and exclude additional files (e.g., `.env`):
   ```bash
   python get_git_diff.py -c -s feature-branch -t develop -o custom_diff.diff -e .env
   ```

How to run the script using bat file
```
run.bat <folder of git> -c -s <source> -t <target> -o <outputfile>
```
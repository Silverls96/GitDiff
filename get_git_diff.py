from multiprocessing.spawn import prepare
from xml.dom.minidom import Document
import git
import argparse
import os


def get_git_diff(repo_path, output_file, exclude_patterns):
    try:
        # Open the repository
        repo = git.Repo(repo_path)
        
        # Ensure the repo is not bare
        if repo.bare:
            print("Error: Repository is bare")
            return
        
        # Prepare exclusion arguments
        exclude_args = [f":(exclude){pattern}" for pattern in exclude_patterns]
        
        # Get the git diff (unstaged changes)
        unstaged_diff = repo.git.diff("--", *exclude_args)
        
        # Get staged changes
        staged_diff = repo.git.diff('--cached', *exclude_args)

        output = f"Repository: {repo_path}\n\n==== Unstaged Changes ====\n"
        output += unstaged_diff if unstaged_diff else "No unstaged changes."
        output += "\n\n==== Staged Changes ====\n"
        output += staged_diff if staged_diff else "No staged changes."
        
        print(output)
        write_to_file(output_file, output)
    except git.exc.InvalidGitRepositoryError:
        print("Error: Not a valid git repository.")
    except Exception as e:
        print(f"Error: {e}")

def get_branch_diff(repo_path, feature_branch, target_branch, output_file, exclude_patterns):
    """Compare two branches and show the diff between them."""
    try:
        repo = git.Repo(repo_path)
        if repo.bare:
            print("Error: Repository is bare")
            return

        # Get current branch if feature_branch is None
        if feature_branch is None:
            feature_branch = repo.active_branch.name
            print(f"No feature branch specified. Using current branch: {feature_branch}")

        # Check if the target branch exists locally. If not, try checking remote.
        if target_branch not in repo.heads:
            print(f"Error: Target branch '{target_branch}' does not exist locally.")
            remote_target = f"origin/{target_branch}"
            if remote_target in repo.refs:
                print(f"Target branch '{target_branch}' not found locally. Using remote branch '{remote_target}'.")
                target_branch = remote_target
            else:
                msg = f"Error: Target branch '{target_branch}' does not exist locally or remotely."
                print(msg)
                write_to_file(output_file, msg)
                return
            
         # Check if the feature branch exists locally. If not, try checking remote.
        if feature_branch not in repo.heads:
            # Check if the remote has the branch (assuming origin)
            remote_feature = f"origin/{feature_branch}"
            if remote_feature in repo.refs:
                print(f"Feature branch '{feature_branch}' not found locally. Using remote branch '{remote_feature}'.")
                feature_branch = remote_feature
            else:
                msg = f"Error: Feature branch '{feature_branch}' does not exist locally or remotely."
                print(msg)
                write_to_file(output_file, msg)
                return

        # Build exclusion arguments.
        exclude_args = [f":(exclude){pattern}" for pattern in exclude_patterns] if exclude_patterns else []


        # Get the diff. This shows changes in the feature branch relative to the target branch.
        diff = repo.git.diff(target_branch, feature_branch, "--", *exclude_args)
        output = (f"Diff between target branch '{target_branch}' and feature branch "
                  f"'{feature_branch}':\n{diff if diff else 'No differences found between the branches.'}")
        print(output)
        write_to_file(output_file, output)
    
    except git.exc.InvalidGitRepositoryError:
        print(f"Error: {repo_path} is not a valid git repository.")
    except Exception as e:
        print(f"Error: {e}")
    
def write_to_file(filename, content):
    """Write content to file and notify the user."""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"\nDiff result saved to file: {filename}")
    except Exception as e:
        print(f"Error writing to file {filename}: {e}")

# def review_code_with_openai(diff):
#     """Send the Git diff to OpenAI for a code review."""
#     if not diff.strip():
#         return "No changes detected."

#     openai.api_key = os.getenv("OPENAI_API_KEY")
#     prompt = f"Review the following Git diff for code quality, best practices, and possible improvements:\n\n{diff}"

#     response = openai.ChatCompletion.create(
#         model="gpt-4",
#         messages=[{"role": "system", "content": "You are a senior software engineer performing a code review."},
#                   {"role": "user", "content": prompt}]
#     )

#     return response["choices"][0]["message"]["content"]

def prepare_args():
    parser = argparse.ArgumentParser(
        description="Get git diffs. By default, shows local changes; use '--compare' to compare branches."
    )
    parser.add_argument("repo_path", nargs="?", default=".", help="Path to the Git repository (default: current directory)")
    
    # Optional arguments for branch comparison
    parser.add_argument("-c", "--compare", action="store_true", help="Compare two branches instead of showing local changes")
    parser.add_argument("-s", "--feature_branch", type=str, help="Feature branch with your changes. Defaults to current branch if not provided.")
    parser.add_argument("-t", "--target_branch", type=str, help="Target branch you plan to merge into (required when comparing).")

    # Optional argument to specify output file name (default: git.diff)
    parser.add_argument("-o", "--output", type=str,
                        help="File name to output the diff result (default: gitbranch.diff)")
    # Option to exclude files by pattern. Multiple --exclude can be provided.
    parser.add_argument("-e", "--exclude", action="append", default=["src/Migration/Infrastructure/Persistence/Migrations/"],
                        help="File or directory pattern to exclude (can be used multiple times)")

    args = parser.parse_args()
    return args

# def main():
#      try:
#         diff = get_git_diff(args.repo_path, args.feature_branch if args.compare else None, args.target_branch)
#         review = review_code_with_openai(diff)
#         print("\n==== AI Code Review ====\n")
#         print(review)
#     except Exception as e:
#         print(f"Error: {e}")

if __name__ == "__main__":
    args = prepare_args()
    
     # Determine the output file path: default is inside repo_path with filename "gitdiff"
    output_file = args.output if args.output else os.path.join(args.repo_path, "gitbranch.diff")
    
    if args.compare:
        # For branch comparison, target_branch must be provided.
        if not args.target_branch:
            print("For branch comparison, please provide a target branch using -t or --target_branch")
        else:
            get_branch_diff(args.repo_path, args.feature_branch, args.target_branch, output_file, args.exclude)

    else:
        get_git_diff(args.repo_path, output_file, args.exclude)
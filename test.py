import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import tempfile
import io
import git

import get_git_diff as ggd

class TestGitDiffUtility(unittest.TestCase):
    
    def setUp(self):
        # Create a temporary directory and file for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_output = os.path.join(self.temp_dir.name, "test_output.diff")
        
        # Mock the git.Repo object
        self.mock_repo_patcher = patch('git.Repo')
        self.mock_repo = self.mock_repo_patcher.start()
        
        # Set up the mock repo instance
        self.repo_instance = MagicMock()
        self.mock_repo.return_value = self.repo_instance
        
        # Mock the repo.git attribute
        self.repo_instance.git = MagicMock()
        
        # Set repo.bare to False
        self.repo_instance.bare = False
        
    def tearDown(self):
        # Clean up the temporary directory
        self.temp_dir.cleanup()
        self.mock_repo_patcher.stop()
    
    def test_get_git_diff_success(self):
        """Test successful git diff for local changes"""
        # Mock the git diff responses
        self.repo_instance.git.diff.side_effect = [
            "Sample unstaged diff",  # First call for unstaged changes
            "Sample staged diff"     # Second call for staged changes
        ]
        
        # Redirect stdout to capture print statements
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        # Call the function
        ggd.get_git_diff("/mock/repo/path", self.temp_output, ["node_modules"])
        
        # Reset stdout
        sys.stdout = sys.__stdout__
        
        # Check that the mock was called correctly
        self.repo_instance.git.diff.assert_any_call("--", ":(exclude)node_modules")
        self.repo_instance.git.diff.assert_any_call("--cached", ":(exclude)node_modules")
        
        # Verify the output file was created with correct content
        with open(self.temp_output, 'r') as f:
            content = f.read()
            self.assertIn("Repository: /mock/repo/path", content)
            self.assertIn("Sample unstaged diff", content)
            self.assertIn("Sample staged diff", content)
            
        # Check print output
        self.assertIn("Diff result saved to file", captured_output.getvalue())
    
    def test_get_git_diff_no_changes(self):
        """Test git diff with no changes"""
        # Mock the git diff responses with empty strings (no changes)
        self.repo_instance.git.diff.side_effect = ["", ""]
        
        ggd.get_git_diff("/mock/repo/path", self.temp_output, [])
        
        # Verify the output file has correct content for no changes
        with open(self.temp_output, 'r') as f:
            content = f.read()
            self.assertIn("No unstaged changes", content)
            self.assertIn("No staged changes", content)
    
    def test_get_git_diff_invalid_repo(self):
        """Test handling invalid git repository"""
        # Mock the Repo constructor to raise InvalidGitRepositoryError
        self.mock_repo.side_effect = git.exc.InvalidGitRepositoryError
        
        # Redirect stdout to capture print statements
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        ggd.get_git_diff("/not/a/repo", self.temp_output, [])
        
        # Reset stdout
        sys.stdout = sys.__stdout__
        
        # Check error message
        self.assertIn("Error: Not a valid git repository", captured_output.getvalue())
        
    @patch('get_git_diff.write_to_file')
    def test_get_branch_diff_success(self, mock_write):
        """Test successful branch comparison"""
        # Configure repo mock
        self.repo_instance.heads = ['main', 'feature']
        self.repo_instance.refs = ['origin/main', 'origin/feature']
        self.repo_instance.git.diff.return_value = "Sample branch diff"
        
        # Redirect stdout to capture print statements
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        ggd.get_branch_diff("/mock/repo/path", "feature", "main", self.temp_output, [])
        
        # Reset stdout
        sys.stdout = sys.__stdout__
        
        # Check diff was called with correct branches
        self.repo_instance.git.diff.assert_called_once_with("main", "feature", "--")
        
        # Verify write_to_file was called with correct content
        mock_write.assert_called_once()
        self.assertIn("feature", mock_write.call_args[0][1])
        self.assertIn("main", mock_write.call_args[0][1])
        self.assertIn("Sample branch diff", mock_write.call_args[0][1])
    
    @patch('get_git_diff.write_to_file')
    def test_get_branch_diff_use_current_branch(self, mock_write):
        """Test branch comparison with current branch as feature branch"""
        # Configure repo mock for active branch
        active_branch = MagicMock()
        active_branch.name = "current-branch"
        self.repo_instance.active_branch = active_branch
        self.repo_instance.heads = ['main', 'current-branch']
        
        ggd.get_branch_diff("/mock/repo/path", None, "main", self.temp_output, [])
        
        # Check we used the current branch
        self.repo_instance.git.diff.assert_called_once_with("main", "current-branch", "--")
    
    @patch('get_git_diff.write_to_file')
    def test_get_branch_diff_remote_branch(self, mock_write):
        """Test branch comparison with remote branch"""
        # Configure repo mock with only remote branch
        self.repo_instance.heads = ['feature']  # main not in local heads
        self.repo_instance.refs = ['origin/main', 'origin/feature']
        
        ggd.get_branch_diff("/mock/repo/path", "feature", "main", self.temp_output, [])
        
        # Check we used the remote branch
        self.repo_instance.git.diff.assert_called_once_with("origin/main", "feature", "--")
    
    @patch('get_git_diff.write_to_file')
    def test_get_branch_diff_nonexistent_branches(self, mock_write):
        """Test branch comparison with nonexistent branches"""
        # Configure repo mock with no matching branches
        self.repo_instance.heads = ['dev']
        self.repo_instance.refs = ['origin/dev']
        
        # Redirect stdout to capture print statements
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        ggd.get_branch_diff("/mock/repo/path", "feature", "main", self.temp_output, [])
        
        # Reset stdout
        sys.stdout = sys.__stdout__
        
        # Check error messages
        self.assertIn("does not exist locally or remotely", captured_output.getvalue())
        
    def test_write_to_file(self):
        """Test writing content to file"""
        test_content = "Test content for file writing"
        
        # Redirect stdout to capture print statements
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        ggd.write_to_file(self.temp_output, test_content)
        
        # Reset stdout
        sys.stdout = sys.__stdout__
        
        # Verify the file was created with correct content
        with open(self.temp_output, 'r') as f:
            content = f.read()
            self.assertEqual(content, test_content)
            
        # Check print output
        self.assertIn(f"Diff result saved to file: {self.temp_output}", captured_output.getvalue())
    
    @patch('argparse.ArgumentParser.parse_args')
    def test_prepare_args(self, mock_parse_args):
        """Test argument parsing"""
        # Configure mock args
        mock_args = MagicMock()
        mock_args.repo_path = "/test/repo"
        mock_args.compare = True
        mock_args.feature_branch = "feature"
        mock_args.target_branch = "main"
        mock_args.output = "output.diff"
        mock_args.exclude = ["node_modules", "*.log"]
        mock_parse_args.return_value = mock_args
        
        # Call the function
        args = ggd.prepare_args()
        
        # Verify the args
        self.assertEqual(args.repo_path, "/test/repo")
        self.assertTrue(args.compare)
        self.assertEqual(args.feature_branch, "feature")
        self.assertEqual(args.target_branch, "main")
        self.assertEqual(args.output, "output.diff")
        self.assertEqual(args.exclude, ["node_modules", "*.log"])

if __name__ == '__main__':
    unittest.main()
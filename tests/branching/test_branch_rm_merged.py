import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from sc.branching.commands.branch_rm_merged import BranchRmMerged
from sc.exceptions import ScError


class TestBranchRmMerged(unittest.TestCase):
    @patch("sc.branching.commands.branch_rm_merged.BranchRmMerged._error_on_sc_uninitialised")
    def test_verify_options_errors_with_all_and_not_merged(
        self, error_on_sc_uninitialised
    ):
        cmd = BranchRmMerged(top_dir=Path("/workspace"), all=True, not_merged=True)

        with self.assertRaisesRegex(ScError, "Cannot pass both --all and --no-merged"):
            cmd.run_repo_command()
        error_on_sc_uninitialised.assert_called_once_with()

    @patch("sc.branching.commands.branch_rm_merged.Delete")
    @patch("sc.branching.commands.branch_rm_merged.TicketService")
    @patch("sc.branching.commands.branch_rm_merged.BranchRmMerged._get_feature_branches")
    @patch("sc.branching.commands.branch_rm_merged.BranchRmMerged._error_on_sc_uninitialised")
    def test_run_repo_command_deletes_without_prompt(
        self,
        error_on_sc_uninitialised,
        get_feature_branches,
        ticket_service_cls,
        delete_cls,
    ):
        top_dir = Path("/workspace")

        branch = Mock()
        branch.name = "feature/donut"

        ticket = Mock()
        ticket.to_terminal.return_value = "TICKET-123 donut"
        ticket_service_cls.return_value.get_ticket_from_branch.return_value = ticket

        get_feature_branches.return_value = [branch]

        cmd = BranchRmMerged(top_dir=top_dir, no_prompt=True)
        cmd.run_repo_command()

        error_on_sc_uninitialised.assert_called_once_with()
        get_feature_branches.assert_called_once_with(top_dir)
        ticket_service_cls.return_value.get_ticket_from_branch.assert_called_once_with(
            "feature/donut"
        )
        delete_cls.assert_called_once_with(top_dir, branch, remote=True)
        delete_cls.return_value.run_repo_command.assert_called_once_with()
        delete_cls.return_value.run_git_command.assert_not_called()

    @patch("sc.branching.commands.branch_rm_merged.Delete")
    @patch("sc.branching.commands.branch_rm_merged.TicketService")
    @patch("sc.branching.commands.branch_rm_merged.BranchRmMerged._get_feature_branches")
    def test_run_git_command_deletes_using_git_command(
        self,
        get_feature_branches,
        ticket_service_cls,
        delete_cls,
    ):
        top_dir = Path("/repo")

        branch = Mock()
        branch.name = "feature/donut"

        ticket_service_cls.return_value.get_ticket_from_branch.return_value.to_terminal.return_value = (
            "TICKET-123 donut"
        )
        get_feature_branches.return_value = [branch]

        cmd = BranchRmMerged(top_dir=top_dir, no_prompt=True)
        cmd.run_git_command()

        get_feature_branches.assert_called_once_with(top_dir)
        delete_cls.assert_called_once_with(top_dir, branch, remote=True)
        delete_cls.return_value.run_git_command.assert_called_once_with()
        delete_cls.return_value.run_repo_command.assert_not_called()

    @patch("sc.branching.commands.branch_rm_merged.Prompter.yn", return_value=False)
    @patch("sc.branching.commands.branch_rm_merged.Delete")
    @patch("sc.branching.commands.branch_rm_merged.TicketService")
    @patch("sc.branching.commands.branch_rm_merged.BranchRmMerged._get_feature_branches")
    @patch("sc.branching.commands.branch_rm_merged.BranchRmMerged._error_on_sc_uninitialised")
    def test_run_repo_command_does_not_delete_when_prompt_declines(
        self,
        error_on_sc_uninitialised,
        get_feature_branches,
        ticket_service_cls,
        delete_cls,
        prompt_yn,
    ):
        top_dir = Path("/workspace")

        branch = Mock()
        branch.name = "feature/donut"
        get_feature_branches.return_value = [branch]
        ticket_service_cls.return_value.get_ticket_from_branch.return_value.to_terminal.return_value = (
            "TICKET-123 donut"
        )

        cmd = BranchRmMerged(top_dir=top_dir)
        cmd.run_repo_command()

        prompt_yn.assert_called_once_with("Delete branch?")
        delete_cls.assert_not_called()

    @patch("sc.branching.commands.branch_rm_merged.Prompter.yn")
    @patch("sc.branching.commands.branch_rm_merged.Delete")
    @patch("sc.branching.commands.branch_rm_merged.TicketService")
    @patch("sc.branching.commands.branch_rm_merged.BranchRmMerged._get_feature_branches")
    @patch("sc.branching.commands.branch_rm_merged.BranchRmMerged._error_on_sc_uninitialised")
    def test_run_repo_command_no_prompt_does_not_prompt(
        self,
        error_on_sc_uninitialised,
        get_feature_branches,
        ticket_service_cls,
        delete_cls,
        prompt_yn,
    ):
        branch = Mock()
        branch.name = "feature/donut"
        get_feature_branches.return_value = [branch]
        ticket_service_cls.return_value.get_ticket_from_branch.return_value.to_terminal.return_value = (
            "TICKET-123 donut"
        )

        cmd = BranchRmMerged(top_dir=Path("/workspace"), no_prompt=True)
        cmd.run_repo_command()

        prompt_yn.assert_not_called()
        delete_cls.assert_called_once()

    @patch("sc.branching.commands.branch_rm_merged.GitFlowLibrary.get_git_root")
    @patch("sc.branching.commands.branch_rm_merged.BranchRmMerged._rm_merged")
    @patch("sc.branching.commands.branch_rm_merged.BranchRmMerged._error_on_sc_uninitialised")
    def test_run_repo_command_git_only_uses_current_git_root(
        self,
        error_on_sc_uninitialised,
        rm_merged,
        get_git_root,
    ):
        git_root = Path("/workspace/project")
        get_git_root.return_value = git_root

        cmd = BranchRmMerged(top_dir=Path("/workspace"), git_only=True)
        cmd.run_repo_command()

        error_on_sc_uninitialised.assert_called_once_with()
        get_git_root.assert_called_once()
        rm_merged.assert_called_once_with(git_root, True)

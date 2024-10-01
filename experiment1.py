#!/usr/bin/env python

################################################################################
#
#        experiment1.py - The gittuf NDSS Artifact Evaluation Demo, pt. 1
#
#  This script creates a repository and runs various tests on it, demonstrating
#              gittuf's ability to meet our claims in the paper.
#
################################################################################

import shutil
import os
import tempfile
import click

import utils

REQUIRED_BINARIES = ["git", "gittuf", "ssh-keygen"]

REPOSITORY_STEPS = 3
GITTUF_STEPS = 10
DEMO_STEPS = 2

@click.command()
@click.option(
    "--automatic", default=False, type=bool, help="Whether to wait for input before each command is run."
)
@click.option(
    "--repository-directory", default="repo", help="The path where the script should store the working copy of the repository."
)
def experiment1(automatic, repository_directory):
    """Experiment 1 for NDSS Artifact Evaluation"""

    print("gittuf NDSS Artifact Evaluation - Experiment 1")

    # Repository Setup
    print("[1 / 3] Repository Setup ------------------------------------------")

    step = 1

    # Set up directory structure and keys
    current_dir = os.getcwd()
    keys_dir = "keys"

    # Select folder for the working repository copy
    tmp_dir = tempfile.TemporaryDirectory()
    tmp_keys_dir = os.path.join(tmp_dir.name, keys_dir)
    tmp_repo_dir = os.path.join(tmp_dir.name, "repo")

    shutil.copytree(os.path.join(current_dir, keys_dir), tmp_keys_dir)
    os.mkdir(tmp_repo_dir)
    os.chdir(tmp_repo_dir)

    # Ensure correct permissions for keys
    for key in os.listdir(tmp_keys_dir):
        os.chmod(os.path.join(tmp_keys_dir, key), 0o600)

    # Compute folder paths
    authorized_key_path_git = os.path.join(tmp_keys_dir, "authorized.pub")

    authorized_key_path_policy = os.path.join(tmp_keys_dir, "authorized.pub")

    # Initialize the Git repository in the chosen directory
    step = utils.prompt_key(automatic, step, REPOSITORY_STEPS, "Initialize Git repository")
    cmd = "git init -b main"
    utils.display_command(cmd)
    utils.run_command(cmd, 0)

    # Set the configuration options needed to sign commits. For this demo, the
    # "authorized" key is used, but note that this is not the key used for
    # managing the policy.
    step = utils.prompt_key(automatic, step, REPOSITORY_STEPS, "Set repo config to use demo identity and test key")
    cmd = "git config --local gpg.format ssh"
    utils.display_command(cmd)
    utils.run_command(cmd, 0)
    cmd = "git config --local commit.gpgsign true"
    utils.display_command(cmd)
    utils.run_command(cmd, 0)
    cmd = f"git config --local user.signingkey {authorized_key_path_git}"
    utils.display_command(cmd)
    utils.run_command(cmd, 0)
    cmd = "git config --local user.name gittuf-demo"
    utils.display_command(cmd)
    utils.run_command(cmd, 0)
    cmd = "git config --local user.email gittuf.demo@example.com"
    utils.display_command(cmd)
    utils.run_command(cmd, 0)

    step = utils.prompt_key(automatic, step, REPOSITORY_STEPS, "Set PAGER")
    os.environ["PAGER"] = "cat"
    utils.display_command("export PAGER=cat")

    # gittuf Setup
    print("\n[2 / 3] gittuf Setup ----------------------------------------------")

    step = 1

    step = utils.prompt_key(automatic, step, GITTUF_STEPS, "Initialize gittuf root of trust")
    cmd = "gittuf trust init -k ../keys/root"
    utils.display_command(cmd)
    utils.run_command(cmd, 0)

    step = utils.prompt_key(automatic, step, GITTUF_STEPS, "Trust developer 1's key for the policy")
    cmd = (
        "gittuf trust add-policy-key"
        " -k ../keys/root"
        " --policy-key ../keys/developer1.pub"
    )
    utils.display_command(cmd)
    utils.run_command(cmd, 0)

    step = utils.prompt_key(automatic, step, GITTUF_STEPS, "Trust developer 2's key for the policy")
    cmd = (
        "gittuf trust add-policy-key"
        " -k ../keys/root"
        " --policy-key ../keys/developer2.pub"
    )
    utils.display_command(cmd)
    utils.run_command(cmd, 0)

    step = utils.prompt_key(automatic, step, GITTUF_STEPS, "Set policy threshold to 2 signatures")
    cmd = ("gittuf trust update-policy-threshold -k ../keys/root --threshold 2")
    utils.display_command(cmd)
    utils.run_command(cmd, 0)

    step = utils.prompt_key(automatic, step, GITTUF_STEPS, "Initialize policy with developer 1's key")
    cmd = "gittuf policy init -k ../keys/developer1"
    utils.display_command(cmd)
    utils.run_command(cmd, 0)

    step = utils.prompt_key(automatic, step, GITTUF_STEPS, "Sign policy with developer 2's key")
    cmd = "gittuf policy sign -k ../keys/developer2"
    utils.display_command(cmd)
    utils.run_command(cmd, 0)

    step = utils.prompt_key(automatic, step, GITTUF_STEPS, "Developer 1 adds rule to protect the main branch")
    cmd = (
        "gittuf policy add-rule"
        " -k ../keys/developer1"
        " --rule-name 'protect-main'"
        " --rule-pattern git:refs/heads/main"
        f" --authorize-key {authorized_key_path_policy}"
    )
    utils.display_command(cmd)
    utils.run_command(cmd, 0)

    step = utils.prompt_key(automatic, step, GITTUF_STEPS, "Sign policy with developer 2's key")
    cmd = "gittuf policy sign -k ../keys/developer2"
    utils.display_command(cmd)
    utils.run_command(cmd, 0)

    step = utils.prompt_key(automatic, step, GITTUF_STEPS, "Apply the policy")
    cmd = "gittuf policy apply"
    utils.display_command(cmd)
    utils.run_command(cmd, 0)

    step = utils.prompt_key(automatic, step, GITTUF_STEPS, "Verify branch protection for this change")
    cmd = "gittuf verify-ref refs/gittuf/policy"
    utils.display_command(cmd)
    utils.run_command(cmd, 0)

    # Policy demonstration
    print("\n[3 / 3] gittuf Verification ----------------------------------------------")

    step = 1

    step = utils.prompt_key(automatic, step, DEMO_STEPS, "Developer 1 adds rule to protect the feature branch")
    cmd = (
        "gittuf policy add-rule"
        " -k ../keys/developer1"
        " --rule-name 'protect-feature'"
        " --rule-pattern git:refs/heads/main"
        f" --authorize-key {authorized_key_path_policy}"
    )
    utils.display_command(cmd)
    utils.run_command(cmd, 0)

    step = utils.prompt_key(automatic, step, DEMO_STEPS, "Developer 1 attempts to apply the policy...")
    cmd = "gittuf policy apply"
    utils.display_command(cmd)
    utils.run_command(cmd, 1)

    print("...but is unable to due to both developers needing to approve.")


if __name__ == "__main__":
    utils.check_binaries(REQUIRED_BINARIES)
    experiment1()

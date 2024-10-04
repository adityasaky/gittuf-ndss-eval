#!/usr/bin/env python

################################################################################
#
#        experiment1.py - The gittuf NDSS Artifact Evaluation Demo, pt. 1
#
#            This script demonstrates the policy features of gittuf.
#
################################################################################

import os
import shutil
import tempfile
import click

from utils import prompt_key, display_command, run_command, check_binaries

REQUIRED_BINARIES = ["git", "gittuf", "ssh-keygen"]

REPOSITORY_STEPS = 3
GITTUF_STEPS = 10
DEMO_STEPS = 2

@click.command()
@click.option(
    "--automatic", default=False, type=bool,
    help="Whether to wait for input before each command is run."
)
@click.option(
    "--repository-directory", default="",
    help="The path where the script should store the working copy of the repository."
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
    working_dir = repository_directory
    if working_dir == "":
        tmp_dir =  tempfile.TemporaryDirectory()
        working_dir = tmp_dir.name

    # Set directory variables accordingly
    tmp_keys_dir = os.path.join(working_dir, keys_dir)
    tmp_repo_dir = os.path.join(working_dir, "repo")

    shutil.copytree(os.path.join(current_dir, keys_dir), tmp_keys_dir)
    os.mkdir(tmp_repo_dir)
    os.chdir(tmp_repo_dir)

    # Ensure correct permissions for keys
    for key in os.listdir(tmp_keys_dir):
        os.chmod(os.path.join(tmp_keys_dir, key), 0o600)

    # Compute folder paths
    authorized_key_path_git = os.path.join(tmp_keys_dir, "authorized.pub")
    dev1_key_path_git = os.path.join(tmp_keys_dir, "developer1")
    dev2_key_path_git = os.path.join(tmp_keys_dir, "developer2")

    authorized_key_path_policy = os.path.join(tmp_keys_dir, "authorized.pub")
    dev1_key_path_policy = os.path.join(tmp_keys_dir, "developer1.pub")
    dev2_key_path_policy = os.path.join(tmp_keys_dir, "developer2.pub")

    # Initialize the Git repository in the chosen directory
    step = prompt_key(automatic, step, REPOSITORY_STEPS, "Initialize Git repository")
    cmd = "git init -b main"
    display_command(cmd)
    run_command(cmd, 0)

    # Set the configuration options needed to sign commits. For this demo, the
    # "authorized" key is used, but note that this is not the key used for
    # managing the policy.
    step = prompt_key(automatic, step, REPOSITORY_STEPS,
    "Set repo config to use demo identity and test key")
    cmd = "git config --local gpg.format ssh"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "git config --local commit.gpgsign true"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = f"git config --local user.signingkey {authorized_key_path_git}"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "git config --local user.name gittuf-demo"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "git config --local user.email gittuf.demo@example.com"
    display_command(cmd)
    run_command(cmd, 0)

    step = prompt_key(automatic, step, REPOSITORY_STEPS, "Set PAGER")
    os.environ["PAGER"] = "cat"
    display_command("export PAGER=cat")

    # gittuf Setup
    print("\n[2 / 3] gittuf Setup ----------------------------------------------")

    step = 1

    # Initialize gittuf's root of trust
    step = prompt_key(automatic, step, GITTUF_STEPS,
    "Initialize gittuf root of trust")
    cmd = "gittuf trust init -k ../keys/root"
    display_command(cmd)
    run_command(cmd, 0)

    # Add developer 1's key as trusted for policy
    step = prompt_key(automatic, step, GITTUF_STEPS,
    "Trust developer 1's key for the policy")
    cmd = (
        "gittuf trust add-policy-key"
        " -k ../keys/root"
        f" --policy-key {dev1_key_path_policy}"
    )
    display_command(cmd)
    run_command(cmd, 0)

    # Add developer 2's key as trusted for policy
    step = prompt_key(automatic, step, GITTUF_STEPS,
    "Trust developer 2's key for the policy")
    cmd = (
        "gittuf trust add-policy-key"
        " -k ../keys/root"
        f" --policy-key {dev2_key_path_policy}"
    )
    display_command(cmd)
    run_command(cmd, 0)

    # Set the threshold for policy changes to be 2 (in this case, both
    # developers)
    step = prompt_key(automatic, step, GITTUF_STEPS,
    "Set policy threshold to 2 signatures")
    cmd = "gittuf trust update-policy-threshold -k ../keys/root --threshold 2"
    display_command(cmd)
    run_command(cmd, 0)

    # Initialize the policy (by using developer 1's key)
    step = prompt_key(automatic, step, GITTUF_STEPS,
    "Initialize policy with developer 1's key")
    cmd = "gittuf policy init -k ../keys/developer1"
    display_command(cmd)
    run_command(cmd, 0)

    # Sign the policy with developer 2's key
    # We must do this since we cannot sign a commit with two keys
    step = prompt_key(automatic, step, GITTUF_STEPS,
    "Sign policy with developer 2's key")
    cmd = "gittuf policy sign -k ../keys/developer2"
    display_command(cmd)
    run_command(cmd, 0)

    # Add a rule to protect the main branch (using developer 1's key)
    step = prompt_key(automatic, step, GITTUF_STEPS,
    "Developer 1 adds rule to protect the main branch")
    cmd = (
        "gittuf policy add-rule"
        " -k ../keys/developer1"
        " --rule-name 'protect-main'"
        " --rule-pattern git:refs/heads/main"
        f" --authorize-key {authorized_key_path_policy}"
    )
    display_command(cmd)
    run_command(cmd, 0)

    # Developer 2 approves and signs the policy
    step = prompt_key(automatic, step, GITTUF_STEPS,
    "Sign policy with developer 2's key")
    cmd = "gittuf policy sign -k ../keys/developer2"
    display_command(cmd)
    run_command(cmd, 0)

    # Make the policy live
    step = prompt_key(automatic, step, GITTUF_STEPS, "Apply the policy")
    cmd = "gittuf policy apply"
    display_command(cmd)
    run_command(cmd, 0)

    # Ensure that everything is OK by verifying the state of the repository
    step = prompt_key(automatic, step, GITTUF_STEPS, "Verify policy")
    cmd = "gittuf --verbose verify-ref refs/gittuf/policy"
    display_command(cmd)
    run_command(cmd, 0)

    # Policy demonstration
    print("\n[3 / 3] Policy Violation ----------------------------------------------")

    step = 1

    # Now, simulate a rouge rule add by developer 1
    step = prompt_key(automatic, step, DEMO_STEPS,
    "Developer 1 adds rule to protect the feature branch")
    cmd = (
        "gittuf policy add-rule"
        " -k ../keys/developer1"
        " --rule-name 'protect-feature'"
        " --rule-pattern git:refs/heads/main"
        f" --authorize-key {authorized_key_path_policy}"
    )
    display_command(cmd)
    run_command(cmd, 0)

    # Attempt to apply the new policy
    step = prompt_key(automatic, step, DEMO_STEPS,
    "Developer 1 attempts to apply the policy...")
    cmd = "gittuf --verbose policy apply"
    display_command(cmd)
    run_command(cmd, 1)

    print("...but is unable to due to both developers needing to approve.")


if __name__ == "__main__":
    check_binaries(REQUIRED_BINARIES)
    experiment1() # pylint: disable=no-value-for-parameter

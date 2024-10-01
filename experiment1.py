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
import shlex
import subprocess
import tempfile
import click

NO_PROMPT = False
REQUIRED_BINARIES = ["git", "gittuf", "ssh-keygen"]

REPOSITORY_STEPS = 3
GITTUF_STEPS = 10
DEMO_STEPS = 2

def _check_binaries():
    for p in REQUIRED_BINARIES:
        if not shutil.which(p):
            raise Exception(f"required command {p} not found")

def _prompt_key(opnum, optotal, prompt):
    if NO_PROMPT:
        print(f"\n({opnum} / {optotal}): {prompt}")
        return
    inp = False
    while inp != "":
        try:
            inp = input(f"\n({opnum} / {optotal}): {prompt} -- press any key to continue")
        except Exception:
            pass

def _display_command(cmd):
    print(f"[{os.getcwd()}] $ {cmd}")

def _run_command(cmd, expected_retcode):
    retcode = subprocess.call(shlex.split(cmd))
    if retcode != expected_retcode:
        raise Exception(f"Expected {expected_retcode} from process but it exited with {retcode}.")

@click.command()
@click.option(
    "--automatic", default=False, type=bool, help="Whether to wait for input before each command is run."
)
@click.option(
    "--repository-directory", default="repo", help="The path where the script should store the working copy of the repository."
)
def experiment1(automatic, repository_directory):
    """Experiment 1 for NDSS Artifact Evaluation"""

    if automatic:
        global NO_PROMPT
        NO_PROMPT = True

    # Repository Setup
    print("[1 / 3] Repository Setup ------------------------------------------")

    repository_counter = 1

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
    _prompt_key(1, REPOSITORY_STEPS, "Initialize Git repository")
    cmd = "git init -b main"
    _display_command(cmd)
    _run_command(cmd, 0)

    # Set the configuration options needed to sign commits. For this demo, the
    # "authorized" key is used, but note that this is not the key used for
    # managing the policy.
    _prompt_key(2, REPOSITORY_STEPS, "Set repo config to use demo identity and test key")
    cmd = "git config --local gpg.format ssh"
    _display_command(cmd)
    _run_command(cmd, 0)
    cmd = "git config --local commit.gpgsign true"
    _display_command(cmd)
    _run_command(cmd, 0)
    cmd = f"git config --local user.signingkey {authorized_key_path_git}"
    _display_command(cmd)
    _run_command(cmd, 0)
    cmd = "git config --local user.name gittuf-demo"
    _display_command(cmd)
    _run_command(cmd, 0)
    cmd = "git config --local user.email gittuf.demo@example.com"
    _display_command(cmd)
    _run_command(cmd, 0)

    _prompt_key(3, REPOSITORY_STEPS, "Set PAGER")
    os.environ["PAGER"] = "cat"
    _display_command("export PAGER=cat")

    # gittuf Setup
    print("\n[2 / 3] gittuf Setup ----------------------------------------------")

    _prompt_key(1, GITTUF_STEPS, "Initialize gittuf root of trust")
    cmd = "gittuf trust init -k ../keys/root"
    _display_command(cmd)
    _run_command(cmd, 0)

    _prompt_key(2, GITTUF_STEPS, "Trust developer 1's key for the policy")
    cmd = (
        "gittuf trust add-policy-key"
        " -k ../keys/root"
        " --policy-key ../keys/developer1.pub"
    )
    _display_command(cmd)
    _run_command(cmd, 0)

    _prompt_key(3, GITTUF_STEPS, "Trust developer 2's key for the policy")
    cmd = (
        "gittuf trust add-policy-key"
        " -k ../keys/root"
        " --policy-key ../keys/developer2.pub"
    )
    _display_command(cmd)
    _run_command(cmd, 0)

    _prompt_key(4, GITTUF_STEPS, "Set policy threshold to 2 signatures")
    cmd = ("gittuf trust update-policy-threshold -k ../keys/root --threshold 2")
    _display_command(cmd)
    _run_command(cmd, 0)

    _prompt_key(5, GITTUF_STEPS, "Initialize policy with developer 1's key")
    cmd = "gittuf policy init -k ../keys/developer1"
    _display_command(cmd)
    _run_command(cmd, 0)

    _prompt_key(6, GITTUF_STEPS, "Sign policy with developer 2's key")
    cmd = "gittuf policy sign -k ../keys/developer2"
    _display_command(cmd)
    _run_command(cmd, 0)

    _prompt_key(7, GITTUF_STEPS, "Developer 1 adds rule to protect the main branch")
    cmd = (
        "gittuf policy add-rule"
        " -k ../keys/developer1"
        " --rule-name 'protect-main'"
        " --rule-pattern git:refs/heads/main"
        f" --authorize-key {authorized_key_path_policy}"
    )
    _display_command(cmd)
    _run_command(cmd, 0)

    _prompt_key(8, GITTUF_STEPS, "Sign policy with developer 2's key")
    cmd = "gittuf policy sign -k ../keys/developer2"
    _display_command(cmd)
    _run_command(cmd, 0)

    _prompt_key(9, GITTUF_STEPS, "Apply the policy")
    cmd = "gittuf policy apply"
    _display_command(cmd)
    _run_command(cmd, 0)

    _prompt_key(10, GITTUF_STEPS, "Verify branch protection for this change")
    cmd = "gittuf verify-ref refs/gittuf/policy"
    _display_command(cmd)
    _run_command(cmd, 0)

    # Policy demonstration
    print("\n[3 / 3] gittuf Verification ----------------------------------------------")

    _prompt_key(1, DEMO_STEPS, "Developer 1 adds rule to protect the feature branch")
    cmd = (
        "gittuf policy add-rule"
        " -k ../keys/developer1"
        " --rule-name 'protect-feature'"
        " --rule-pattern git:refs/heads/main"
        f" --authorize-key {authorized_key_path_policy}"
    )
    _display_command(cmd)
    _run_command(cmd, 0)

    _prompt_key(2, DEMO_STEPS, "Developer 1 attempts to apply the policy...")
    cmd = "gittuf policy apply"
    _display_command(cmd)
    _run_command(cmd, 1)

    print("...but is unable to due to both developers needing to approve.")


if __name__ == "__main__":
    _check_binaries()
    experiment1()

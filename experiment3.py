#!/usr/bin/env python

################################################################################
#
#        experiment3.py - The gittuf NDSS Artifact Evaluation Demo, pt. 3
#
#  This script creates a repository and runs various tests on it, demonstrating
#              gittuf's ability to meet our claims in the paper.
#
################################################################################

import os
import shutil
import tempfile
import click

from utils import prompt_key, display_command, run_command, check_binaries

REQUIRED_BINARIES = ["git", "gittuf", "ssh-keygen"]

REPOSITORY_STEPS = 3
GITTUF_STEPS = 8
DEMO_STEPS = 4

@click.command()
@click.option(
    "--automatic", default=False, type=bool, help="Whether to wait for input before each command is run."
)
@click.option(
    "--repository-directory", default="repo", help="The path where the script should store the working copy of the repository."
)
def experiment3(automatic, repository_directory):
    """Experiment 3 for NDSS Artifact Evaluation"""

    print("gittuf NDSS Artifact Evaluation - Experiment 3")

    # Repository Setup
    print("[1 / 3] Repository Setup ------------------------------------------")

    step = 1

    # Set up directory structure and keys
    current_dir = os.getcwd()
    keys_dir = "keys"

    # Select f# pylint: disable=no-value-for-parameterolder for the working repository copy
    tmp_dir = tempfile.TemporaryDirectory()
    tmp_keys_dir = os.path.join(tmp_dir.name, keys_dir)

    # Repo A is the "origin" repo for Repo B
    tmp_repo_a_dir = os.path.join(tmp_dir.name, "repo_a")
    tmp_repo_b_dir = os.path.join(tmp_dir.name, "repo_b")

    shutil.copytree(os.path.join(current_dir, keys_dir), tmp_keys_dir)
    os.mkdir(tmp_repo_a_dir)
    # os.mkdir(tmp_repo_b_dir)
    os.chdir(tmp_repo_a_dir)

    # Ensure correct permissions for keys
    for key in os.listdir(tmp_keys_dir):
        os.chmod(os.path.join(tmp_keys_dir, key), 0o600)

    # Compute folder paths
    authorized_key_path_git = os.path.join(tmp_keys_dir, "authorized.pub")

    authorized_key_path_policy = os.path.join(tmp_keys_dir, "authorized.pub")

    # Initialize the Git repository in the chosen directory
    step = prompt_key(automatic, step, REPOSITORY_STEPS, "Initialize Git repository")
    cmd = "git init -b main"
    display_command(cmd)
    run_command(cmd, 0)

    # Set the configuration options needed to sign commits. For this demo, the
    # "authorized" key is used, but note that this is not the key used for
    # managing the policy.
    step = prompt_key(automatic, step, REPOSITORY_STEPS, "Set repo config to use demo identity and test key")
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

    step = prompt_key(automatic, step, GITTUF_STEPS, "Initialize gittuf root of trust")
    cmd = "gittuf trust init -k ../keys/root"
    display_command(cmd)
    run_command(cmd, 0)

    step = prompt_key(automatic, step, GITTUF_STEPS, "Add policy key to gittuf root of trust")
    cmd = (
        "gittuf trust add-policy-key"
        " -k ../keys/root"
        " --policy-key ../keys/targets.pub"
    )
    display_command(cmd)
    run_command(cmd, 0)

    step = prompt_key(automatic, step, GITTUF_STEPS, "Initialize policy")
    cmd = "gittuf policy init -k ../keys/targets"
    display_command(cmd)
    run_command(cmd, 0)

    step = prompt_key(automatic, step, GITTUF_STEPS, "Add a rule to protect the main branch")
    cmd = (
        "gittuf policy add-rule"
        " -k ../keys/targets"
        " --rule-name 'protect-main'"
        " --rule-pattern git:refs/heads/main"
        f" --authorize-key {authorized_key_path_policy}"
    )
    display_command(cmd)
    run_command(cmd, 0)

    step = prompt_key(automatic, step, GITTUF_STEPS, "Apply the policy")
    cmd = "gittuf policy apply"
    display_command(cmd)
    run_command(cmd, 0)

    step = prompt_key(automatic, step, GITTUF_STEPS, "Make change to repo's main branch")
    display_command("echo 'Hello, world!' > README.md")
    with open("README.md", "w") as fp:
        fp.write("Hello, world!\n")
    cmd = "git add README.md"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "git commit -m 'Initial commit'"
    display_command(cmd)
    run_command(cmd, 0)

    step = prompt_key(automatic, step, GITTUF_STEPS, "Record change to main in RSL")
    cmd = "gittuf rsl record main"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "git show refs/gittuf/reference-state-log"
    display_command(cmd)
    run_command(cmd, 0)

    step = prompt_key(automatic, step, GITTUF_STEPS, "Verify branch protection for this change")
    cmd = "gittuf verify-ref main"
    display_command(cmd)
    run_command(cmd, 0)


    # RSL Manipulation
    print("\n[3 / 3] RSL Manipulation ----------------------------------------------")

    step = 1

    step = prompt_key(automatic, step, DEMO_STEPS, "Another user clones the git repository")
    cmd = f"cd {tmp_dir.name}"
    display_command(cmd)
    os.chdir(tmp_dir.name)
    cmd = f"gittuf clone {tmp_repo_a_dir} repo_b"
    display_command(cmd)
    run_command(cmd, 0)


    cmd = f"cd {tmp_repo_a_dir}"
    display_command(cmd)
    os.chdir(tmp_repo_a_dir)

    step = prompt_key(automatic, step, DEMO_STEPS, "The original repository owner rolls back the RSL and rewrites history")
    cmd = "git commit --amend -m 'Evil commit message'"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "git update-ref refs/gittuf/reference-state-log refs/gittuf/reference-state-log~1"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "gittuf rsl record"

    # step = prompt_key(automatic, step, DEMO_STEPS, "Make evil change to repo's main branch with an authorized key")
    # display_command("echo 'Hello, WORLD!' > README.md")
    # with open("README.md", "w") as fp:
    #     fp.write("Hello, WORLD!\n")
    # cmd = "git add README.md"
    # display_command(cmd)
    # run_command(cmd, 0)
    # cmd = "git commit -m 'Initial commit'"
    # display_command(cmd)
    # run_command(cmd, 0)

    step = prompt_key(automatic, step, DEMO_STEPS, "The other user attempts to fetch changes, but is warned that a branch has changed")
    cmd = "cd repo_b"
    display_command(cmd)
    os.chdir(tmp_repo_b_dir)
    cmd = "git pull"
    display_command(cmd)
    run_command(cmd, 128)
    cmd = "git reset --hard @{upstream}"
    display_command(cmd)
    run_command(cmd, 0)

    step = prompt_key(automatic, step, DEMO_STEPS, "Now, the user attemps to pull the RSL, and is also warned that something is amiss")
    cmd = "gittuf rsl remote pull origin"
    display_command(cmd)
    run_command(cmd, 1)

    print("... but is warned that something has happened.")

if __name__ == "__main__":
    check_binaries(REQUIRED_BINARIES)
    experiment3() # pylint: disable=no-value-for-parameter

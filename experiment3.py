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
GITTUF_STEPS = 5
DEMO_STEPS = 14

@click.command()
@click.option(
    "--automatic", default=False, type=bool,
    help="Whether to wait for input before each command is run."
)
@click.option(
    "--repository-directory", default="",
    help="The path where the script should store the working copy of the repository."
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

    # Select folder for the working repository copy
    working_dir = repository_directory
    if working_dir == "":
        tmp_dir =  tempfile.TemporaryDirectory()
        working_dir = tmp_dir.name

    tmp_keys_dir = os.path.join(working_dir, keys_dir)

    # "repo_server" is the remote repo for "repo_a" and "repo_b"
    tmp_repo_server_dir = os.path.join(working_dir, "repo_server")
    tmp_repo_a_dir = os.path.join(working_dir, "repo_a")
    tmp_repo_b_dir = os.path.join(working_dir, "repo_b")

    shutil.copytree(os.path.join(current_dir, keys_dir), tmp_keys_dir)
    os.mkdir(tmp_repo_server_dir)
    os.chdir(tmp_repo_server_dir)

    # Ensure correct permissions for keys
    for key in os.listdir(tmp_keys_dir):
        os.chmod(os.path.join(tmp_keys_dir, key), 0o600)

    # Compute folder paths
    authorized_key_path_git = os.path.join(tmp_keys_dir, "authorized")
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
    cmd = "git config --local user.name gittuf-demo authorized-user"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "git config --local user.email gittuf.demo@example.com"
    display_command(cmd)
    run_command(cmd, 0)

    cmd = "git config receive.denyCurrentBranch ignore"
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
        f" --authorize-key {dev1_key_path_policy}"
        f" --authorize-key {dev2_key_path_policy}"
    )
    display_command(cmd)
    run_command(cmd, 0)

    step = prompt_key(automatic, step, GITTUF_STEPS, "Apply the policy")
    cmd = "gittuf policy apply"
    display_command(cmd)
    run_command(cmd, 0)

    # RSL Demonstration
    print("\n[3 / 3] RSL Demonstration ----------------------------------------------")

    step = 1

    step = prompt_key(automatic, step, DEMO_STEPS, "Make change to repo's main branch")
    display_command("echo 'Hello, world!' > README.md")
    with open("README.md", "w", encoding="utf-8") as fp:
        fp.write("Hello, world!\n")
    cmd = "git add README.md"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "git commit -m 'Initial commit'"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "gittuf rsl record main"
    display_command(cmd)
    run_command(cmd, 0)

    step = prompt_key(automatic, step, DEMO_STEPS, "User A clones the git repository")
    cmd = f"cd {working_dir}"
    display_command(cmd)
    os.chdir(working_dir)
    cmd = f"gittuf clone {tmp_repo_server_dir} repo_a"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = f"cd {tmp_repo_a_dir}"
    display_command(cmd)
    os.chdir(tmp_repo_a_dir)

    step = prompt_key(automatic, step, DEMO_STEPS,
    "Set repo config to use dev1 identity and test key")
    cmd = "git config --local gpg.format ssh"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "git config --local commit.gpgsign true"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = f"git config --local user.signingkey {dev1_key_path_git}"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "git config --local user.name gittuf-demo"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "git config --local user.email gittuf.demo@example.com"
    display_command(cmd)
    run_command(cmd, 0)

    step = prompt_key(automatic, step, DEMO_STEPS, "Make change to repo's main branch")
    display_command("echo 'Hello, new world!' > README.md")
    with open("README.md", "w", encoding="utf-8") as fp:
        fp.write("Hello, new world!\n")
    cmd = "git add README.md"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "git commit -m 'Another commit'"
    display_command(cmd)
    run_command(cmd, 0)

    step = prompt_key(automatic, step, DEMO_STEPS, "Record change to main in RSL")
    cmd = "gittuf rsl record main"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "git show refs/gittuf/reference-state-log"
    display_command(cmd)
    run_command(cmd, 0)

    step = prompt_key(automatic, step, DEMO_STEPS, "Verify branch protection for this change")
    cmd = "gittuf --verbose verify-ref main"
    display_command(cmd)
    run_command(cmd, 0)

    step = prompt_key(automatic, step, DEMO_STEPS, "User A pushes changes to the remote")
    cmd = "git push"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "gittuf rsl remote push origin"
    display_command(cmd)
    run_command(cmd, 0)

    step = prompt_key(automatic, step, DEMO_STEPS, "Server drops the latest push")
    cmd = f"cd {tmp_repo_server_dir}"
    display_command(cmd)
    os.chdir(tmp_repo_server_dir)
    cmd = "git reset --hard HEAD~1"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "git update-ref refs/gittuf/reference-state-log refs/gittuf/reference-state-log~1"
    display_command(cmd)
    run_command(cmd, 0)

    step = prompt_key(automatic, step, DEMO_STEPS, "User B clones the git repository")
    cmd = f"cd {working_dir}"
    display_command(cmd)
    os.chdir(working_dir)
    cmd = f"gittuf clone {tmp_repo_server_dir} repo_b"
    display_command(cmd)
    run_command(cmd, 0)

    cmd = f"cd {tmp_repo_b_dir}"
    display_command(cmd)
    os.chdir(tmp_repo_b_dir)

    step = prompt_key(automatic, step, DEMO_STEPS,
    "Set repo config to use dev2 identity and test key")
    cmd = "git config --local gpg.format ssh"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "git config --local commit.gpgsign true"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = f"git config --local user.signingkey {dev2_key_path_git}"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "git config --local user.name gittuf-demo"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "git config --local user.email gittuf.demo@example.com"
    display_command(cmd)
    run_command(cmd, 0)

    step = prompt_key(automatic, step, DEMO_STEPS, "Make change to repo's main branch")
    display_command("echo 'Hello, newer world!' > README.md")
    with open("README.md", "w", encoding="utf-8") as fp:
        fp.write("Hello, newer world!\n")
    cmd = "git add README.md"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "git commit -m 'Yet another commit'"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "gittuf rsl record main"
    display_command(cmd)
    run_command(cmd, 0)

    step = prompt_key(automatic, step, DEMO_STEPS, "Verify branch protection for this change")
    cmd = "gittuf --verbose verify-ref main"
    display_command(cmd)
    run_command(cmd, 0)

    step = prompt_key(automatic, step, DEMO_STEPS, "User B pushes changes to the remote")
    cmd = "git push"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "gittuf rsl remote push origin"
    display_command(cmd)
    run_command(cmd, 0)

    step = prompt_key(automatic, step, DEMO_STEPS, "User A attempts to pull the latest changes...")
    cmd = f"cd {tmp_repo_a_dir}"
    display_command(cmd)
    os.chdir(tmp_repo_a_dir)
    cmd = "git pull"
    display_command(cmd)
    run_command(cmd, 128)

    print("... but is warned that something has happened.")

if __name__ == "__main__":
    check_binaries(REQUIRED_BINARIES)
    experiment3() # pylint: disable=no-value-for-parameter

# ---- Cut here when ready to clean up ----
    # step = prompt_key(automatic, step, DEMO_STEPS, "The original repository owner rolls back the RSL and rewrites history")
    # cmd = "git commit --amend -m 'Evil commit message'"
    # display_command(cmd)
    # run_command(cmd, 0)
    # cmd = "git update-ref refs/gittuf/reference-state-log refs/gittuf/reference-state-log~1"
    # display_command(cmd)
    # run_command(cmd, 0)
    # cmd = "gittuf rsl record"

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

    # step = prompt_key(automatic, step, DEMO_STEPS, "The other user attempts to fetch changes, but is warned that a branch has changed")
    # cmd = "cd repo_b"
    # display_command(cmd)
    # os.chdir(tmp_repo_b_dir)
    # cmd = "git pull"
    # display_command(cmd)
    # run_command(cmd, 128)
    # cmd = "git reset --hard @{upstream}"
    # display_command(cmd)
    # run_command(cmd, 0)

    # step = prompt_key(automatic, step, DEMO_STEPS, "Now, the user attempts to pull the RSL, and is also warned that something is amiss")
    # cmd = "gittuf rsl remote pull origin"
    # display_command(cmd)
    # run_command(cmd, 1)

    # cmd = "gittuf rsl remote pull origin"
    # display_command(cmd)
    # run_command(cmd, 0)

    # cmd = "gittuf --verbose verify-ref main"
    # display_command(cmd)
    # run_command(cmd, 0)

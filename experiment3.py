#!/usr/bin/env python

################################################################################
#
#        experiment3.py - The gittuf NDSS Artifact Evaluation Demo, pt. 3
#
#                 This script demonstrates the RSL of gittuf.
#
################################################################################

import os
import shutil
import tempfile
import click

from utils import prompt_key, display_command, run_command, check_binaries, print_section

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
    print_section("[1 / 3] Repository Setup")

    step = 1

    # Set up directory structure and keys
    current_dir = os.getcwd()
    keys_dir = "keys"

    # Select folder for the working repository copy
    working_dir = repository_directory
    if working_dir == "":
        tmp_dir =  tempfile.TemporaryDirectory()
        working_dir = tmp_dir.name
    else:
        working_dir = os.path.abspath(repository_directory)

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
    root_private_key_path = os.path.join(tmp_keys_dir, "root")
    authorized_private_key_path = os.path.join(tmp_keys_dir, "authorized")
    dev1_private_key_path = os.path.join(tmp_keys_dir, "developer1")
    dev2_private_key_path = os.path.join(tmp_keys_dir, "developer2")

    authorized_public_key_path = os.path.join(tmp_keys_dir, "authorized.pub")
    targets_public_key_path = os.path.join(tmp_keys_dir, "targets.pub")
    dev1_public_key_path = os.path.join(tmp_keys_dir, "developer1.pub")
    dev2_public_key_path = os.path.join(tmp_keys_dir, "developer2.pub")

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
    cmd = f"git config --local user.signingkey {authorized_private_key_path}"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "git config --local user.name gittuf-demo authorized-user"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "git config --local user.email gittuf.demo@example.com"
    display_command(cmd)
    run_command(cmd, 0)

    # Enable pushing to this repo as a remote
    cmd = "git config receive.denyCurrentBranch ignore"
    display_command(cmd)
    run_command(cmd, 0)

    step = prompt_key(automatic, step, REPOSITORY_STEPS, "Set PAGER")
    os.environ["PAGER"] = "cat"
    display_command("export PAGER=cat")

    # gittuf Setup
    print_section("[2 / 3] gittuf Setup")

    step = 1

    # Initialize gittuf's root of trust
    step = prompt_key(automatic, step, GITTUF_STEPS, "Initialize gittuf root of trust")
    cmd = "gittuf trust init -k ../keys/root"
    display_command(cmd)
    run_command(cmd, 0)

    # Add the targets key as trusted for policy
    step = prompt_key(automatic, step, GITTUF_STEPS, "Add policy key to gittuf root of trust")
    cmd = (
        "gittuf trust add-policy-key"
        f" -k {root_private_key_path}"
        f" --policy-key {targets_public_key_path}"
    )
    display_command(cmd)
    run_command(cmd, 0)

    # Initialize the policy
    step = prompt_key(automatic, step, GITTUF_STEPS, "Initialize policy")
    cmd = "gittuf policy init -k ../keys/targets"
    display_command(cmd)
    run_command(cmd, 0)

    # Add a rule authorizing developers 1 and 2 as well as the authorized key to
    # modify main
    step = prompt_key(automatic, step, GITTUF_STEPS, "Add a rule to protect the main branch")
    cmd = (
        "gittuf policy add-rule"
        " -k ../keys/targets"
        " --rule-name 'protect-main'"
        " --rule-pattern git:refs/heads/main"
        f" --authorize-key {authorized_public_key_path}"
        f" --authorize-key {dev1_public_key_path}"
        f" --authorize-key {dev2_public_key_path}"
    )
    display_command(cmd)
    run_command(cmd, 0)

    # Apply gittuf policy
    step = prompt_key(automatic, step, GITTUF_STEPS, "Apply the policy")
    cmd = "gittuf policy apply"
    display_command(cmd)
    run_command(cmd, 0)

    # RSL Demonstration
    print_section("[3 / 3] RSL Demonstration")

    step = 1

    # Simulate the owner making a change to the main branch
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

    # Developer 1 clones repo
    step = prompt_key(automatic, step, DEMO_STEPS, "Developer 1 clones the git repository")
    cmd = f"cd {working_dir}"
    display_command(cmd)
    os.chdir(working_dir)
    cmd = f"gittuf clone {tmp_repo_server_dir} repo_a"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = f"cd {tmp_repo_a_dir}"
    display_command(cmd)
    os.chdir(tmp_repo_a_dir)

    # Setup git configuration for developer 1
    step = prompt_key(automatic, step, DEMO_STEPS,
    "Set repo config to use developer 1 identity and test key")
    cmd = "git config --local gpg.format ssh"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "git config --local commit.gpgsign true"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = f"git config --local user.signingkey {dev1_private_key_path}"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "git config --local user.name gittuf-demo"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "git config --local user.email gittuf.demo@example.com"
    display_command(cmd)
    run_command(cmd, 0)

    # Make change to main branch as developer 1
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

    # Ensure changes follow policy
    step = prompt_key(automatic, step, DEMO_STEPS, "Verify branch protection for this change")
    cmd = "gittuf --verbose verify-ref main"
    display_command(cmd)
    run_command(cmd, 0)

    step = prompt_key(automatic, step, DEMO_STEPS, "Developer 1 pushes changes to the remote")
    cmd = "git push"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "gittuf rsl remote push origin"
    display_command(cmd)
    run_command(cmd, 0)

    # Simulate the server dropping the latest push
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

    # Developer 2 now clones the repository, unaware as to what has happened
    step = prompt_key(automatic, step, DEMO_STEPS, "Developer 2 clones the git repository")
    cmd = f"cd {working_dir}"
    display_command(cmd)
    os.chdir(working_dir)
    cmd = f"gittuf clone {tmp_repo_server_dir} repo_b"
    display_command(cmd)
    run_command(cmd, 0)

    cmd = f"cd {tmp_repo_b_dir}"
    display_command(cmd)
    os.chdir(tmp_repo_b_dir)

    # Setup Git configuration for developer 2
    step = prompt_key(automatic, step, DEMO_STEPS,
    "Set repo config to use developer 2 identity and test key")
    cmd = "git config --local gpg.format ssh"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "git config --local commit.gpgsign true"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = f"git config --local user.signingkey {dev2_private_key_path}"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "git config --local user.name gittuf-demo"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "git config --local user.email gittuf.demo@example.com"
    display_command(cmd)
    run_command(cmd, 0)

    # Developer 2 makes a change to the main branch
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

    # Developer 2 checks the changes against policy
    # Verification will succeed here
    step = prompt_key(automatic, step, DEMO_STEPS, "Verify branch protection for this change")
    cmd = "gittuf --verbose verify-ref main"
    display_command(cmd)
    run_command(cmd, 0)

    # Send the changes back to the remote
    step = prompt_key(automatic, step, DEMO_STEPS, "Developer 2 pushes changes to the remote")
    cmd = "git push"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "gittuf rsl remote push origin"
    display_command(cmd)
    run_command(cmd, 0)

    # Developer 1 attempts to sync their repository with the remote
    step = prompt_key(automatic, step, DEMO_STEPS,
    "Developer 1 attempts to pull the latest changes...")
    cmd = f"cd {tmp_repo_a_dir}"
    display_command(cmd)
    os.chdir(tmp_repo_a_dir)
    cmd = "gittuf rsl remote pull origin"
    display_command(cmd)
    run_command(cmd, 1)

    print("\n... but is warned by gittuf that the RSL has diverged!")

if __name__ == "__main__":
    check_binaries(REQUIRED_BINARIES)
    experiment3() # pylint: disable=no-value-for-parameter

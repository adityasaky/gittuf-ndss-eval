#!/usr/bin/env python

################################################################################
#
#        experiment1.py - The gittuf NDSS Artifact Evaluation Demo, pt. 4
#
#      This script demonstrates the policy verification features of gittuf.
#
################################################################################

import os
import shutil
import tempfile
import click

from utils import prompt_key, display_command, run_command, check_binaries, print_section

REQUIRED_BINARIES = ["git", "gittuf", "ssh-keygen"]

REPOSITORY_STEPS = 3
GITTUF_STEPS = 7
DEMO_STEPS = 9

@click.command()
@click.option(
    "--automatic", default=False, type=bool,
    help="Whether to wait for input before each command is run."
)
@click.option(
    "--repository-directory", default="",
    help="The path where the script should store the working copy of the repository."
)
def experiment4(automatic, repository_directory):
    """Experiment 4 for NDSS Artifact Evaluation"""

    print("gittuf NDSS Artifact Evaluation - Experiment 4")

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
    tmp_repo_dir = os.path.join(working_dir, "repo")

    shutil.copytree(os.path.join(current_dir, keys_dir), tmp_keys_dir)

    # Repo A is the "origin" repo for Repo B
    tmp_repo_a_dir = os.path.join(working_dir, "repo_a")
    tmp_repo_b_dir = os.path.join(working_dir, "repo_b")

    os.mkdir(tmp_repo_a_dir)
    os.chdir(tmp_repo_a_dir)

    # Ensure correct permissions for keys
    for key in os.listdir(tmp_keys_dir):
        os.chmod(os.path.join(tmp_keys_dir, key), 0o600)

    # Compute folder paths
    root_private_key_path = os.path.join(tmp_keys_dir, "root")
    targets_private_key_path = os.path.join(tmp_keys_dir, "targets")
    unauthorized_private_key_path = os.path.join(tmp_keys_dir, "unauthorized")
    dev1_private_key_path = os.path.join(tmp_keys_dir, "developer1")

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
    step = prompt_key(automatic, step, REPOSITORY_STEPS, "Set repo config to use demo identity and test key")
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

    step = prompt_key(automatic, step, REPOSITORY_STEPS, "Set PAGER")
    os.environ["PAGER"] = "cat"
    display_command("export PAGER=cat")

    # gittuf Setup
    print_section("[2 / 3] gittuf Setup")

    step = 1

    step = prompt_key(automatic, step, GITTUF_STEPS, "Initialize gittuf root of trust")
    cmd = f"gittuf trust init -k {root_private_key_path}"
    display_command(cmd)
    run_command(cmd, 0)

    step = prompt_key(automatic, step, GITTUF_STEPS, "Add policy key to gittuf root of trust")
    cmd = (
        "gittuf trust add-policy-key"
        f" -k {root_private_key_path}"
        f" --policy-key {targets_public_key_path}"
    )
    display_command(cmd)
    run_command(cmd, 0)

    step = prompt_key(automatic, step, GITTUF_STEPS, "Initialize policy")
    cmd = f"gittuf policy init -k {targets_private_key_path}"
    display_command(cmd)
    run_command(cmd, 0)

    step = prompt_key(automatic, step, GITTUF_STEPS, "Add a rule to protect the main branch")
    cmd = (
        "gittuf policy add-rule"
        f" -k {targets_private_key_path}"
        " --rule-name 'protect-main'"
        " --rule-pattern git:refs/heads/main"
        f" --authorize-key {dev1_public_key_path}"
    )
    display_command(cmd)
    run_command(cmd, 0)

    step = prompt_key(automatic, step, GITTUF_STEPS, "Add a rule to protect the feature branch")
    cmd = (
        "gittuf policy add-rule"
        f" -k {targets_private_key_path}"
        " --rule-name 'protect-feature'"
        " --rule-pattern git:refs/heads/feature"
        f" --authorize-key {dev2_public_key_path}"
    )
    display_command(cmd)
    run_command(cmd, 0)

    step = prompt_key(automatic, step, GITTUF_STEPS, "Apply the policy")
    cmd = "gittuf policy apply"
    display_command(cmd)
    run_command(cmd, 0)

    # Ensure that everything is OK by verifying the state of the repository
    step = prompt_key(automatic, step, GITTUF_STEPS, "Verify policy")
    cmd = "gittuf --verbose verify-ref refs/gittuf/policy"
    display_command(cmd)
    run_command(cmd, 0)

    # RSL Manipulation
    print_section("[3 / 3] Write Rule Violations")

    step = 1

    step = prompt_key(automatic, step, DEMO_STEPS, "Make authorized change to repo's main branch")
    display_command("echo 'Hello, world!' > README.md")
    with open("README.md", "w", encoding="utf-8") as fp:
        fp.write("Hello, world!\n")
    cmd = "git add README.md"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "git commit -m 'Initial commit'"
    display_command(cmd)
    run_command(cmd, 0)

    step = prompt_key(automatic, step, DEMO_STEPS, "Record change to main in RSL")
    cmd = "gittuf rsl record main"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "git show refs/gittuf/reference-state-log"
    display_command(cmd)
    run_command(cmd, 0)

    step = prompt_key(automatic, step, DEMO_STEPS, "Update repo config to use unauthorized key")
    cmd = f"git config --local user.signingkey {unauthorized_private_key_path}"
    display_command(cmd)
    run_command(cmd, 0)

    step = prompt_key(automatic, step, DEMO_STEPS, "Another user clones the git repository")
    cmd = f"cd {working_dir}"
    display_command(cmd)
    os.chdir(working_dir)
    cmd = f"gittuf clone {tmp_repo_a_dir} repo_b"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "cd repo_b"
    display_command(cmd)
    os.chdir(tmp_repo_b_dir)

    step = prompt_key(automatic, step, GITTUF_STEPS, "Verify the state of the repository")
    cmd = "gittuf --verbose verify-ref main"
    display_command(cmd)
    run_command(cmd, 0)

    step = prompt_key(automatic, step, DEMO_STEPS, "Make unauthorized change to original repo's main branch")
    cmd = "cd repo_a"
    display_command(cmd)
    os.chdir("../repo_a")
    display_command("echo 'Evil change!' > README.md")
    with open("README.md", "w", encoding="utf-8") as fp:
        fp.write("Evil change!\n")
    cmd = "git add README.md"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "git commit -m 'Totally not an evil change'"
    display_command(cmd)
    run_command(cmd, 0)

    step = prompt_key(automatic, step, DEMO_STEPS, "Record change to main in RSL")
    cmd = "gittuf rsl record main"
    display_command(cmd)
    run_command(cmd, 0)

    cmd = f"cd {tmp_repo_a_dir}"
    display_command(cmd)
    os.chdir(tmp_repo_a_dir)

    step = prompt_key(automatic, step, DEMO_STEPS, "The other user fetches changes")
    cmd = "cd repo_b"
    display_command(cmd)
    os.chdir(tmp_repo_b_dir)
    cmd = "git pull"
    display_command(cmd)
    run_command(cmd, 0)

    step = prompt_key(automatic, step, DEMO_STEPS, "Now, the user pulls the RSL from the remote repository")
    cmd = "gittuf rsl remote pull origin"
    display_command(cmd)
    run_command(cmd, 0)

    step = prompt_key(automatic, step, DEMO_STEPS, "Finally, the user attempts to verify the state of the repository...")
    cmd = "gittuf --verbose verify-ref main"
    display_command(cmd)
    run_command(cmd, 1)

    print("\n... but is warned by gittuf that there's a policy violation!")

if __name__ == "__main__":
    check_binaries(REQUIRED_BINARIES)
    experiment4() # pylint: disable=no-value-for-parameter

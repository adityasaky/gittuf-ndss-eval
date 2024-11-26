#!/usr/bin/env python

################################################################################
#
#        experiment2.py - The gittuf NDSS Artifact Evaluation Demo, pt. 2
#
#          This script demonstrates the delegation features of gittuf.
#
################################################################################

import os
import shutil
import tempfile
import click

from utils import prompt_key, display_command, run_command, check_binaries, print_section

REQUIRED_BINARIES = ["git", "gittuf", "ssh-keygen"]

REPOSITORY_STEPS = 3
GITTUF_STEPS = 9
DEMO_STEPS = 4

@click.command()
@click.option(
    "--automatic", default=False, type=bool, is_flag=True,
    help="Whether to wait for input before each command is run."
)
@click.option(
    "--repository-directory", default="",
    help="The path where the script should store the working copy of the repository."
)
def experiment2(automatic, repository_directory):
    """Experiment 2 for NDSS Artifact Evaluation"""

    print("gittuf NDSS Artifact Evaluation - Experiment 2")

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
    os.mkdir(tmp_repo_dir)
    os.chdir(tmp_repo_dir)

    # Ensure correct permissions for keys
    for key in os.listdir(tmp_keys_dir):
        os.chmod(os.path.join(tmp_keys_dir, key), 0o600)

    # Compute folder paths
    root_private_key_path = os.path.join(tmp_keys_dir, "root")
    authorized_private_key_path = os.path.join(tmp_keys_dir, "authorized")
    targets_private_key_path = os.path.join(tmp_keys_dir, "targets")
    dev1_private_key_path = os.path.join(tmp_keys_dir, "developer1")
    dev2_private_key_path = os.path.join(tmp_keys_dir, "developer2")
    dev3_private_key_path = os.path.join(tmp_keys_dir, "developer3")

    targets_public_key_path = os.path.join(tmp_keys_dir, "targets.pub")
    dev1_public_key_path = os.path.join(tmp_keys_dir, "developer1.pub")
    dev2_public_key_path = os.path.join(tmp_keys_dir, "developer2.pub")
    dev3_public_key_path = os.path.join(tmp_keys_dir, "developer3.pub")

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

    # Initialize gittuf's root of trust
    step = prompt_key(automatic, step, GITTUF_STEPS, "Initialize gittuf root of trust")
    cmd = f"gittuf trust init -k {root_private_key_path}"
    display_command(cmd)
    run_command(cmd, 0)

    # Add developer 1's key as trusted for policy
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
    cmd = f"gittuf policy init -k {targets_private_key_path}"
    display_command(cmd)
    run_command(cmd, 0)

    # Add a rule authorizing developer 1 to modify the main branch
    step = prompt_key(automatic, step, GITTUF_STEPS, "Add a rule to protect the main branch granting trust to developer 1")
    cmd = (
        "gittuf policy add-rule"
        f" -k {targets_private_key_path}"
        " --rule-name 'protect-main'"
        " --rule-pattern git:refs/heads/main"
        f" --authorize-key {dev1_public_key_path}"
    )
    display_command(cmd)
    run_command(cmd, 0)

    # Add a rule authorizing developer 2 to modify the feature branch
    step = prompt_key(automatic, step, GITTUF_STEPS, "Add a rule to protect the feature branch granting trust to developer 2")
    cmd = (
        "gittuf policy add-rule"
        f" -k {targets_private_key_path}"
        " --rule-name 'protect-feature'"
        " --rule-pattern git:refs/heads/feature"
        f" --authorize-key {dev2_public_key_path}"
    )
    display_command(cmd)
    run_command(cmd, 0)

    # Add a policy file for the main branch
    step = prompt_key(automatic, step, GITTUF_STEPS,
    "Create a delegated policy from the protect-main rule")
    cmd = f"gittuf policy init -k {dev1_private_key_path} --policy-name protect-main"
    display_command(cmd)
    run_command(cmd, 0)

    step = prompt_key(automatic, step, GITTUF_STEPS, "Add a rule in the delegated rule file granting trust to developer 3 for the feature branch")
    cmd = (
        "gittuf policy add-rule"
        " --policy-name protect-main"
        f" -k {dev1_private_key_path}"
        " --rule-name 'protect-feature-delegated'"
        " --rule-pattern git:refs/heads/feature"
        f" --authorize-key {dev3_public_key_path}"
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

    # Policy Violation
    print_section("[3 / 3] Policy Violation")

    step = 1

    # Set the git configuration to sign as Developer 3
    step = prompt_key(automatic, step, DEMO_STEPS,
    "Set repo config to use developer 3's identity and test key")
    cmd = "git config --local gpg.format ssh"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "git config --local commit.gpgsign true"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = f"git config --local user.signingkey {dev3_private_key_path}"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "git config --local user.name gittuf-demo"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "git config --local user.email gittuf.demo@example.com"
    display_command(cmd)
    run_command(cmd, 0)

    # Make a commit as Developer 3 to the feature branch
    step = prompt_key(automatic, step, DEMO_STEPS, "Make change to repo's feature branch")
    cmd = "git checkout -b feature"
    display_command(cmd)
    run_command(cmd, 0)
    display_command("echo 'Hello, new world!' > README.md")
    with open("README.md", "w", encoding="utf-8") as fp:
        fp.write("Hello, new world!\n")
    cmd = "git add README.md"
    display_command(cmd)
    run_command(cmd, 0)
    cmd = "git commit -m 'Another commit'"
    display_command(cmd)
    run_command(cmd, 0)

    step = prompt_key(automatic, step, DEMO_STEPS, "Record change to feature in RSL")
    cmd = "gittuf rsl record feature"
    display_command(cmd)
    run_command(cmd, 0)

    # Finally, verify the policy to find that the delegation was unauthorized
    step = prompt_key(automatic, step, DEMO_STEPS, "Developer 3 attempts to verify the policy...")
    cmd = "gittuf --verbose verify-ref feature"
    display_command(cmd)
    run_command(cmd, 1)

    print("\n...and finds out that developer 1 was not allowed in gittuf policy to grant them permissions for the feature branch!")


if __name__ == "__main__":
    check_binaries(REQUIRED_BINARIES)
    experiment2() # pylint: disable=no-value-for-parameter

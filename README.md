# Artifact Evaluation for gittuf - NDSS 2025

This repository contains the scripts and documentation needed to evaluate gittuf
as presented in the paper.

## Prerequisites

Before building and evaluating gittuf, you will need to install a few packages:

- A recent version of Python
- Git 2.43 or greater
- GNU `make`
- The Go toolchain

A reboot or shell reload is recommended after installing the prerequisites, as
updates to your PATH need to take effect before building gittuf will succeed.

## Building gittuf

Once all prerequisites are installed, download the source code for gittuf
v0.6.0, available
[here](https://github.com/gittuf/gittuf/archive/refs/tags/v0.6.0.zip). Unzip the
archive, open a terminal in the unzipped directory, and run the `make` command.
Build tests may take some time depending on your hardware and operating system,
but are important for ensuring the proper functioning of gittuf on your
platform.

## Running Evaluations

Each experiment is contained in its respective Python file. To run an
experiment, simply pass it to Python, e.g. `python3 experiment1.py`. The script
will then walk you through the steps in the experiment. Simply press the `Enter`
key to advance to the next step.

Each command is checked for proper functioning and return code. In the case of
an error, the script will print out the issue and abort.

### Customization

Each script file supports the same options as follows:

- `--automatic <False | True>`: Runs the demo without waiting on input to
  proceed to the next
  step.

- `--repository-directory <directory>`: Set a custom directory for the working
  repository. Note that this directory is not automatically deleted by the
  script after it exits.

## Experiment Details

### Experiment 1 - Unilateral Policy Modification

This experiment simulates a scenario with a repository owner (with key `root`)
creating a gittuf-enabled repository and delegating trust in the policy to two
developers (with keys `developer1` and `developer2`, respectively). To prevent a
single developer from making changes themselves, the threshold for policy
metadata signatures is set to two.

Developer 1 and 2 initialize and set a rule to protect the main branch in the
policy, with both developers signing off on the change.

Developer 1 then attempts to add another rule without developer 2's agreement,
which causes verification to fail.

### Experiment 2

In progress.

### Experiment 3 - RSL Divergence

This experiment simulates a scenario with a repository owner creating a
gittuf-enabled repository and making a commit. Another user unrelated to the
first developer (but with read access to the repository) then clones the
repository.

The original developer then goes back and overwrites the first commit with a
malicious edit. The other user attempts to pull the changes, but is warned by
git that there is a mismatch. The user overrides the warning, but upon pulling
the RSL, git raises an alarm that the RSL entry that there has been a divergence
in the RSL history.

### Experiment 4

In progress.

# Artifact Evaluation for gittuf - NDSS 2025

This repository contains the scripts and documentation needed to evaluate gittuf
as presented in the paper.

## Prerequisites

Before building and evaluating gittuf, you will need to install a few packages:

- A recent version of Python 3
  - [The `click` library](https://pypi.org/project/click/)
- [Git, 2.43 or greater](https://git-scm.com/downloads)
- GNU `make`
- [The Go toolchain, 1.22 or greater](https://go.dev/doc/install)

Installation of these tools varies with the operating system used.

A reboot or shell reload is recommended after installing the prerequisites, as
updates to your PATH need to take effect before building gittuf will succeed.

## Building gittuf

Once all prerequisites are installed, download the source code for gittuf,
available [here](https://github.com/gittuf/gittuf). Use the `main` branch.
Cloning using Git is preferred, but downloading the ZIP archive will work as
well.

**To clone both repositories, run:**
```sh
git clone https://github.com/gittuf/gittuf
git clone https://github.com/gittuf/ndss-eval
```

Open a terminal inside the downloaded repository directory and run the `make`
command. Build tests may take some time depending on your hardware and operating
system, but are important for ensuring the proper functioning of gittuf on your
platform.

**To build gittuf, run:**
```sh
cd gittuf
make
```

## Running Evaluations

Each experiment is contained in its respective Python file. To run an
experiment, simply pass it to Python, e.g. `python3 experiment1.py`. The script
will then walk you through the steps in the experiment. Simply press the `Enter`
key to advance to the next step.

Each command is checked for the proper return code. In the case of an error, the
script will print out the issue and abort.

Note that the Python scripts should not be moved from where they are in this
evaluation repository, as they depend on accessing the keys contained in the
`keys` folder. You can however select a custom location for where the script
should write the repository used for the experiment.

### Customization

Each script file supports these options:

- `--automatic [False | True]`: Runs the demo without waiting on input to
  proceed to the next
  step.

- `--repository-directory <directory>`: Set a custom directory for the working
  repository. Unlike the standard functionality with a temporary directory, the
  directory specified here is not automatically deleted by the script after it
  exits.

## Experiment Details

### Experiment 1 - Unilateral Policy Modification

This experiment simulates a scenario where a single developer is prevented from
editing a policy that was configured to require two developers to sign off.

First, a repository owner (with key `root`) creates a gittuf-enabled repository
and delegates trust in the policy to two developers (with keys `developer1` and
`developer2`, respectively). To prevent a single developer from making changes
themselves, the threshold for policy metadata signatures is set to two.

Developer 1 and 2 initialize and set a rule to protect the main branch in the
policy, with both developers signing off on the change.

Developer 1 then attempts to add another rule without developer 2's agreement,
which causes verification to fail.

**To run the experiment, run:**
```sh
python3 experiment1.py
```

### Experiment 2 - Delegations

This epxeriment simulates utilization of gittuf's delegations feature.

First, a repository owner defines a policy and delegates authority to make
changes to the `main` branch to developer 1. Developer 1 then (without
authorization) delegates access to the `feature` branch to developer 2.
Developer 2 then makes a change to the `feature` branch.

When the developer attempts to verify the changes made to policy and branches,
gittuf alerts them to the unathorized changes.

**To run the experiment, run:**
```sh
python3 experiment2.py
```

### Experiment 3 - RSL Divergence

This experiment simulates a scenario focusing on how gittuf's Reference State
Log (RSL) propagates across repository copies.

First, a repository owner creates a gittuf-enabled repository and makes a
commit. User A then clones the repository and makes a change (authorized by the
policy), and then pushes their changes. The upstream repository owner drops
these changes.

User B then clones the repository, unaware as to what has happened. The user
makes a commit and pushes it to the remote repository. User A then attempts to
pull the latest changes, but is warned that their branch has diverged from what
is on the remote repository.

**To run the experiment, run:**
```sh
python3 experiment3.py
```

### Experiment 4 - Policy Violation and Independent Verification

This experiment simulates a scenario where an user writes to a part of a
repository they are not allowed to; another user then pulls the latest copy of
the repository and then attempts to verify the changes.

A repository owner creates a gittuf-enabled repository and sets policy
authorizing a user (with key `developer1`) to make changes to the main branch.
Another user (with key `developer2`), who is only allowed to edit the `feature`
branch, submits a commit that affects the `main` branch.

Another developer then clones the repository onto their machine and attempts to
verify the changes, but gittuf raises an alert that an unauthorized signature is
on a commit (against the policy).

**To run the experiment, run:**
```sh
python3 experiment4.py
```

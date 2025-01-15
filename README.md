### Build Status
[![MacOS Build with PDM](https://github.com/jgraeb/floras/actions/workflows/macos_build_pdm.yaml/badge.svg?branch=main)](https://github.com/jgraeb/floras/actions/workflows/macos_build_pdm.yaml)
[![MacOS Build with conda](https://github.com/jgraeb/floras/actions/workflows/macos_build_conda.yaml/badge.svg?branch=main)](https://github.com/jgraeb/floras/actions/workflows/macos_build_conda.yaml)

[![Ubuntu Build with PDM](https://github.com/jgraeb/floras/actions/workflows/ubuntu_build_pdm.yaml/badge.svg?branch=main)](https://github.com/jgraeb/floras/actions/workflows/ubuntu_build_pdm.yaml)
[![Ubuntu Build with conda](https://github.com/jgraeb/floras/actions/workflows/ubuntu_build_conda.yaml/badge.svg?branch=main)](https://github.com/jgraeb/floras/actions/workflows/ubuntu_build_conda.yaml)

[![codecov](https://codecov.io/github/jgraeb/floras/graph/badge.svg?token=XB5ZDOWZK2)](https://codecov.io/github/jgraeb/floras)
[![Lint](https://github.com/jgraeb/floras/actions/workflows/lint.yaml/badge.svg?branch=main)](https://github.com/jgraeb/floras/actions/workflows/lint.yaml)

# Floras: Flow-Based Reactive Test Synthesis for Autonomous Systems

<p align="center">
  <img src="https://raw.githubusercontent.com/jgraeb/floras/refs/heads/main/docs/logo.png" width="250" />
</p>

Floras documentation can be found [here](https://floras.readthedocs.io).

### Requirements
Floras requires `Python>=3.10,<3.13` and a C++17-compliant compiler (for example `g++>=7.0` or `clang++>=5.0`).
You can check the versions by running `python --version` and `gcc --version`.

#### Pre-installing Graphviz
Please pre-install [graphviz](https://graphviz.org) and [pygraphviz](https://pygraphviz.github.io).
If you are using a Mac, please install it via [brew](https://brew.sh) and [pip](https://pypi.org/project/pip/):
```
brew install graphviz
pip install pygraphviz
```
On Ubuntu, please install graphviz using these commands:
```
sudo apt-get install graphviz graphviz-dev
pip install pygraphviz
```

## Installing Floras

To install floras, please clone the repository:
```
git clone https://github.com/tulip-control/floras.git
```
We are using [pdm](https://pdm-project.org/en/latest/) to manage the dependencies.
```
pip install pdm
```
Navigate to the repo to install floras and all required dependencies:
```
cd floras
pdm install
```
Next, install [spot](https://spot.lre.epita.fr/) by running:
```
pdm run python get_spot.py
```
If you are using [conda](https://conda.org/), instead of the above command, you can install spot directly from [conda-forge](https://conda-forge.org/) (this is faster). This does not work on MacOS, please use the above command to build spot in that case.
```
conda install -c conda-forge spot
```
If the spot installation does not work, please install it according to the instructions on the [spot website](https://spot.lre.epita.fr/install.html).

To enter the virtual environment created by pdm:
```
$(pdm venv activate)
```
You can test your installation by running the following command:
```
pdm run pytest -v tests
```

For installation instructions and troubleshooting, please visit [this page](https://floras.readthedocs.io/en/latest/contributing/).


The floras repository contains implementations of the algorithms developed in the following paper:

[Josefine B. Graebener*, Apurva S. Badithela*, Denizalp Goktas, Wyatt Ubellacker, Eric V. Mazumdar, Aaron D. Ames, and Richard M. Murray. "Flow-Based Synthesis of Reactive Tests for Discrete Decision-Making Systems with Temporal Logic Specifications." ArXiv abs/2404.09888 (2024).](https://arxiv.org/abs/2404.09888)

# Installing Floras
### Requirements
Floras requires `Python>=3.10,<3.13` and a C++17-compliant compiler (for example `g++>=7.0` or `clang++>=5.0`).
You can check the versions by running `python --version` and `gcc --version`.

#### Pre-installing Graphviz
Please pre-install [graphviz](https://graphviz.org) and [pygraphviz](https://pygraphviz.github.io).
If you are using a Mac, please install it via [brew](https://brew.sh):
```
brew install graphviz
export CFLAGS="-I $(brew --prefix graphviz)/include"
export LDFLAGS="-L $(brew --prefix graphviz)/lib"
pip install pygraphviz
```
On Ubuntu, please install graphviz using these commands:
```
sudo apt-get install graphviz graphviz-dev
pip install pygraphviz
```

### From Source
To install floras directly from source, please clone the repository:
```
git clone https://github.com/tulip-control/floras.git
```
We are using [pdm](https://pdm-project.org/en/latest/) to manage the dependencies, please install it using [pip](https://pypi.org/project/pip/).
```
pip install pdm
```
After installing graphviz as described in the last section, navigate to the repo to install floras and the required dependencies:
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

### Troubleshooting
Here are common errors we encountered and what we learned to fix the problem.

If you are on a Mac and your C++ compiler version is correct, but the build still fails, try adding the following command to your path:
```
export SDKROOT=$(xcrun --show-sdk-path)
```

If installing pygraphviz fails, you can try to install it using the following command:
```
pip install --no-cache-dir \
   --config-settings="--global-option=build_ext" \
   --config-settings="--global-option=-I$(brew --prefix graphviz)/include/" \
   --config-settings="--global-option=-L$(brew --prefix graphviz)/lib/" \
   --use-pep517 \
   pygraphviz
```

If you are using conda, you can try installing graphviz via conda ([this](https://pygraphviz.github.io/documentation/pygraphviz-1.7/install.html) is not recommended but might work for a Python version `<=3.11`). For more info on how to debug the graphviz installation, please check out the [graphviz documentation](https://pygraphviz.github.io/documentation/stable/install.html).

Floras requires `spot`, which should be automatically installed when following the steps above. If the spot installation fails, please download [spot](https://spot.lre.epita.fr/install.html) from its source, follow the instructions in the spot documentation, and repeat the floras installation.

# phy: interactive visualization and manual spike sorting of large-scale ephys data

[![Build Status](https://travis-ci.org/cortex-lab/phy.svg?branch=dev)](https://travis-ci.org/cortex-lab/phy)
[![codecov.io](https://img.shields.io/codecov/c/github/cortex-lab/phy.svg)](http://codecov.io/github/cortex-lab/phy?branch=dev)
[![Documentation Status](https://readthedocs.org/projects/phy/badge/?version=latest)](https://phy.readthedocs.io/en/latest/?badge=latest)
[![GitHub release](https://img.shields.io/github/release/cortex-lab/phy.svg)](https://github.com/cortex-lab/phy/releases/latest)
<!-- [![PyPI release](https://img.shields.io/pypi/v/phy.svg)](https://pypi.python.org/pypi/phy) -->

[**phy**](https://github.com/cortex-lab/phy) is an open-source Python library providing a graphical user interface for visualization and manual curation of large-scale electrophysiological data. It is optimized for high-density multielectrode arrays containing hundreds to thousands of recording sites (mostly [Neuropixels probes](https://www.ucl.ac.uk/neuropixels/)).

[![phy 2.0a1 screenshot](https://user-images.githubusercontent.com/1942359/61941399-b00bda00-af97-11e9-92d9-5b7308ed25ac.png)](https://user-images.githubusercontent.com/1942359/61941399-b00bda00-af97-11e9-92d9-5b7308ed25ac.png)


## Links

* [**Documentation**](http://phy.readthedocs.org/en/latest/)
* [Mailing list](https://groups.google.com/forum/#!forum/phy-users)


## User installation instructions

If you are isntalling from the original repo, [**click here to see the installation instructions.**](https://phy.readthedocs.io/en/latest/installation/). Otherwise, my particular installations instructions are as follow:

```bash
conda create -n myPhy2 python pip numpy matplotlib scipy h5py pyqt cython -y
conda activate phy2
pip install colorcet 
pip install pyopengl 
pip install qtconsole 
pip install requests 
pip install traitlets 
pip install tqdm 
pip install joblib 
pip install click 
pip install mkdocs
```

(for some reason, in Windows seems to be better to install each reqire separately)

Now, to install Phy proper, you have two options:

If installing from the remote repo:

```bash
pip install git+https://github.com/fjflores/phy.git@dev
```

or if installing from the local repo:

```bash
cd path-to-phy/phy
pip install -e .
```

and finally, install the [Phylib](https://github.com/fjflores/phylib) library

```bash
pip install git+https://github.com/fjflores/phylib.git
```

## Credits

**phy** is developed by [Cyrille Rossant](http://cyrille.rossant.net).

Past and present contributors include:

* [Shabnam Kadir](https://iris.ucl.ac.uk/iris/browse/profile?upi=SKADI56)
* [Dan Goodman](http://thesamovar.net/)
* [Max Hunter](https://iris.ucl.ac.uk/iris/browse/profile?upi=MLDHU99)
* [Kenneth Harris](https://iris.ucl.ac.uk/iris/browse/profile?upi=KDHAR02)

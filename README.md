# Dhammapada latine

[![SWH](https://archive.softwareheritage.org/badge/origin/https://github.com/ETCBC/dhammapada/)](https://archive.softwareheritage.org/browse/origin/?origin_url=https://github.com/ETCBC/dhammapada)
[![DOI](https://zenodo.org/badge/440102377.svg)](https://zenodo.org/badge/latestdoi/440102377)
[![Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip)

[![etcbc](programs/images/etcbc.png)](http://www.etcbc.nl)
![logo](programs/images/logo.png)
[![dans](programs/images/dans.png)](https://dans.knaw.nl/en)
[![tf](programs/images/tf-small.png)](https://annotation.github.io/text-fabric/tf)


## About

This is the
[text-fabric](https://github.com/annotation/text-fabric)
representation of the Dhammapada in the edition with Latin translation by V. Fausböll, 1900.

See [about](docs/about.md) for more information about this textual source.

The conversion to Text-Fabric is joint work of 

*   [prof. dr. Bee Scherer](https://research.vu.nl/en/persons/bee-scherer),
    Text and Traditions,
    VU-University Amsterdam;
*   [prof. dr. Willem van Peursen](https://research.vu.nl/en/persons/willem-van-peursen),
    [ETCBC](http://www.etcbc.nl),
    VU-University Amsterdam;
*   Yvonne Mataar,
    transcription and correction
*   [dr. Dirk Roorda](https://pure.knaw.nl/portal/en/persons/dirk-roorda),
    [DANS](https://www.dans.knaw.nl),
    conversion to the Text-Fabric-sphere.

There is more information on the
[transcription](docs/transcription.md).

## How to use

### Without installing anything

There is an online search interface to both the Pāli text and the Latin translation.
It is online, but it works purely on your computer, in the browser.

Just click
[dhammapada-search](https://etcbc.github.io/dhammapada-search/)
and off you go.

**Hint 1:**
Search for the latin word `et`.

**Hint 2:**
Click on the buttons `pali` or `latin` to see a sizable portion of the text.
This might give you some clues for patterns to search.

### Having Text-Fabric installed

This data can be processed by 
[Text-Fabric](https://annotation.github.io/text-fabric/tf).

Text-Fabric will automatically download the corpus data.

After [installing Text-Fabric](https://annotation.github.io/text-fabric/tf/about/install.html),
you can start the Text-Fabric browser by this command

```sh
text-fabric etcbc/dhammapada
```

Alternatively, you can work in a Jupyter notebook and say

```python
from tf.app import use

A = use('etcbc/dhammapada')
```

In both cases the data is downloaded and ends up in your home directory,
under `text-fabric-data`.

See also 
[start](https://nbviewer.jupyter.org/github/etcbc/dhammapada/blob/master/tutorial/start.ipynb)
and
[search](https://nbviewer.jupyter.org/github/etcbc/dhammapada/blob/master/tutorial/search.ipynb).

# Author

[Dirk Roorda](https://github.com/dirkroorda)

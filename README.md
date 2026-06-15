<p align="center">
<img src="https://yidingli.com/docs/evokit/_images/gear.svg" width=120em>
</p>



# EVOKIT

A modular, [permissively licensed](./LICENCE.txt), highly customisable evolutionary computing framework. This framework was developed further from [my MEng report](media\YidingLi-MEng-2024-09-23.pdf), produced with supervision and guidance from [Dr. Stephen Kelly](https://creativealgorithms-cd4c88.gitlab.io/team/).

This framework is thoroughly documented and completely typed. Please see the [documentation](https://yidingli.com/docs/evokit/index.html) for instructions on how to install and use it.

## Installation

Install from PyPI:

```shell
pip install evokit
```

Install from source:

```
pip install .
```

Please see [the installation guide](https://yidingli.com/projects/evokit/docs/install-and-build.html) for detailed instructions on building and conducting trial runs.

## Components

The library have the following modules:

| Component                                                    | Description                                                  |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| [core](https://yidingli.com/docs/evokit/evokit.core.html)    | Interfaces for custom evolutionary operators                 |
| [core.accelerator](https://yidingli.com/docs/evokit/evokit.core.accelerator.html) | Performance-boosting utilities; parallelisation              |
| [watch](https://yidingli.com/docs/evokit/evokit.watch.html)  | Utilities to observe and report algorithms at runtime. Also includes performance profilers. |
| [evolvables](https://yidingli.com/docs/evokit/evokit.evolvables.html) | Custom evolutionary operators, including representations     |
| [tools.diversity](https://yidingli.com/docs/evokit/evokit.tools.diversity.html) | Diversity maintenance                                        |
| [tools.lineage](https://yidingli.com/docs/evokit/evokit.tools.lineage.html) | Lineage tracing                                              |
| `save`, `load` in [core.population](https://yidingli.com/docs/evokit/evokit.core.html#evokit.core.population.save) | Saving and loading individuals and populations               |
| [evolvables.ac](https://yidingli.com/docs/evokit/evokit.evolvables.ac.html) | Artificial Chemistry                                         |

## Other Licences

The documentation includes a local copy of the Open Sans font by [Steve Matteson](https://mattesontypographics.com/). The font is distributed under the [Open Font Licence](https://openfontlicense.org/open-font-license-official-text/). The font only exists in the documentation [i.e. here](./docs/source/_static/OpenSans-Regular.ttf) and is not included in the software.




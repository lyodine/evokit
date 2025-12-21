<p align="center">
<img src="./media/gear.svg" width=100>
</p>

# EVOKIT

A modular, [permissively licensed](./LICENCE.txt), highly customisable evolutionary computing framework. This framework was developed further from [my MEng report](media\YidingLi-MEng-2024-09-23.pdf), produced with supervision and guidance from [Dr. Stephen Kelly](https://creativealgorithms-cd4c88.gitlab.io/team/).

This framework is thoroughly documented and completely typed. Please see the [documentation] for instructions on how to install and use it.

## Installation

Install from PyPI:

```shell
pip install evokit
```

Install from source:

```
pip install .
```

Please see [documentation](https://yidingli.com/projects/evokit/docs/install-and-build.html) for detailed instructions, how the project is built, and how to perform a trial run after installation.

## Components

The library have the following modules:

| Component                                                    | Description                                              |
| ------------------------------------------------------------ | -------------------------------------------------------- |
| [core](./evokit/core/)                                       | Interfaces for custom evolutionary operators             |
| [core.accelerator](./evokit/core/accelerator/)               | Performance-boosting utilities; parallelisation          |
| [accounting](./evokit/accounting/)                           | Monitor and report algorithms at runtime                 |
| [core.accelerator](./evokit/evolvables/)                     | Custom evolutionary operators, including representations |
| [tools.diversity](./evokit/tools/diversity/)                 | Diversity maintenance                                    |
| [core.lineage](./evokit/tools/lineage/)                      | Lineage tracing                                          |
| `save`, `load` in [core.population](./evokit/core/population.py) | Saving and loading individuals and populations           |




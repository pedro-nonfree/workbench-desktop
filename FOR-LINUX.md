## Dependencies

In order to execute this program properly you have to install the SmartmonTools version 7 or superior program and the dmidecode package (only in Linux).

It is available in most Linux systems. Depending on your distribution you have to introduce the next command in a terminal:

Debian/Ubuntu/Linux Mint and Debian based distributions:

```
sudo apt-get install smartmontools dmidecode
```

Arch Linux and Arch based distributions:

```
sudo pacman -S smartmontools dmidecode
```

Fedora/Centos/OpenSuse and Red Hat derivates:

```
sudo yum install smartmontools dmidecode
```

Solus:

```
sudo eopkg it smartmontools dmidecode
```

## Building

In order to build the different releases for the objective operating system, the usage of the PyInstaller library is mandatory.

Execute:

```
pyinstaller --windowed -F --icon="path to .ico" -n "workbench" workbench.py
```

## Installation

Extract the workbench.tar.gz file: `tar -xvf workbench.tar.gz`

## Usage

Execute the program with admin privileges:

```
sudo ./workbench
```

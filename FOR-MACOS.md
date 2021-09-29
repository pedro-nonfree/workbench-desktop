## Dependencies

In order to execute this program properly you have to install the SmartmonTools version 7 or superior program and the dmidecode package (only in Linux).

If you do not have installed brew in MacOS, open a terminal and type in the next command:

```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Then type the following in your terminal:

```
brew install smartmontools
```

## Building

In order to build the different releases for the objective operating system, the usage of the PyInstaller library is mandatory.

Execute:

```
pyinstaller --windowed -F --icon="path to .icns" -n "workbench" workbench.py
```

## Installation

Extract the workbench.tar.gz file:

```
tar -xvf workbench.tar.gz
```

## Usage

Execute the program with admin privileges:

```
sudo ./workbench
```

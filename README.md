# eReuse.org Workbench Desktop
## What does this program do?
eReuse.org Workbench Desktop is a desktop cross-platform application which intends to extract information about the hardware of computer devices and deliver a snapshot.
## How it works?
![Workbench Desktop](/diagram/Workbench_Desktop.png)
## Dependencies
In order to execute this program properly you have to install the SmartmonTools version 7 or superior program and the dmidecode package (only in Linux).
### Linux
It is available in most Linux systems. Depending on your distribution you have to introduce the next command in a terminal:
- Debian/Ubuntu/Linux Mint and Debian based distributions: **$ sudo apt-get install smartmontools dmidecode**
- Arch Linux and Arch based distributions: **$ sudo pacman -S smartmontools dmidecode**
- Fedora/Centos/OpenSuse and Red Hat derivates: **$ sudo yum install smartmontools dmidecode**
- Solus: **$ sudo eopkg it smartmontools dmidecode**
### Windows
The program is already included in the installation process, you only have to execute the installer and follow the instructions.
### MacOS
If you do not have installed brew in MacOS, open a terminal and type in the next command: **$ /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"** \
Then type the following in your terminal: **$ brew install smartmontools**
## Building
In order to build the different releases for the objective operating system, the usage of the PyInstaller library is mandatory.
### Linux
- Execute: **pyinstaller --windowed -F --icon="path to .ico" -n "workbench" workbench.py**
### Windows
- Execute: **pyinstaller --windowed -F --uac-admin --icon="path to .ico" -n "workbench" workbench.py**
- There is a script writen that 
### MacOS
- Execute: **pyinstaller --windowed -F --icon="path to .icns" -n "workbench" workbench.py**
## Installation
### Linux
- Extract the workbench.tar.gz file: **$ tar -xvf workbench.tar.gz**
### Windows
- Execute the installer and follow the steps
- After that the program should be placed in Program Files (x86)\\eReuse.org\\Workbench
### MacOS
- Extract the workbench.tar.gz file: **$ tar -xvf workbench.tar.gz**
## Usage
### Linux
- Execute the program with admin privileges: **$ sudo ./workbench**
### Windows
- Execute the program placed in **Program Files (x86)\\eReuse.org\\Workbench**
### MacOS
- Execute the program with admin privileges: **$ sudo ./workbench**

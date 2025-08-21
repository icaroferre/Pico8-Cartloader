# Pico8 Cartloader

The Pico8 Cartloader is a multi-threaded Python script designed to downloads cartridges from the [Lexaloffle BBS](https://www.lexaloffle.com/bbs/?cat=7#sub=2), scrape the cartridge's data (title, developer, description), download the thumbnails, and generate a gamelist.xml file for systems running Emulation Station (specially the RG351P).

By default it'll download the first 10 pages of featured cartridges and output all files to an ```output``` folder in the script's folder.

# How to Use

Install all requirements from the ```requirements.txt``` file (```pip3 install -r requirements.txt```) and run ```python3 path/to/folder/carloader.py```.


------

Developed by  
[@icaroferre](http://twitter.com/icaroferre)

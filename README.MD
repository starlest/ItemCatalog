# TournamentDatabase
Project 4 of Udacity's Full Stack Web Developer Nanodegree Program

# Requirements
1) [Git](http://git-scm.com/downloads).  
2) [VirtualBox](https://www.virtualbox.org/wiki/Downloads).  
3) [Vagrant](https://www.vagrantup.com/downloads.html).

# Installations
1) Install all the required programs if you have not done so.  
2) Using the terminal, change directory to folder of this repisotory in your PC.  
3) Type "vagrant up" to launch your virtual machine.  
4) Once it is up and running, type "vagrant ssh" to log into it.  
5) Change directory to the tournament folder with the required files by typing "cd /vagrant/catalog".  
6) Set up the database by typing "psql" and once inside "create database catalog;"
7) Exit the psql by pressing CTR+D
8) Setup the database next "python database_setup.py"
9) Insert dummy categories "python load_database.py"
10) Run the server "python main.py"
11) View the website at your browser "localhost:5000"
12) When you want to log out, type exit at the shell prompt. 
13) To turn the virtual machine off (without deleting anything), type "vagrant halt".   
  
Reference: https://udacity.atlassian.net/wiki/display/BENDH/Vagrant+VM+Installation

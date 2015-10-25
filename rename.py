# -*- coding: cp1251 -*-
import requests, sys, os, logging, datetime, string, shutil

from HTMLParser import HTMLParser
from xml.dom.minidom import parseString

path = u'/Volumes/D/Video/Films/'
onlyfiles = os.listdir(path)
files = onlyfiles
countOfFiles = len(files)

def search( FileName, EditedFileName ):
	if len(EditedFileName) > 2:
		print "[E] %s " %EditedFileName
		r = requests.get("http://www.kinopoisk.ru/index.php?first=no&what=&kp_query="+EditedFileName)
	else:
		print "[F] %s " %FileName
		r = requests.get("http://www.kinopoisk.ru/index.php?first=no&what=&kp_query="+FileName)

	# FilmBlock = часть html файла с информацией о фильме
	content = r.content.decode('cp1251')
	FilmBlock = content[(content.find('element most_wanted')):]
	FilmBlock = FilmBlock[:-(len(FilmBlock)-2000)]

	# Выдираем информацию о фильме
	# RusName = Название фильма на русском
	RusName = FilmBlock[(FilmBlock.find('<div class="info">'))+50:]
	RusName = RusName[:-(len(RusName)-100)]
	RusName = RusName[(RusName.find('">'))+2:]
	RusName = RusName[:-(len(RusName)-(RusName.find('</a> <span class="year')))]
	RusName = RusName.replace('&nbsp;',' ')

	# EngName = Название фильма на английском
	EngName = FilmBlock[(FilmBlock.find('<span class="year">'))+19:]
	EngName = EngName[(EngName.find('<span class="gray">'))+19:]
	EngName = EngName[:-(len(EngName)-(EngName.find('</span>'))+9)]
	EngName = EngName.replace('&nbsp;',' ')
	
	# year = год выхода фильма
	year = FilmBlock[(FilmBlock.find('<span class="year">'))+19:]
	year = year[:-(len(year)-4)]

	# ext = расширение исходного файла
	ext = FileName[(len(FileName)-4):]
	NewName = RusName+' ('+EngName+') '+year+ext

	# Выводим название название фильма с kinopoisk.ru в консоль
	print "[S] %s " %NewName
	if NewName == FileName: #and NewName.decode() != EditedFileName.decode():
		print "Фильм соответствует формату"
	else:
		answer = raw_input("Rename? (y/n) Edit file name (e): ")
		if answer == "y" or answer == "Y":
			print "Переименовываю"
			shutil.move(path+FileName,path+NewName)
			print "Переименовал"
		if answer == "n" or answer == "N":
			print "Не переименовываю"
		if answer == "e" or answer == "E":
			print "Old file name: %s" %FileName
			EditFileName = raw_input("New search name = ")
			search(FileName = FileName,EditedFileName =EditFileName)

for i in range(1, countOfFiles):
	search (FileName = files[i], EditedFileName = "")
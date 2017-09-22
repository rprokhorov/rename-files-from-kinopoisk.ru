import requests, sys, os, logging, datetime, string, shutil, re
from lxml import html
# Mac OS X Path
#path = u'/Volumes/D/Video/Films/Rename/'
# Windows Path
path = u'Z:\Video\Films\Rename'
pathnew = u'Z:\Video\Films'
headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'
      }
onlyfiles = os.listdir(path)
files = onlyfiles
countOfFiles = len(files)
print(countOfFiles)
def search(FileName, EditedFileName):
	if len (EditedFileName) > 0:
		print ("[E] %s " %EditedFileName)
		r = requests.get("http://www.kinopoisk.ru/index.php?first=no&what=&kp_query="+EditedFileName, headers = headers)
	else:
		print ("[F] %s " %FileName)
		r = requests.get("http://www.kinopoisk.ru/index.php?first=no&what=&kp_query="+FileName, headers = headers)
	# FilmBlock = С‡Р°СЃС‚СЊ html С„Р°Р№Р»Р° СЃ РёРЅС„РѕСЂРјР°С†РёРµР№ Рѕ С„РёР»СЊРјРµ
	tree = html.fromstring(r.content)
	link = tree.xpath('//div[@class = "info"]/p/a/@href')[0]
	title_array = []
	for el in range(0, 5):
		try:
			# RusName - the name of the movie in Russian
			RusName = re.sub('[^0-9а-яА-Яa-zA-Z\ \(\)\-\,\.]','',tree.xpath('//div[@class = "info"]/p/a/text()')[el])
			# EnName - the name of the movie in English
			EngName = re.sub('[^0-9а-яА-Яa-zA-Z\ \(\)\-\,\.]','',tree.xpath('//div[@class = "info"]/span/text()')[el]).split(", ")
			del EngName[-1]
			EngName = ''.join(EngName)
			# Year - movie release date
			Year = tree.xpath('//div[@class = "info"]/p/span/text()')[el]
			Duration = re.sub('[^0-9а-яА-Яa-zA-Z\ \(\)\-\,\.]','',tree.xpath('//div[@class = "info"]/span/text()')[el]).split(", ")[-1]
			ext = FileName.split(".")[-1]
			NewName = RusName+' ('+EngName+') ['+Duration+'] '+Year+'.'+ext
			print ("["+str(el+1)+"] "+NewName)
			title_array.append(NewName)
		except Exception:
			print ("")
	answer = input("Rename (1-6). Escape (n). Edit file name (e): ")
	if answer == "1" or answer == "2" or answer == "3" or answer == "4" or answer == "5" or answer == "6":
		print (title_array[int(answer)-1])
		print ("Renaming")
		shutil.move(path+"\\"+FileName,pathnew+"\\"+title_array[int(answer)-1])
		print ("Done!")
	if answer == "n" or answer == "N":
		print ("Escaped.")
	if answer == "e" or answer == "E":
		print ("Old file name: %s" %FileName)
		EditFileName = input("New search name = ")
		search(FileName = FileName,EditedFileName =EditFileName)

for i in range(0, countOfFiles):
	search (FileName = files[i], EditedFileName = "")

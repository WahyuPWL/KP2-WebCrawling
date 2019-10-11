import os
import urllib.request

listLog=["Doaj.log","Ieee.log","Rg.log","Sinta2.log"]
for i in listLog:
 try:
  os.remove(i)
 except FileNotFoundError:
  continue
urllib.request.urlopen('http://127.0.0.1:8000/main')
urllib.request.urlopen('http://127.0.0.1:8000/fix')

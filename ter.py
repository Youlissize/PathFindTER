import pandas as pd
import matplotlib.pyplot as plt
import sys
import os
import requests
import zipfile
from tqdm import tqdm
import json

#update les données si : pas dans dossier ou n'importe quel argument en executant le script
larg=[]
for arg in sys.argv:
    larg.append(arg)
if not os.path.isfile("data.zip") or len(larg)>1:
    url="https://eu.ftp.opendatasoft.com/sncf/gtfs/export-ter-gtfs-last.zip"
    r = requests.get(url)  
    with open('data.zip', 'wb') as f:
            f.write(r.content)
    with zipfile.ZipFile("data.zip", 'r') as zip_ref:
            zip_ref.extractall()

#le parseur de pandas en fait il marche bien
calendar_dates=pd.read_csv("calendar_dates.txt")
stops=pd.read_csv("stops.txt")
stop_times=pd.read_csv("stop_times.txt")
routes=pd.read_csv("routes.txt")
transfers=pd.read_csv("transfers.txt")
trips=pd.read_csv("trips.txt")

#du coup on fait une liste de chaque arrêt avec leurs id, nom et position et on initie un dictionaire qui à chaque arrêt va donner la liste de ses voisins 
stoppointsfull=stops.groupby("location_type").get_group(0)
stoppoints=stoppointsfull[["stop_id","stop_name","stop_lon","stop_lat"]]
neighbours=dict(zip([i for i in stoppoints.stop_id],[set([]) for i in stoppoints.stop_id]))

# et maintenant on créé une fonction qui itere de manière bien degueulasse sur chacun des 230244 trajets individuels, et on prend la liste ordonnée de ses arrêts, puis on en tire les voisins et on en remplit le dictionaire neighbours créé plus haut pour l'arrêt en question
# le tqdm il sert à avoir une barre de chargement pour se rendre compte que sur mon pc ça prendrait 6h de calculs
pastgsids=[]
groupedbytrip=stop_times.groupby('trip_id')
def get_neighbours():
    for i in tqdm(stop_times.trip_id):
        g=groupedbytrip.get_group(i)
        gsid=[sid for sid in g.stop_id]
        if set(gsid) not in pastgsids:
            for i,n in zip(gsid,range(len(gsid))):
                if n==0:
                    neighbours[i].update([gsid[1]])
                if n==len(gsid)-1:
                    neighbours[i].update([gsid[-2]])
                else:
                    neighbours[i].update([gsid[n+1]])
                    neighbours[i].update([gsid[n-1]])
            pastgsids.append(set(gsid))

get_neighbours()

neighbourslisted = {k: list(v) for k, v in neighbours.items()}

# maintenant pour sauvegarder les résultats dans des fichiers
with open('neighbours.json', 'w') as f:
    json.dump(neighbourslisted,f)

with open('stoppoints.json', 'w') as f:
    f.write(stoppoints.to_json(orient="table",force_ascii=False,index=False))

with open("uniquetrips.txt","w") as f:
    f.write(str(pastgsids))

#joli gui pour visualiser les données si jamais
#from pandasgui import show
#show(stops,stop_times,calendar_dates,transfers,routes,trips)

import zipfile, json, csv, io
import pandas as pd, numpy as np
frames=[]
for y,enc in ((2023,"utf-8-sig"),(2024,"utf-8-sig"),(2025,"cp1252")):
    z=zipfile.ZipFile(f"c{y}.zip"); n=[i for i in z.namelist() if i.endswith(".csv")][0]
    with z.open(n) as f: head=f.readline().decode(enc).lstrip("﻿")
    sep=";" if head.count(";")>head.count(",") else ","
    cols=[c.strip('"') for c in next(csv.reader([head],delimiter=sep))]
    with z.open(n) as f:
        df=pd.read_csv(f,sep=sep,encoding=enc,usecols=[cols[0],cols[4],cols[5]],dtype=str,keep_default_na=False)
    df.columns=["c","v","d"]; df["v"]=pd.to_numeric(df.v,errors="coerce")
    off=df.d.str.contains(r"[+-]\d{4}$")
    t=pd.to_datetime(df.d.str.replace(r" ([+-]\d{4})$",r"\1",regex=True).str.replace(" ","T",n=1),format="mixed",errors="coerce",utc=False) if False else None
    if off.all():
        ts=pd.to_datetime(df.d.str.replace(r" ([+-]\d{4})$",r"\1",regex=True),format="%Y-%m-%d %H:%M:%S.%f%z",utc=True)
    else:
        loc=pd.to_datetime(df.d.str[:19].str.replace(" ","T"),errors="coerce")
        ts=loc.dt.tz_localize("Europe/Paris",ambiguous="NaT",nonexistent="shift_forward").dt.tz_convert("UTC")
    df["h"]=ts; print(y,len(df),"offset" if off.all() else "naif",int(df.h.isna().sum()),"NaT",flush=True)
    frames.append(df[["c","v","h"]])
d=pd.concat(frames); d=d.dropna(subset=["h"])
d=d.drop_duplicates(["c","h"])
d["j"]=d.h.dt.tz_convert("Europe/Paris").dt.date
dj=d.groupby(["c","j"]).v.sum(); act_j=dj[dj>0].reset_index().groupby("j").c.nunique()
mm=d.assign(m=d.h.dt.tz_convert("Europe/Paris").dt.to_period("M")); dm=mm.groupby(["c","m"]).v.sum(); act_m=dm[dm>0].reset_index().groupby("m").c.nunique()
d.attrs["x"]=1
g=d.groupby("h").agg(passages_total=("v","sum"),compteurs_actifs=("c","nunique"),compteurs_non_nuls=("v",lambda s:int((s>0).sum())))
m=json.load(open("meteo.json"))["hourly"]
w=pd.DataFrame({"h":pd.to_datetime(m["time"],utc=True),"temperature_c":m["temperature_2m"],"precipitation_mm":m["precipitation"],"pluie_mm":m["rain"],"vent_kmh":m["wind_speed_10m"]}).set_index("h")
t=w.join(g,how="left")
loc=t.index.tz_convert("Europe/Paris")
t["act_jour"]=pd.Series(loc.date,index=t.index).map(act_j).values
t["act_mois"]=pd.Series(loc.to_period("M"),index=t.index).map(act_m).values; print("heures:",len(t),"sans compteur:",int(t.passages_total.isna().sum()))
t.to_pickle("heure2.pkl")

import pandas as pd, numpy as np, itertools
t=pd.read_pickle("heure.pkl").reset_index().rename(columns={"h":"heure_utc"})
t["heure_paris"]=t.heure_utc.dt.tz_convert("Europe/Paris")
t["date_paris"]=t.heure_paris.dt.date; t["hj"]=t.heure_paris.dt.hour; t["mois"]=t.heure_paris.dt.month
t["saison"]=t.mois.map(lambda m:"hiver" if m in(12,1,2) else "printemps" if m in(3,4,5) else "été" if m in(6,7,8) else "automne")
t["type_jour"]=np.where(t.heure_paris.dt.dayofweek>=5,"week-end","semaine")
t["il_pleut"]=t.precipitation_mm>=0.1
print("manquants compteurs:",int(t.passages_total.isna().sum()),"| heures de pluie:",int(t.il_pleut.sum()))
def ppc(df,mode):
    if mode=="actifs": return df.passages_total/df.compteurs_actifs
    return df.passages_total/df.compteurs_non_nuls.replace(0,np.nan)
def effet(df,col="ppc"):
    d=df.dropna(subset=[col])
    g=d.groupby(["type_jour","saison","hj"])
    rows=[]
    for k,x in g:
        p=x[x.il_pleut]; s=x[~x.il_pleut]
        if len(p)>=5 and len(s)>0 and s[col].mean()!=0: rows.append((k[0],len(p),p[col].mean()/s[col].mean()-1))
    r=pd.DataFrame(rows,columns=["tj","np","e"])
    out=r.groupby("tj").apply(lambda x:(x.np*x.e).sum()/x.np.sum()); return out.round(4).to_dict(), int(r.np.sum())
for mode in("actifs","non_nuls"):
    t["ppc"]=ppc(t,mode)
    print("== passages par compteur =",mode, "| effet semaine/week-end, heures de pluie retenues:",effet(t))
    for name,pts in (("A pointe 7-9 & 17-19",[7,8,9,17,18,19]),("B pointe 7-10 & 17-20",[7,8,9,10,17,18,19,20]),("C 8-9 & 17-18",[8,9,17,18]),("D 7-8 & 17-18",[7,8,17,18]),("E 8-9 & 17-19",[8,9,17,18,19])):
        for wk in("tous","semaine"):
            d=t[(t.hj.isin(pts))]
            if wk=="semaine": d=d[d.type_jour=="semaine"]
            a=d[d.il_pleut].ppc.mean(); b=d[~d.il_pleut].ppc.mean()
            print(f"  {name:24s} {wk:8s} sans {b:6.1f} avec {a:6.1f} écart {100*(a/b-1):5.1f} %")

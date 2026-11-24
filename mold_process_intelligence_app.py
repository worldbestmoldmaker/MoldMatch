"""FISBA Inspection Intelligence - Streamlit application.
Run with: streamlit run mold_process_intelligence_app.py
"""
from __future__ import annotations
import io
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="FISBA Inspection Intelligence", page_icon="🔬", layout="wide")

FISBA_COLUMNS = [
    "Login name","Sample ID","Sample name","Tray Pos","Cav","pass/fail","TempMeas",
    "Work Request","Subgroup","Molding Date","Molding Time","DateMeas","TimeMeas",
    "OT Insert ID","MID","Mold Design","Mold Type","RadiusSPH","NominalRad",
    "RadSPHDev","RadiusTOR","Toricity","NominalTori","ToriDev","Twist","PV",
    "DeltaR","Coma","C4 (c2,2)","C5 (s2,2)","C8 (4,0)","AnaMaskWidth","AnaMaskHeight"
]
METRICS = ["RadiusSPH","NominalRad","RadSPHDev","RadiusTOR","Toricity","NominalTori",
           "ToriDev","Twist","PV","DeltaR","Coma","C4 (c2,2)","C5 (s2,2)",
           "C8 (4,0)","AnaMaskWidth","AnaMaskHeight","TempMeas"]
DIMENSIONS = ["Cav","MID","OT Insert ID","Mold Design","Mold Type","Subgroup","Work Request","Sample name"]
COLOR_MAP = {"Pass":"#2F80ED", "Fail":"#D62728", "Incomplete Data":"#F2994A"}
RESULT_ORDER = ["Pass","Fail","Incomplete Data"]


def template_bytes():
    return (",".join('"'+c.replace('"','""')+'"' for c in FISBA_COLUMNS)+"\n").encode("utf-8-sig")


def demo_data(n=500, seed=7):
    rng=np.random.default_rng(seed)
    t=pd.date_range(pd.Timestamp.now().floor("min")-pd.Timedelta(minutes=n*5), periods=n, freq="5min")
    cav=rng.integers(1,9,n); mid=np.where(cav<=4,"MID-A","MID-B")
    delta=rng.normal(5.0,1.1,n)+(cav-4.5)*0.12
    pv=rng.normal(500,65,n)+np.maximum(delta-6,0)*25
    raddev=rng.normal(0,0.004,n)+(cav-4.5)*0.0004
    tor=rng.normal(0.004,0.002,n)
    fail=(np.abs(raddev)>0.010)|(pv>650)|(np.abs(delta)>8.0)|(np.abs(tor)>0.009)
    out=pd.DataFrame({
        "Login name":"DEMO_USER","Sample ID":[f"S-{i+1:05d}" for i in range(n)],"Sample name":"BC",
        "Tray Pos":np.arange(n)%20+1,"Cav":cav,"pass/fail":np.where(fail,"fail","pass"),
        "TempMeas":rng.normal(23,0.5,n),"Work Request":"WR-DEMO","Subgroup":np.where(np.arange(n)<n/2,"G1","G2"),
        "Molding Date":t.date.astype(str),"Molding Time":t.time.astype(str),"DateMeas":t.date.astype(str),"TimeMeas":t.time.astype(str),
        "OT Insert ID":[f"OT-{x:02d}" for x in cav],"MID":mid,"Mold Design":"Harmony","Mold Type":"PP_BC",
        "RadiusSPH":7.997+raddev,"NominalRad":7.997,"RadSPHDev":raddev,"RadiusTOR":7.997+raddev+tor,
        "Toricity":tor,"NominalTori":0,"ToriDev":tor,"Twist":rng.normal(0,0.15,n),"PV":pv,"DeltaR":delta,
        "Coma":rng.normal(50,9,n),"C4 (c2,2)":rng.normal(0,20,n),"C5 (s2,2)":rng.normal(100,25,n),
        "C8 (4,0)":rng.normal(-40,10,n),"AnaMaskWidth":5,"AnaMaskHeight":5
    })
    idx=rng.choice(n,max(5,n//40),replace=False)
    out.loc[idx,"DeltaR"]+=rng.choice([-1,1],len(idx))*rng.uniform(4,8,len(idx))
    return out


def read_csv_robust(file):
    raw=file.getvalue()
    for enc in ["utf-8-sig","utf-8","cp1252","latin1"]:
        for sep in [",",";","\t"]:
            try:
                df=pd.read_csv(io.BytesIO(raw),encoding=enc,sep=sep,engine="python")
                if len(df.columns)>5: return df
            except Exception: pass
    raise ValueError("Could not read the CSV. Export it with comma, semicolon, or tab delimiters.")


def normalize(df):
    out=df.copy(); out.columns=[str(c).strip() for c in out.columns]
    missing=[c for c in FISBA_COLUMNS if c not in out.columns]
    if missing: raise ValueError("Missing FISBA columns: "+", ".join(missing))
    out=out[FISBA_COLUMNS].copy()
    for c in METRICS:
        out[c]=pd.to_numeric(out[c].replace(["invalid","Invalid","INVALID",""],np.nan),errors="coerce")
    out["Cav"]=out["Cav"].astype(str).str.strip()
    result=out["pass/fail"].astype(str).str.strip().str.lower()
    out["Result"]=np.select([result.str.startswith("pass"),result.str.startswith("fail")],["Pass","Fail"],default="Incomplete Data")
    out["MoldingDateTime"]=pd.to_datetime(out["Molding Date"].astype(str)+" "+out["Molding Time"].astype(str),errors="coerce")
    out["MeasurementDateTime"]=pd.to_datetime(out["DateMeas"].astype(str)+" "+out["TimeMeas"].astype(str),errors="coerce")
    return out


def add_anomalies(df, cols):
    out=df.copy(); scores=[]
    for c in cols:
        x=out[c]; med=x.median(); mad=np.nanmedian(np.abs(x-med)); scale=max(1.4826*mad,x.std(ddof=0)*0.25,1e-12)
        z=np.abs(x-med)/scale; out[f"z_{c}"]=z; scores.append(z)
    out["Anomaly Score"]=pd.concat(scores,axis=1).max(axis=1) if scores else 0
    out["Anomaly"]=out["Anomaly Score"]>=3.5
    return out


def overview(df):
    known=df[df.Result.isin(["Pass","Fail"])]
    pass_rate=(known.Result=="Pass").mean() if len(known) else np.nan
    cols=st.columns(6)
    cols[0].metric("Inspections",f"{len(df):,}"); cols[1].metric("Pass rate","N/A" if pd.isna(pass_rate) else f"{pass_rate:.1%}")
    cols[2].metric("Average DeltaR",f"{df.DeltaR.mean():.3f}"); cols[3].metric("Average PV",f"{df.PV.mean():.2f}")
    cols[4].metric("Average radius deviation",f"{df.RadSPHDev.mean():.5f}"); cols[5].metric("Anomalies",f"{int(df.Anomaly.sum()):,}")
    a,b=st.columns([1.5,1])
    with a:
        metric=st.selectbox("Trend measurement",["DeltaR","PV","RadSPHDev","Toricity","Coma","C4 (c2,2)","C5 (s2,2)","C8 (4,0)"],key="trend")
        use_time=df.MeasurementDateTime.notna().any(); x="MeasurementDateTime" if use_time else df.index
        fig=px.scatter(df,x=x,y=metric,color="Result",color_discrete_map=COLOR_MAP,category_orders={"Result":RESULT_ORDER},hover_data=["Sample ID","Cav","MID","OT Insert ID","Anomaly Score"])
        anomalous=df[df["Anomaly"] & df[metric].notna()]
        if not anomalous.empty:
            ax=anomalous["MeasurementDateTime"] if use_time else anomalous.index
            fig.add_trace(go.Scatter(x=ax,y=anomalous[metric],mode="markers",name="Anomaly ◆",marker=dict(symbol="diamond-open",size=12,color="black",line=dict(width=2)),hovertext=anomalous["Sample ID"],hovertemplate="Anomaly ◆<br>Sample %{hovertext}<br>Value %{y}<extra></extra>"))
        fig.update_layout(title=f"{metric} inspection trend",legend_title_text="Inspection result")
        st.plotly_chart(fig,use_container_width=True)
    with b:
        counts=df.groupby(["Cav","Result"],as_index=False).size()
        fig=px.bar(counts,x="Cav",y="size",color="Result",barmode="stack",title="Inspection results by cavity",color_discrete_map=COLOR_MAP,category_orders={"Result":RESULT_ORDER})
        st.plotly_chart(fig,use_container_width=True)
    st.subheader("Cavity performance")
    summary=df.groupby("Cav",as_index=False).agg(Inspections=("Sample ID","size"),Pass_Rate=("Result",lambda x:(x=="Pass").mean()),DeltaR_Mean=("DeltaR","mean"),DeltaR_Std=("DeltaR","std"),PV_Mean=("PV","mean"),RadiusDev_Mean=("RadSPHDev","mean"),Anomaly_Rate=("Anomaly","mean"))
    st.dataframe(summary.style.format({"Pass_Rate":"{:.1%}","Anomaly_Rate":"{:.1%}","DeltaR_Mean":"{:.3f}","DeltaR_Std":"{:.3f}","PV_Mean":"{:.2f}","RadiusDev_Mean":"{:.5f}"}),use_container_width=True)
    if "Spec Failures" in df.columns:
        failed=df[df.Result.isin(["Fail","Incomplete Data"])][["Sample ID","Cav","MID","Result","Spec Failures","DeltaR","PV","RadSPHDev"]]
        if not failed.empty:
            st.subheader("Specification failures / incomplete records")
            st.dataframe(failed,use_container_width=True)


def measurement_analysis(df):
    st.subheader("Measurement analysis")
    c1,c2,c3=st.columns(3); metric=c1.selectbox("Measurement",[c for c in METRICS if c!="TempMeas"],index=9); group=c2.selectbox("Compare by",DIMENSIONS,index=0); chart=c3.selectbox("Chart",["Box plot","Violin plot","Histogram"])
    plot=df.dropna(subset=[metric])
    if chart=="Box plot": fig=px.box(plot,x=group,y=metric,color="Result",points="outliers",color_discrete_map=COLOR_MAP)
    elif chart=="Violin plot": fig=px.violin(plot,x=group,y=metric,color="Result",box=True,points="outliers",color_discrete_map=COLOR_MAP)
    else: fig=px.histogram(plot,x=metric,color="Result",marginal="box",barmode="overlay",color_discrete_map=COLOR_MAP)
    st.plotly_chart(fig,use_container_width=True)
    stats=plot.groupby(group)[metric].agg(["count","mean","std","min","median","max"]).reset_index(); st.dataframe(stats,use_container_width=True)
    st.subheader("Two-measurement relationship")
    a,b=st.columns(2); x=a.selectbox("X",METRICS,index=8,key="xmetric"); y=b.selectbox("Y",METRICS,index=9,key="ymetric")
    st.plotly_chart(px.scatter(df,x=x,y=y,color="Result",symbol="Cav",hover_data=["Sample ID","MID","OT Insert ID"],color_discrete_map=COLOR_MAP),use_container_width=True)


def pass_fail_drivers(df):
    st.subheader("Pass/fail measurement separation")
    st.caption("Uses the active calculated specification result when enabled; otherwise uses the original FISBA pass/fail field.")
    known=df[df.Result.isin(["Pass","Fail"])]
    rows=[]
    for c in METRICS:
        p=known.loc[known.Result=="Pass",c].dropna(); f=known.loc[known.Result=="Fail",c].dropna()
        if len(p)>=3 and len(f)>=3:
            pooled=max(known[c].std(ddof=0),1e-12); rows.append({"Measurement":c,"Pass mean":p.mean(),"Fail mean":f.mean(),"Separation score":abs(f.mean()-p.mean())/pooled,"Pass n":len(p),"Fail n":len(f)})
    drivers=pd.DataFrame(rows).sort_values("Separation score",ascending=False) if rows else pd.DataFrame()
    if drivers.empty: st.info("At least three pass and three fail measurements are required.")
    else:
        st.dataframe(drivers.style.format({"Pass mean":"{:.4g}","Fail mean":"{:.4g}","Separation score":"{:.2f}"}),use_container_width=True)
        top=drivers.iloc[0]; st.info(f"Largest observed pass/fail separation: {top['Measurement']} (standardized separation {top['Separation score']:.2f}). Correlation does not prove cause.")


def anomalies(df):
    st.subheader("Unusual inspection records"); cutoff=st.slider("Anomaly score threshold",2.0,8.0,3.5,0.1)
    bad=df[df["Anomaly Score"]>=cutoff].sort_values("Anomaly Score",ascending=False)
    cols=["Sample ID","MeasurementDateTime","Cav","MID","OT Insert ID","Result","Anomaly Score","DeltaR","PV","RadSPHDev","Toricity","Coma","C4 (c2,2)","C5 (s2,2)","C8 (4,0)"]
    st.dataframe(bad[cols],use_container_width=True); st.download_button("Download anomaly records",bad.to_csv(index=False).encode("utf-8-sig"),"fisba_anomalies.csv","text/csv")


def reports(df):
    st.subheader("Export")
    cavity=df.groupby("Cav",as_index=False).agg(Inspections=("Sample ID","size"),Pass_Rate=("Result",lambda x:(x=="Pass").mean()),DeltaR_Mean=("DeltaR","mean"),PV_Mean=("PV","mean"),RadiusDev_Mean=("RadSPHDev","mean"),Anomaly_Rate=("Anomaly","mean"))
    st.download_button("Download filtered FISBA data",df.to_csv(index=False).encode("utf-8-sig"),"fisba_filtered_data.csv","text/csv")
    st.download_button("Download cavity summary",cavity.to_csv(index=False).encode("utf-8-sig"),"fisba_cavity_summary.csv","text/csv")


def main():
    st.title("🔬 FISBA Inspection Intelligence"); st.caption("Analysis for your BC FISBA inspection export format: cavity, MID, radius, toricity, PV, DeltaR, Coma and Zernike terms.")
    with st.sidebar:
        st.header("FISBA data"); source=st.radio("Source",["Upload FISBA CSV","Demonstration data"])
        if source=="Upload FISBA CSV":
            up=st.file_uploader("Upload FISBA CSV",type=["csv","txt"]); st.download_button("Download blank FISBA template",template_bytes(),"FISBA_Inspection_Template.csv","text/csv")
            if up is None: st.info("Upload a FISBA CSV to begin."); st.stop()
            try: raw=read_csv_robust(up)
            except Exception as e: st.error(str(e)); st.stop()
        else: raw=demo_data(st.slider("Demo inspections",100,3000,500,100))
        try: data=normalize(raw)
        except Exception as e: st.error(str(e)); st.stop()
        available=[c for c in ["DeltaR","PV","RadSPHDev","Toricity","Coma","C4 (c2,2)","C5 (s2,2)","C8 (4,0)"] if data[c].notna().sum()>=5]
        data=add_anomalies(data,available)

        st.header("Pass/Fail Specifications"); st.caption("Change the limits below. The app immediately recalculates every inspection result.")
        use_specs=st.toggle("Use calculated Pass/Fail from specification limits",value=False,key="use_calculated_specs")
        spec_defaults={"DeltaR":(-10.0,10.0),"PV":(0.0,700.0),"RadSPHDev":(-0.010,0.010),"Toricity":(-0.010,0.010),"Coma":(-100.0,100.0),"C4 (c2,2)":(-100.0,100.0),"C5 (s2,2)":(-200.0,200.0),"C8 (4,0)":(-100.0,100.0)}
        enabled_specs={}
        if use_specs:
            for metric,(default_lsl,default_usl) in spec_defaults.items():
                enabled=st.checkbox(f"Use {metric}",value=(metric in ["DeltaR","PV","RadSPHDev"]),key=f"spec_enabled_{metric}")
                if enabled:
                    c1,c2=st.columns(2); lsl=c1.number_input(f"{metric} LSL",value=float(default_lsl),format="%.6f",key=f"spec_lsl_{metric}"); usl=c2.number_input(f"{metric} USL",value=float(default_usl),format="%.6f",key=f"spec_usl_{metric}")
                    if lsl>=usl: st.error(f"{metric}: LSL must be less than USL.")
                    else: enabled_specs[metric]=(lsl,usl)
            data["Original Result"]=data["Result"].copy()
            if enabled_specs:
                pass_mask=pd.Series(True,index=data.index,dtype=bool); complete_mask=pd.Series(True,index=data.index,dtype=bool); failure_lists=[[] for _ in range(len(data))]
                for metric,(lsl,usl) in enabled_specs.items():
                    measured=data[metric].notna(); within=data[metric].between(lsl,usl,inclusive="both")
                    complete_mask &= measured; pass_mask &= measured & within
                    for pos in np.flatnonzero((measured & ~within).to_numpy()): failure_lists[pos].append(f"{metric} outside [{lsl:g}, {usl:g}]")
                    for pos in np.flatnonzero((~measured).to_numpy()): failure_lists[pos].append(f"{metric} missing")
                data["Calculated Result"]=np.where(~complete_mask,"Incomplete Data",np.where(pass_mask,"Pass","Fail")); data["Spec Failures"]=[", ".join(x) for x in failure_lists]; data["Result"]=data["Calculated Result"]
                cp=int((data["Calculated Result"]=="Pass").sum()); cf=int((data["Calculated Result"]=="Fail").sum()); ci=int((data["Calculated Result"]=="Incomplete Data").sum()); op=int((data["Original Result"]=="Pass").sum())
                st.success(f"Calculated result is ACTIVE: {cp} Pass, {cf} Fail, {ci} Incomplete Data. Original file had {op} Pass.")
            else: st.warning("No valid specifications are enabled, so the original FISBA pass/fail result is still being used.")
        else: st.info("Result source: original FISBA pass/fail column.")

        st.header("Filters")
        cavities=sorted(data.Cav.dropna().unique().tolist()); chosen_cav=st.multiselect("Cavity",cavities,default=cavities)
        mids=sorted(data.MID.dropna().astype(str).unique().tolist()); chosen_mid=st.multiselect("MID",mids,default=mids)
        results=st.multiselect("Result",RESULT_ORDER,default=RESULT_ORDER)
        df=data[data.Cav.isin(chosen_cav)&data.MID.astype(str).isin(chosen_mid)&data.Result.isin(results)].copy()
        if df.empty: st.warning("No records match the selected filters."); st.stop()
        st.caption(f"{len(df):,} inspections selected")

    tabs=st.tabs(["Overview","Measurements","Pass/Fail Drivers","Anomalies","Export"])
    with tabs[0]: overview(df)
    with tabs[1]: measurement_analysis(df)
    with tabs[2]: pass_fail_drivers(df)
    with tabs[3]: anomalies(df)
    with tabs[4]: reports(df)
    st.divider(); st.caption("Decision-support analysis. Confirm specification limits and quality disposition using approved procedures.")

if __name__=="__main__": main()

#!/usr/bin/env python3
"""Reproduce the annual sensitivity summary for corridor-scale CEq.

Input (default: ../Data/Data_S3_CEq_Annual_Sensitivity.csv) contains one row
per year and nested corridor level. Outputs are written to ./outputs.
Required packages: numpy, pandas, matplotlib.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from Code_S1_Habitat_Robustness import WEIGHTS, metric_values

FONT_SETTINGS = {
    'font.family': 'serif',
    'font.serif': ['Times New Roman'],
    'font.size': 11,
    'axes.titlesize': 13,
    'axes.labelsize': 12,
    'xtick.labelsize': 10.5,
    'ytick.labelsize': 10.5,
    'legend.fontsize': 10.5,
    'mathtext.fontset': 'stix',
}

def sample_sd(x): return float(np.std(np.asarray(x,float),ddof=1))
def cv(x):
    a=np.asarray(x,float); return sample_sd(a)/a.mean()*100

def kendalls_w(rank_matrix):
    r=np.asarray(rank_matrix,float); m,n=r.shape; sums=r.sum(axis=0)
    s=np.sum((sums-sums.mean())**2); return float(12*s/(m*m*(n**3-n)))

def plot_threshold_panel(ax, areas):
    ids=np.array(sorted(areas.OBJECTID.unique()))
    by={(r.Scenario,int(r.OBJECTID)):np.array([r[f'S{i}_m2'] for i in range(1,6)],float)
        for _,r in areas.iterrows()}
    baseline=np.array([
        metric_values(by[('C0',i)],WEIGHTS['Linear_g1'])['STDHNLPI'] for i in ids
    ])
    alternatives=[]
    for scenario,color,label in [
        ('Cm20','tab:blue','Thresholds -20%'),
        ('Cp20','tab:orange','Thresholds +20%'),
    ]:
        alternative=np.array([
            metric_values(by[(scenario,i)],WEIGHTS['Linear_g1'])['STDHNLPI'] for i in ids
        ])
        alternatives.append(alternative)
        ax.scatter(baseline,alternative,s=38,color=color,label=label,zorder=3)

    upper=max(np.nanmax(baseline),*(np.nanmax(x) for x in alternatives))*1.08
    ax.plot([0,upper],[0,upper],'--',color='tab:blue',lw=1.4,label='1:1 line',zorder=2)
    ax.set_xlim(-0.03,upper)
    ax.set_ylim(-0.03,upper)
    ax.set_xlabel('Baseline STDHNLPI (C0)')
    ax.set_ylabel('Alternative-threshold STDHNLPI')
    ax.set_title('A. STDHNLPI threshold sensitivity',pad=8)
    ax.legend(loc='upper left',frameon=True)

def plot_annual_panel(ax, profiles):
    for year,row in profiles.iterrows():
        ax.plot([50,75,95],row.values,marker='o',ms=5.5,lw=1.7,label=str(year))
    ax.set_xticks([50,75,95],['50%','75%','95%'])
    ax.set_xlabel('Corridor percentile')
    ax.set_ylabel(r'Expected ALAN exposure, $CEq$ (nW cm$^{-2}$ sr$^{-1}$)')
    ax.set_title('B. Annual sensitivity of corridor-scale expected ALAN exposure',pad=8)
    ax.grid(True,color='#b0b0b0',alpha=0.3,lw=0.7)
    ax.legend(title='Annual composite',loc='upper right',frameon=True)

def main():
    ap=argparse.ArgumentParser(); here=Path(__file__).resolve().parent
    ap.add_argument('--input',type=Path,default=here.parent/'Data'/'Data_S3_CEq_Annual_Sensitivity.csv')
    ap.add_argument('--habitat-areas',type=Path,default=here.parent/'Data'/'Data_S1_Habitat_Class_Areas.csv')
    ap.add_argument('--output',type=Path,default=here/'outputs')
    args=ap.parse_args(); args.output.mkdir(parents=True,exist_ok=True)
    d=pd.read_csv(args.input)
    p=d.pivot(index='Year',columns='Corridor_percentile',values='CEq_nW_cm-2_sr-1').sort_index()
    summary=[]
    for c in (50,75,95):
        x=p[c].values; summary.append({'Corridor':c,'Mean_CEq':x.mean(),'SD_CEq':sample_sd(x),'CV_CEq_pct':cv(x),
                                      'Min_CEq':x.min(),'Max_CEq':x.max()})
    pd.DataFrame(summary).to_csv(args.output/'annual_summary.csv',index=False)
    grad=pd.DataFrame({'Year':p.index,'CEq_50':p[50].values,'CEq_75':p[75].values,'CEq_95':p[95].values})
    grad['Ratio_75_to_50']=grad.CEq_75/grad.CEq_50; grad['Ratio_95_to_50']=grad.CEq_95/grad.CEq_50
    grad['Drop_75_vs_50_pct']=(grad.Ratio_75_to_50-1)*100; grad['Drop_95_vs_50_pct']=(grad.Ratio_95_to_50-1)*100
    grad['Ordering']='50 > 75 > 95'; grad.to_csv(args.output/'corridor_gradient.csv',index=False)
    ranks=np.tile(np.array([3,2,1],float),(len(p),1)); w=kendalls_w(ranks)
    (args.output/'summary.txt').write_text(f"Kendall's W = {w:.3f}\n",encoding='utf-8')
    plt.figure(figsize=(7,5))
    for y,row in p.iterrows(): plt.plot([50,75,95],row.values,marker='o',label=str(y))
    plt.xticks([50,75,95],['50%','75%','95%']); plt.xlabel('Corridor percentile'); plt.ylabel('CEq (nW cm$^{-2}$ sr$^{-1}$)')
    plt.legend(title='Annual composite'); plt.tight_layout(); plt.savefig(args.output/'annual_CEq_profiles.png',dpi=300); plt.close()
    plt.figure(figsize=(7,5))
    for y,row in p.iterrows(): plt.plot([50,75,95],row.values/row.loc[50],marker='o',label=str(y))
    plt.xticks([50,75,95],['50%','75%','95%']); plt.xlabel('Corridor percentile'); plt.ylabel('CEq relative to 50% core corridor')
    plt.legend(title='Annual composite'); plt.tight_layout(); plt.savefig(args.output/'normalized_CEq_profiles.png',dpi=300); plt.close()

    # Publication-ready horizontal combination of the two sensitivity plots.
    areas=pd.read_csv(args.habitat_areas)
    with plt.rc_context(FONT_SETTINGS):
        fig,axes=plt.subplots(1,2,figsize=(14,5.4),constrained_layout=True)
        plot_threshold_panel(axes[0],areas)
        plot_annual_panel(axes[1],p)
        fig.savefig(args.output/'combined_sensitivity_panels.png',dpi=500,
                    bbox_inches='tight',facecolor='white')
        plt.close(fig)

if __name__=='__main__': main()

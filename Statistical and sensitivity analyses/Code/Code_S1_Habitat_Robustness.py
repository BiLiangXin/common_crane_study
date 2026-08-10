#!/usr/bin/env python3
"""Reproduce habitat-level ALAN threshold and score sensitivity analyses.

Inputs (default: ../Data):
  Data_S1_Habitat_Class_Areas.csv
  Data_S2_Habitat_Exposure_Metrics.csv

Outputs are written to ./outputs unless --output is supplied.
Required packages: numpy, pandas, scipy, matplotlib.
"""
from __future__ import annotations
import argparse, itertools, math
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import rankdata, spearmanr, kendalltau

WEIGHTS = {
    'Concave_g0.5': np.array([0.0, 0.5, np.sqrt(0.5), np.sqrt(0.75), 1.0]),
    'Linear_g1': np.array([0.0, 0.25, 0.50, 0.75, 1.0]),
    'Convex_g2': np.array([0.0, 0.0625, 0.25, 0.5625, 1.0]),
}
SCENARIOS = ['Cm20', 'C0', 'Cp20']

def metric_values(s, w):
    s = np.asarray(s, dtype=float)
    area = s.sum(); alit = s[1:].sum(); weighted = float(np.dot(s, w))
    return {
        'PCR': alit / area,
        'STDHNLPI': weighted / area,
        'ELS': weighted / alit if alit > 0 else np.nan,
        'HER': (s[3] + s[4]) / area,
    }

def ranks_desc(x):
    return rankdata(-np.asarray(x, dtype=float), method='average')

def agreement(base, alt, ids, k=5):
    base = np.asarray(base, float); alt = np.asarray(alt, float); ids = np.asarray(ids)
    keep = np.isfinite(base) & np.isfinite(alt)
    b, a, i = base[keep], alt[keep], ids[keep]
    rho = spearmanr(b, a).statistic
    rb, ra = ranks_desc(b), ranks_desc(a)
    top_b = set(i[np.argsort(-b)[:k]]); top_a = set(i[np.argsort(-a)[:k]])
    return {
        'N': len(b), 'Spearman_rho': rho,
        'Max_rank_shift': float(np.max(np.abs(rb-ra))),
        'Top5_overlap': len(top_b & top_a),
        'Mean_abs_diff': float(np.mean(np.abs(a-b))),
        'Max_abs_diff': float(np.max(np.abs(a-b))),
    }

def exact_label_permutation(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    z = np.concatenate([x, y]); n1 = len(x); n2 = len(y); n = len(z)
    ranks = rankdata(z, method='average')
    obs_u = ranks[:n1].sum() - n1*(n1+1)/2
    center = n1*n2/2
    extreme = 0; total = 0
    for comb in itertools.combinations(range(n), n1):
        u = ranks[list(comb)].sum() - n1*(n1+1)/2
        if abs(u-center) >= abs(obs_u-center) - 1e-12:
            extreme += 1
        total += 1
    p = extreme/total
    rrb = 2*obs_u/(n1*n2)-1
    return obs_u, p, rrb, total

def bh_adjust(pvals):
    p = np.asarray(pvals, float); n=len(p); order=np.argsort(p); out=np.empty(n)
    prev=1.0
    for j in range(n-1, -1, -1):
        idx=order[j]; val=min(prev, p[idx]*n/(j+1)); out[idx]=val; prev=val
    return out

def main():
    ap=argparse.ArgumentParser()
    here=Path(__file__).resolve().parent
    ap.add_argument('--data', type=Path, default=here.parent/'Data')
    ap.add_argument('--output', type=Path, default=here/'outputs')
    args=ap.parse_args(); args.output.mkdir(parents=True, exist_ok=True)
    areas=pd.read_csv(args.data/'Data_S1_Habitat_Class_Areas.csv')
    metrics=pd.read_csv(args.data/'Data_S2_Habitat_Exposure_Metrics.csv')
    ids=np.array(sorted(areas.OBJECTID.unique()))
    by={(r.Scenario,int(r.OBJECTID)):np.array([r[f'S{i}_m2'] for i in range(1,6)],float) for _,r in areas.iterrows()}
    base={m:np.array([metric_values(by[('C0',i)],WEIGHTS['Linear_g1'])[m] for i in ids]) for m in ('PCR','STDHNLPI','ELS','HER')}

    # Threshold sensitivity
    rows=[]
    for metric in base:
        for sc in ('Cm20','Cp20'):
            alt=np.array([metric_values(by[(sc,i)],WEIGHTS['Linear_g1'])[metric] for i in ids])
            rows.append({'Metric':metric,'Alternative':sc,**agreement(base[metric],alt,ids)})
    pd.DataFrame(rows).to_csv(args.output/'threshold_sensitivity.csv',index=False)

    # Weight sensitivity and 3x3 deterministic scenarios
    rows=[]
    for sc in SCENARIOS:
        for name,w in WEIGHTS.items():
            alt=np.array([metric_values(by[(sc,i)],w)['STDHNLPI'] for i in ids])
            rows.append({'Threshold':sc,'Weight_scheme':name,**agreement(base['STDHNLPI'],alt,ids)})
    pd.DataFrame(rows).to_csv(args.output/'joint_threshold_score_sensitivity.csv',index=False)

    # Exact key-versus-temporary comparisons under each threshold (linear scores)
    event=metrics.set_index('OBJECTID')['event_type_en'].to_dict()
    rows=[]
    for sc in SCENARIOS:
        for metric in ('PCR','STDHNLPI','ELS','HER'):
            vals={i:metric_values(by[(sc,i)],WEIGHTS['Linear_g1'])[metric] for i in ids}
            x=[vals[i] for i in ids if event[i]=='Key stopover' and np.isfinite(vals[i])]
            y=[vals[i] for i in ids if event[i]=='Temporary stopover' and np.isfinite(vals[i])]
            u,p,r,nperm=exact_label_permutation(x,y)
            rows.append({'Scenario':sc,'Metric':metric,'N_key':len(x),'N_temp':len(y),
                         'Median_key':np.median(x),'Median_temp':np.median(y),
                         'U_key':u,'Exact_perm_p':p,'Rank_biserial':r,'N_permutations':nperm})
    g=pd.DataFrame(rows)
    mask=g.Scenario.eq('C0'); g.loc[mask,'BH_q_baseline4']=bh_adjust(g.loc[mask,'Exact_perm_p'].values)
    g.to_csv(args.output/'group_comparisons_thresholds.csv',index=False)

    # Internal convergence
    c0=metrics.copy()
    comparisons=[
        ('STDHNLPI vs MeanRadiance','STDHNLPI_C0','MeanRadiance'),
        ('ELS vs MeanExposed','ELS_C0','MeanExposed'),
        ('HER vs P90','HER_C0','P90'),
        ('HER vs P95','HER_C0','P95'),
    ]
    rows=[]
    for name,a,b in comparisons:
        q=c0[[a,b]].dropna(); rows.append({'Comparison':name,'N':len(q),'Spearman_rho':spearmanr(q[a],q[b]).statistic,
                                            'Kendall_tau_b':kendalltau(q[a],q[b]).statistic})
    pd.DataFrame(rows).to_csv(args.output/'internal_convergence.csv',index=False)

    # Main threshold sensitivity figure
    plt.figure(figsize=(6.8,5.4))
    for sc,mark in [('Cm20','o'),('Cp20','s')]:
        alt=np.array([metric_values(by[(sc,i)],WEIGHTS['Linear_g1'])['STDHNLPI'] for i in ids])
        plt.scatter(base['STDHNLPI'],alt,label=sc,marker=mark)
    lim=max(np.nanmax(base['STDHNLPI']),0.55); plt.plot([0,lim],[0,lim],'--',lw=1)
    plt.xlabel('Baseline STDHNLPI'); plt.ylabel('Alternative STDHNLPI'); plt.legend(); plt.tight_layout()
    plt.savefig(args.output/'STDHNLPI_threshold_sensitivity.png',dpi=300); plt.close()

if __name__=='__main__':
    main()

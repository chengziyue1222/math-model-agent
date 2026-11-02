"""2021B: grouped prediction, within-support decisions and five new experiments."""
from __future__ import annotations

from pathlib import Path
import re

import numpy as np
import pandas as pd
from numpy.polynomial import Polynomial
from scipy.interpolate import PchipInterpolator
from scipy.optimize import least_squares
from scipy.special import expit, logit
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler


FEATURES = ['temperature_c','co_wt_percent','silica_mg','hap_mg','flow_ml_min','packing_ii','quartz']


def load_data(path):
    raw = pd.read_excel(path).iloc[:, :10]
    raw.iloc[:, :2] = raw.iloc[:, :2].ffill()
    records=[]
    for row in raw.itertuples(index=False,name=None):
        group, description, temperature, conversion, _, selectivity, *_ = row
        if pd.isna(temperature):
            continue
        values = re.search(r'(\d+(?:\.\d+)?)mg\s*(\d+(?:\.\d+)?)wt%',str(description))
        hap = re.search(r'(\d+(?:\.\d+)?)mg\s*HAP',str(description))
        flow = re.search(r'浓度\s*(\d+(?:\.\d+)?)\s*ml/min',str(description))
        if values is None or flow is None:
            raise ValueError(f'unparsed catalyst description: {description}')
        records.append({'group':group,'description':description,'temperature_c':float(temperature),
                        'conversion_percent':float(conversion),'selectivity_percent':float(selectivity),
                        'yield_percent':float(conversion*selectivity/100),
                        'co_wt_percent':float(values[2]),'silica_mg':float(values[1]),
                        'hap_mg':float(hap[1]) if hap else 0.,'flow_ml_min':float(flow[1]),
                        'packing_ii':float(str(group).startswith('B')),'quartz':float('石英砂' in str(description))})
    frame=pd.DataFrame(records)
    if len(frame)!=114 or frame.group.nunique()!=21 or frame[FEATURES].isna().any().any():
        raise ValueError('unexpected original attachment schema or observation count')
    return frame


def model(kind,alpha):
    degree=2 if kind=='interactions' else 1
    return make_pipeline(StandardScaler(),PolynomialFeatures(degree,include_bias=False),
                         StandardScaler(),Ridge(alpha=alpha))


def metric(actual,predicted):
    return {'mae_percentage_points':np.mean(np.abs(actual-predicted),axis=0).tolist(),
            'rmse_percentage_points':np.sqrt(np.mean((actual-predicted)**2,axis=0)).tolist()}


def bounded_pchip_optimum(part,upper=None):
    """All real stationary points of the piecewise degree-six yield polynomial."""
    x=part.temperature_c.to_numpy()
    a=PchipInterpolator(x,part.conversion_percent.to_numpy())
    b=PchipInterpolator(x,part.selectivity_percent.to_numpy())
    candidates=[]
    for i in range(len(x)-1):
        width=x[i+1]-x[i]
        if upper is not None:
            width=min(width,upper-x[i])
        if width<0:
            continue
        poly=Polynomial(a.c[:,i][::-1])*Polynomial(b.c[:,i][::-1])/100
        points=[0.,width]
        points += [float(z.real) for z in poly.deriv().roots() if abs(z.imag)<1e-7 and 0<z.real<width]
        candidates += [(float(poly(z)),float(x[i]+z)) for z in points]
    if not candidates:
        return None
    value,temperature=max(candidates)
    return {'group':str(part.group.iloc[0]),'temperature_c':temperature,'predicted_yield_percent':value,
            'temperature_support_c':[float(x[0]),float(x[-1])],
            'scope':'maximum of the within-catalyst PCHIP surrogate on its observed temperature support'}


def solve(root: Path):
    frame=load_data(root/'inputs/附件1.xlsx')
    frame.to_csv(root/'observations.csv',index=False)
    x=frame[FEATURES].to_numpy(float)
    y=frame[['conversion_percent','selectivity_percent']].to_numpy(float)
    target=logit(np.clip(y/100,1e-5,1-1e-5))
    # Fixed before evaluation: different catalysts and hot operating conditions.
    held_groups=['A4','A9','B2','B6']
    group_test=frame.group.isin(held_groups).to_numpy()
    hot_test=(frame.temperature_c.to_numpy()>=400)&~group_test
    development=~(group_test|hot_test)
    groups=frame.group.to_numpy()
    candidates=[]
    cv=GroupKFold(4)
    indices=np.flatnonzero(development)
    for kind in ['temperature-only','additive','interactions']:
        selected=[0] if kind=='temperature-only' else list(range(len(FEATURES)))
        for alpha in [.1,1.,10.,100.]:
            scores=[]
            for train,val in cv.split(x[indices],target[indices],groups[indices]):
                fitted=model(kind,alpha).fit(x[indices[train]][:,selected],target[indices[train]])
                predicted=100*expit(fitted.predict(x[indices[val]][:,selected]))
                scores.append(float(np.mean(np.abs(y[indices[val]]-predicted))))
            candidates.append({'kind':kind,'alpha':alpha,'group_cv_mae':float(np.mean(scores)),
                               'fold_mae':scores,'columns':selected})
    best=min(candidates,key=lambda r:r['group_cv_mae'])
    fitted=model(best['kind'],best['alpha']).fit(x[development][:,best['columns']],target[development])
    predictions=100*expit(fitted.predict(x[:,best['columns']]))
    baseline_candidate=min((v for v in candidates if v['kind']=='temperature-only'),key=lambda r:r['group_cv_mae'])
    baseline=model('temperature-only',baseline_candidate['alpha']).fit(x[development][:,[0]],target[development])
    base_predictions=100*expit(baseline.predict(x[:,[0]]))
    ablation_candidate=min((v for v in candidates if v['kind']=='additive'),key=lambda r:r['group_cv_mae'])
    ablated=model('additive',ablation_candidate['alpha']).fit(x[development],target[development])
    ablation_prediction=100*expit(ablated.predict(x))
    tests={}
    for name,mask in [('unseen-catalysts',group_test),('temperature-extrapolation',hot_test)]:
        tests[name]={'rows':int(mask.sum()),'groups':sorted(set(groups[mask])),
                     'model':metric(y[mask],predictions[mask]),'temperature_baseline':metric(y[mask],base_predictions[mask]),
                     'no-interactions':metric(y[mask],ablation_prediction[mask])}
    report=frame[['group','temperature_c','conversion_percent','selectivity_percent']].copy()
    report['split']=np.where(group_test,'unseen-catalysts',np.where(hot_test,'temperature-extrapolation','development'))
    for i,name in enumerate(['conversion','selectivity']):
        report[name+'_prediction']=predictions[:,i]
        report[name+'_temperature_baseline']=base_predictions[:,i]
        report[name+'_no_interactions']=ablation_prediction[:,i]
    report.to_csv(root/'predictions.csv',index=False)
    group_fits=[]
    for group,part in frame.groupby('group',sort=False):
        xx=part.temperature_c.to_numpy();z=(xx-xx.mean())/50
        item={'group':group,'n':len(part),'temperature_support_c':[float(xx.min()),float(xx.max())]}
        for label in ['conversion_percent','selectivity_percent']:
            yy=part[label].to_numpy()
            losses=[]
            for degree in [1,2]:
                errors=[]
                for j in range(len(part)):
                    keep=np.arange(len(part))!=j
                    coefficients=np.polynomial.polynomial.polyfit(z[keep],yy[keep],degree)
                    errors.append(float(np.polynomial.polynomial.polyval(z[j],coefficients)-yy[j]))
                losses.append((float(np.mean(np.abs(errors))),degree))
            loss,degree=min(losses)
            item[label]={'degree':degree,'leave_one_temperature_out_mae':loss,
                         'center_temperature_c':float(xx.mean()),'scale_c':50.,
                         'coefficients':np.polynomial.polynomial.polyfit(z,yy,degree).tolist(),
                         'pearson_temperature_correlation':float(np.corrcoef(xx,yy)[0,1])}
        group_fits.append(item)
    stability=pd.read_excel(root/'inputs/附件2.xlsx',header=None).iloc[3:,[0,1,3]].dropna().to_numpy(float)
    tt,conversion,selectivity=stability.T
    def decay(p,t):
        return p[0]+p[1]*np.exp(-p[2]*t)
    calibration=least_squares(lambda p:decay(p,tt[:-2])-conversion[:-2],[20,30,.005],bounds=([0,0,0],[100,100,1]))
    time_prediction=decay(calibration.x,tt)
    pd.DataFrame({'time_min':tt,'conversion_percent':conversion,'selectivity_percent':selectivity,
                  'yield_percent':conversion*selectivity/100,'conversion_prediction':time_prediction,
                  'split':['calibration']*(len(tt)-2)+['time-holdout']*2}).to_csv(root/'stability.csv',index=False)
    # Q2 model effects are predictive associations under a confounded design.
    final=model(best['kind'],best['alpha']).fit(x[:,best['columns']],target)
    reference=np.median(x,axis=0)
    effects=[]
    for i,name in enumerate(FEATURES):
        lo,hi=np.quantile(x[:,i],[.1,.9]);points=np.tile(reference,(2,1));points[:,i]=[lo,hi]
        response=100*expit(final.predict(points[:,best['columns']]))
        effects.append({'feature':name,'low':float(lo),'high':float(hi),'predicted_difference_percentage_points':(response[1]-response[0]).tolist(),
                        'interpretation':'exploratory model association; may combine unsupported factor settings; not causal'})
    unrestricted=[];cool=[]
    for _,part in frame.groupby('group',sort=False):
        part=part.sort_values('temperature_c')
        unrestricted.append(bounded_pchip_optimum(part))
        cool.append(bounded_pchip_optimum(part,upper=350-1e-6))
    best_all=max(unrestricted,key=lambda z:z['predicted_yield_percent'])
    best_cool=max((v for v in cool if v is not None),key=lambda z:z['predicted_yield_percent'])
    # Independent dense verification of the piecewise polynomial maximization.
    dense_errors=[]
    for group,part in frame.groupby('group',sort=False):
        part=part.sort_values('temperature_c')
        grid=np.linspace(part.temperature_c.min(),part.temperature_c.max(),2001)
        val=PchipInterpolator(part.temperature_c,part.conversion_percent)(grid)*PchipInterpolator(part.temperature_c,part.selectivity_percent)(grid)/100
        exact=next(z for z in unrestricted if z['group']==group)
        dense_errors.append(float(exact['predicted_yield_percent']-val.max()))
    # Sequential ridge-D-optimal information gain within observed factor support.
    proposals=[]
    for group,part in frame.groupby('group',sort=False):
        row=part.iloc[0]
        for t in np.arange(part.temperature_c.min()+5,part.temperature_c.max(),5):
            if np.min(np.abs(part.temperature_c-t))<1:
                continue
            features=row[FEATURES].to_numpy(float);features[0]=t
            proposals.append((str(group),float(t),features))
    candidate_x=np.array([v[2] for v in proposals])
    design=final[:-1].transform(x[:,best['columns']]);candidate_design=final[:-1].transform(candidate_x[:,best['columns']])
    inverse=np.linalg.pinv(design.T@design+best['alpha']*np.eye(design.shape[1]))
    chosen=[];available=np.ones(len(proposals),bool)
    for _ in range(5):
        leverage=np.einsum('ij,jk,ik->i',candidate_design,inverse,candidate_design)
        leverage[~available]=-np.inf
        j=int(np.argmax(leverage));vector=candidate_design[j];update=inverse@vector
        inverse-=np.outer(update,update)/(1+leverage[j]);available[j]=False
        response=100*expit(final.predict(candidate_x[j:j+1,best['columns']]))[0]
        chosen.append({'group':proposals[j][0],'temperature_c':proposals[j][1],
                       'predicted_conversion_percent':float(response[0]),'predicted_selectivity_percent':float(response[1]),
                       'log_determinant_gain':float(np.log1p(leverage[j])),
                       'status':'PROPOSED_NOT_OBSERVED','reason':'largest remaining regularized design-information gain; one-step covariance update'})
    pd.DataFrame(chosen).to_csv(root/'five_proposed_experiments.csv',index=False)
    observed_best=frame.loc[frame.yield_percent.idxmax()]
    cool_rows=frame[frame.temperature_c<350]
    cool_observed=cool_rows.loc[cool_rows.yield_percent.idxmax()]
    return {'case_id':'cumcm-2021-b','status':'PASS','synthetic':False,'rows':len(frame),'catalysts':frame.group.nunique(),
            'selection':best,'selection_candidates':candidates,'tests':tests,
            'partition':{'development_rows':int(development.sum()),'heldout_groups':held_groups,'temperature_extrapolation_min_c':400,
                         'selection_uses_final_tests':False,'decision_refit':'all observations after the frozen tests; test metrics belong to the development fit'},
            'questions':{'Q1':{'per_catalyst':group_fits,'stability_decay_parameters':calibration.x.tolist(),
                               'stability_time_holdout_mae':float(np.mean(np.abs(time_prediction[-2:]-conversion[-2:]))),
                               'stability_selectivity_range':[float(selectivity.min()),float(selectivity.max())]},
                         'Q2':{'associations':effects,'causal_identification':False,'quartz_catalyst_A11_retained':True},
                         'Q3':{'within_observed_catalog':best_all,'strictly_below_350_c':best_cool,
                               'observed_best':{'group':str(observed_best.group),'temperature_c':float(observed_best.temperature_c),'yield_percent':float(observed_best.yield_percent)},
                               'observed_below_350_best':{'group':str(cool_observed.group),'temperature_c':float(cool_observed.temperature_c),'yield_percent':float(cool_observed.yield_percent)},
                               'all_catalog_optima':unrestricted,'dense_grid_maximum_shortfall':max(dense_errors)},
                         'Q4':{'experiments':chosen,'completed_experiments':0}},
            'limitations':['Temperature and catalyst effects are confounded; predictive associations are not intervention effects.',
                           'The single time series is one catalyst experiment, not seven independent experiments.',
                           'The decision searches only studied catalyst combinations and within their measured temperature range.',
                           'New physical experiments are required to validate the proposed optimum and proposed design.']}

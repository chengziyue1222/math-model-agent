"""2020A: calibrate an effective thermal model and answer all four questions.

The single measured trace supports interpolation checks, not empirical
validation of the new setpoints. Parameters describe effective heat transfer.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import brentq, least_squares, minimize
from scipy.signal import lfilter

from algorithms.research_validation import identifiability_diagnostics


LENGTH = 435.5  # cm, 25 + 11*30.5 + 10*5 + 25
DEFAULT = np.array([175., 195., 235., 255.])


def curve(parameters, settings, speed, *, dx=.25):
    """Exact first-order update for each linearly interpolated ambient segment."""
    parameters = np.asarray(parameters, float)
    if len(parameters) == 2:
        taus, entrance_power = np.repeat(parameters[0], 5), parameters[1]
    else:
        taus, entrance_power = parameters[:5], parameters[5]
    x = np.linspace(0, LENGTH, int(np.ceil(LENGTH/dx))+1)
    time = x/(speed/60)
    starts = 25 + np.arange(11)*35.5
    ends = starts + 30.5
    zone = np.r_[np.repeat(settings[0], 5), settings[1:3], np.repeat(settings[3], 2), [25, 25]]
    knots = np.r_[0., np.column_stack([starts, ends]).ravel(), LENGTH]
    air = np.interp(x, knots, np.r_[25., np.repeat(zone, 2), 25.])
    entry = x <= 25
    air[entry] = 25 + (settings[0]-25)*(x[entry]/25)**entrance_power
    regimes = np.searchsorted([ends[4], ends[5], ends[6], ends[8]], (x[:-1]+x[1:])/2)
    dt = time[1]-time[0]
    temperature = np.empty_like(x); temperature[0] = 25
    for regime in range(5):
        indices = np.flatnonzero(regimes == regime)
        if not len(indices):
            continue
        tau = taus[regime]
        decay = np.exp(-dt/tau)
        slope = np.diff(air)[indices]/dt
        forcing = (1-decay)*air[indices] + slope*(dt-tau*(1-decay))
        first = indices[0]
        temperature[indices+1], _ = lfilter([1], [1, -decay], forcing,
                                          zi=[decay*temperature[first]])
    return time, temperature, air


def process_metrics(time, temperature):
    peak = int(np.argmax(temperature))
    def crossing(level, rising=True):
        xx, yy = (time[:peak+1], temperature[:peak+1]) if rising else (time[peak:], temperature[peak:])
        hits = np.flatnonzero((yy[:-1]-level)*(yy[1:]-level) <= 0)
        if not len(hits):
            return None
        i = hits[0]
        return float(xx[i]+(level-yy[i])*(xx[i+1]-xx[i])/(yy[i+1]-yy[i]))
    low, high = crossing(150), crossing(190)
    left, right = crossing(217), crossing(217, False)
    slope = np.diff(temperature)/np.diff(time)
    area = 0.0
    symmetry = None
    if left is not None:
        t = np.r_[left, time[(time > left)&(time <= time[peak])]]
        area = float(np.trapezoid(np.maximum(np.interp(t,time,temperature)-217, 0), t))
    if left is not None and right is not None:
        extent = max(time[peak]-left, right-time[peak])
        delta = np.linspace(0, extent, 600)
        lhs = np.maximum(np.interp(time[peak]-delta,time,temperature)-217, 0)
        rhs = np.maximum(np.interp(time[peak]+delta,time,temperature)-217, 0)
        symmetry = float(np.trapezoid(np.abs(lhs-rhs), delta))
    return {"peak_c": float(temperature[peak]), "peak_time_s": float(time[peak]),
            "rising_150_190_s": None if low is None or high is None else high-low,
            "above_217_s": None if left is None or right is None else right-left,
            "max_heating_c_per_s": float(slope.max()), "max_cooling_c_per_s": float(-slope.min()),
            "rising_area_c_s": area, "symmetry_difference_area_c_s": symmetry}


def margins(metrics):
    warm = metrics['rising_150_190_s']; hot = metrics['above_217_s']
    if warm is None or hot is None:
        return np.full(8, -100.)
    return np.array([3-metrics['max_heating_c_per_s'], 3-metrics['max_cooling_c_per_s'],
                     (warm-60)/10, (120-warm)/10, (hot-40)/10, (90-hot)/10,
                     (metrics['peak_c']-240)/5, (250-metrics['peak_c'])/5])


def solve(root: Path):
    data = pd.read_excel(root/'inputs/附件.xlsx').iloc[:, :2].to_numpy(float)
    observed_time, observed = data.T
    # Blocked interpolation on a single curve. This is not an independent run.
    holdout = np.zeros(len(data), bool)
    for lo, hi in [(80, 100), (180, 200), (240, 260), (305, 325)]:
        holdout |= (observed_time >= lo)&(observed_time < hi)
    train = ~holdout
    def residual(p):
        time, predicted, _ = curve(p, DEFAULT, 70)
        return (np.interp(observed_time,time,predicted)-observed)[train]
    baseline = least_squares(residual, [40., 3.], bounds=([1., .2], [300., 15.]), max_nfev=250)
    fitted = least_squares(residual, [45., 35., 35., 45., 60., 3.],
                           bounds=([1]*5+[.2], [300]*5+[15]), max_nfev=350, diff_step=1e-4)
    parameters = fitted.x
    time, predicted, _ = curve(parameters, DEFAULT, 70)
    prediction = np.interp(observed_time,time,predicted)
    bt, by, _ = curve(baseline.x, DEFAULT, 70)
    baseline_pred = np.interp(observed_time,bt,by)
    pd.DataFrame({'time_s': observed_time, 'observed_c': observed, 'model_c': prediction,
                  'baseline_c': baseline_pred, 'split': np.where(holdout,'blocked-holdout','calibration')}).to_csv(root/'calibration.csv',index=False)
    errors = {name: {'rmse_c': float(np.sqrt(np.mean((value[holdout]-observed[holdout])**2))),
                     'mae_c': float(np.mean(np.abs(value[holdout]-observed[holdout])))}
              for name,value in [('model',prediction),('baseline',baseline_pred)]}
    q1_settings = [173,198,230,257]
    q1_time, q1_temp, _ = curve(parameters,q1_settings,78)
    stamps = np.arange(0,q1_time[-1]+1e-8,.5)
    pd.DataFrame({'time_s': stamps,'temperature_c': np.interp(stamps,q1_time,q1_temp)}).to_csv(root/'result.csv',index=False)
    points = [25+2*35.5+15.25,25+5*35.5+15.25,25+6*35.5+15.25,25+7*35.5+30.5]
    q1 = {'settings_c':q1_settings,'speed_cm_min':78,'named_positions_cm':points,
          'named_temperatures_c':np.interp(np.array(points)/(78/60),q1_time,q1_temp).tolist(),
          'output':'result.csv','metrics':process_metrics(q1_time,q1_temp)}
    q2_settings = [182,203,237,254]
    def q2_slack(speed):
        t,y,_ = curve(parameters,q2_settings,speed)
        return float(margins(process_metrics(t,y)).min())
    speed_grid = np.linspace(65,100,351)
    slack = np.array([q2_slack(v) for v in speed_grid])
    pd.DataFrame({'speed_cm_min':speed_grid,'minimum_normalized_margin':slack}).to_csv(root/'q2_speed_scan.csv',index=False)
    intervals=[]
    for i in range(len(speed_grid)-1):
        if slack[i]*slack[i+1] < 0:
            intervals.append(float(brentq(q2_slack,speed_grid[i],speed_grid[i+1],xtol=1e-8)))
    feasible = [float(v) for v,s in zip(speed_grid,slack) if s>=0]
    feasible += [v for v in intervals if q2_slack(v)>-1e-6]
    maximum = max(feasible) if feasible else None
    q2 = {'settings_c':q2_settings,'maximum_speed_cm_min':maximum,'boundary_candidates':intervals,
          'search_resolution_cm_min':.1,'scope':'largest feasible boundary located by the saved scan; no monotonicity assumed'}
    bounds = [(165,185),(185,205),(225,245),(245,265),(65,100)]
    history=[]
    def metrics(z,dx=.25):
        t,y,_=curve(parameters,z[:4],z[4],dx=dx)
        return process_metrics(t,y)
    starts = [[175,195,235,255,78],[182,203,237,254,78],[180,190,230,255,75],[170,200,240,260,85]]
    rng=np.random.default_rng(20201102)
    starts += [rng.uniform(np.array(bounds)[:,0],np.array(bounds)[:,1]).tolist() for _ in range(8)]
    def optimize(objective, extra=None):
        candidates=[]
        constraints=[{'type':'ineq','fun':lambda z: margins(metrics(z))}]
        if extra is not None:
            constraints.append({'type':'ineq','fun':extra})
        for initial in starts:
            result=minimize(objective,initial,method='SLSQP',bounds=bounds,constraints=constraints,
                            options={'maxiter':180,'ftol':1e-8,'eps':1e-3})
            measure=metrics(result.x)
            admissible=bool(margins(measure).min()>=-2e-4 and (extra is None or extra(result.x)>=-2e-4))
            history.append({'success':bool(result.success),'message':str(result.message),'x':result.x.tolist(),
                            'feasible':admissible,'objective':float(objective(result.x))})
            if admissible:
                candidates.append((float(objective(result.x)),result.x,measure))
        return min(candidates,key=lambda item:item[0]) if candidates else None
    area_best=optimize(lambda z:metrics(z)['rising_area_c_s']/1000)
    if area_best is None:
        raise RuntimeError('No feasible Q3 design; inspect model assumptions rather than weakening process limits')
    area_limit=1.05*area_best[2]['rising_area_c_s']
    starts.insert(0,area_best[1].tolist())
    symmetry_best=optimize(lambda z:(metrics(z)['symmetry_difference_area_c_s'] or 1e6)/1000,
                           extra=lambda z:(area_limit-metrics(z)['rising_area_c_s'])/1000)
    if symmetry_best is None:
        raise RuntimeError('No feasible Q4 design under the declared 5% area budget')
    designs={}
    for question,(_,z,measure) in [('Q3',area_best),('Q4',symmetry_best)]:
        refined=metrics(z,dx=.125)
        designs[question]={'settings_c':z[:4].tolist(),'speed_cm_min':float(z[4]),'metrics':measure,
                           'refined_metrics':refined,'minimum_normalized_margin':float(margins(refined).min()),
                           'optimality_scope':'best feasible multistart SLSQP result, not a global certificate'}
        t,y,air=curve(parameters,z[:4],z[4],dx=.125)
        pd.DataFrame({'time_s':t,'temperature_c':y,'ambient_c':air}).to_csv(root/(question.lower()+'_curve.csv'),index=False)
    # Independent analytical check: constant ambient has a closed-form response.
    tau=40.;dt=.2;forcing=175.;n=300
    yy,_=lfilter([1-np.exp(-dt/tau)],[1,-np.exp(-dt/tau)],np.repeat(forcing,n),zi=[25*np.exp(-dt/tau)])
    exact=forcing+(25-forcing)*np.exp(-np.arange(1,n+1)*dt/tau)
    analytic_error=float(np.max(np.abs(yy-exact)))
    status=bool(fitted.success and maximum is not None and analytic_error<1e-9 and
                all(z['minimum_normalized_margin']>=-2e-3 for z in designs.values()))
    return {'case_id':'cumcm-2020-a','status':'PASS' if status else 'FAIL','synthetic':False,
            'calibration_parameters':parameters.tolist(),'baseline_parameters':baseline.x.tolist(),
            'holdout':errors,'calibration_count':int(train.sum()),'holdout_count':int(holdout.sum()),
            'identifiability':identifiability_diagnostics(fitted.jac,parameter_scales=parameters),
            'questions':{'Q1':q1,'Q2':q2,**designs},'q4_area_budget_relative_to_q3':1.05,
            'analytic_max_error_c':analytic_error,'optimization_attempts':history,
            'limitations':['One measured trajectory; blocked holdout measures within-run interpolation only.',
                           'Effective time constants and entrance shape are model assumptions, not measured material constants.',
                           'Predictions at changed setpoints and speed need a new physical experiment.',
                           'Q4 uses an explicit 5% area allowance; another preference may change the recommendation.']}

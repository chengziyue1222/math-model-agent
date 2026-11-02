"""Explicit statistical calculations; renderers never train models implicitly."""
from __future__ import annotations

import numpy as np
from scipy import stats
from scipy.spatial.distance import pdist, squareform
from .base import finite_array


def compute_matrix_statistics(observations, *, labels, variable_units, kind="correlation",
                              missing, method="pearson"):
    """Save matrix statistics with explicit complete-case missing handling.

    NaN is retained for constant-variable correlations. Infinity is invalid.
    No pairwise deletion or imputation is silently performed.
    """
    from .practical import labels as validate_labels
    a = np.asarray(observations, float)
    if a.ndim != 2 or not a.size or np.isinf(a).any():
        raise ValueError("observations must be a nonempty matrix without infinity")
    validate_labels(labels, a.shape[1], "labels")
    validate_labels(variable_units, a.shape[1], "variable_units")
    if missing not in {"raise", "complete_case"}:
        raise ValueError("missing must be raise or complete_case")
    if kind not in {"correlation", "covariance"} or method not in {"pearson", "spearman"}:
        raise ValueError("invalid kind or method")
    if kind == "covariance" and method != "pearson":
        raise ValueError("covariance uses the original observations, not ranks")
    original_n = len(a)
    if np.isnan(a).any():
        if missing == "raise":
            raise ValueError("missing observations; select complete_case explicitly")
        a = a[~np.isnan(a).any(axis=1)]
    if len(a) < 2:
        raise ValueError("at least two complete observations required")
    transformed = stats.rankdata(a, axis=0) if method == "spearman" else a
    with np.errstate(invalid="ignore", divide="ignore"):
        matrix = np.atleast_2d(np.corrcoef(transformed, rowvar=False) if kind == "correlation"
                              else np.cov(a, rowvar=False, ddof=1))
    return dict(matrix=matrix, labels=list(labels), variable_units=list(variable_units),
                calculation={"kind": kind, "method": method, "missing": missing,
                             "n": len(a), "original_n": original_n, "ddof": 1,
                             "units": "dimensionless" if kind == "correlation" else "row unit × column unit"})


def compute_pca(matrix, *, standardize=True, components=2):
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler
    a = finite_array(matrix, "matrix", ndim=2)
    if not 1 <= components <= min(a.shape):
        raise ValueError("components must be between 1 and min(matrix.shape)")
    transformed = StandardScaler().fit_transform(a) if standardize else a
    if np.var(transformed, axis=0).sum() == 0:
        raise ValueError("PCA needs nonconstant data")
    model = PCA(n_components=components).fit(transformed)
    return dict(scores=model.transform(transformed), loadings=model.components_.T,
                explained_variance=model.explained_variance_ratio_,
                calculation={"method": "PCA", "standardize": standardize, "n": len(a)})


def compute_mantel(distance_a, distance_b, *, permutations=999, seed=0):
    a, b = [finite_array(v, k, ndim=2) for v, k in [(distance_a, "distance_a"), (distance_b, "distance_b")]]
    if a.shape != b.shape or a.shape[0] != a.shape[1] or len(a) < 3:
        raise ValueError("Mantel distance matrices must be aligned square matrices, n >= 3")
    for matrix in (a, b):
        if np.any(matrix < 0) or not np.allclose(matrix, matrix.T) or not np.allclose(np.diag(matrix), 0):
            raise ValueError("distance matrices must be symmetric, nonnegative with zero diagonal")
    if not isinstance(permutations, int) or permutations < 1:
        raise ValueError("permutations must be a positive integer")
    indices = np.triu_indices(len(a), 1)
    va, vb = a[indices], b[indices]
    if np.std(va) == 0 or np.std(vb) == 0:
        raise ValueError("Mantel needs nonconstant distances")
    r = float(np.corrcoef(va, vb)[0, 1])
    rng = np.random.default_rng(seed)
    null = []
    for _ in range(permutations):
        order = rng.permutation(len(a))
        null.append(float(np.corrcoef(va, b[np.ix_(order, order)][indices])[0, 1]))
    p = (1 + np.count_nonzero(np.abs(null) >= abs(r) - 1e-12)) / (permutations + 1)
    return dict(distance_a=va, distance_b=vb, r=r, p=float(p), permutations=permutations,
                seed=seed, calculation={"method": "Pearson Mantel", "alternative": "two-sided", "sample_count": len(a)})


def distances(matrix, *, metric="euclidean"):
    return squareform(pdist(finite_array(matrix, "matrix", ndim=2), metric=metric))


def compute_taylor(observed, predicted, *, labels=None):
    o = finite_array(observed, "observed")
    p = finite_array(predicted, "predicted", ndim=2)
    if len(o) < 2 or p.shape[0] != len(o) or np.std(o, ddof=1) == 0 or np.any(np.std(p, axis=0, ddof=1) == 0):
        raise ValueError("Taylor requires aligned nonconstant observed/predicted samples")
    return dict(reference_std=float(np.std(o, ddof=1)), std=np.std(p, axis=0, ddof=1),
                correlation=np.array([np.corrcoef(o, column)[0, 1] for column in p.T]),
                centered_rmse=np.sqrt(np.sum(((p-p.mean(0))-(o-o.mean())[:, None])**2, axis=0)/(len(o)-1)),
                labels=labels or [f"模型{i+1}" for i in range(p.shape[1])],
                calculation={"method": "Taylor statistics", "std_ddof": 1, "rmse_ddof": 1})


def compute_embedding(matrix, *, method, seed=0, **parameters):
    a = finite_array(matrix, 'matrix', ndim=2)
    if method == 'tsne':
        from sklearn.manifold import TSNE
        model = TSNE(n_components=2, random_state=seed, **parameters)
    elif method == 'umap':
        try:
            from umap import UMAP
        except ImportError as exc:
            raise ValueError('UMAP computation needs optional umap-learn; rendering supplied coordinates does not') from exc
        model = UMAP(n_components=2, random_state=seed, n_jobs=1, **parameters)
    else:
        raise ValueError('method must be tsne or umap')
    return dict(embedding=model.fit_transform(a), calculation={'method':method,'seed':seed,'parameters':parameters})


def compute_linear_shap(features, coefficients, *, baseline=None):
    a = finite_array(features, 'features', ndim=2)
    beta = finite_array(coefficients, 'coefficients')
    base = a.mean(0) if baseline is None else finite_array(baseline, 'baseline')
    if beta.shape != (a.shape[1],) or base.shape != beta.shape:
        raise ValueError('coefficients and baseline must align with feature columns')
    return dict(attributions=(a-base)*beta, features=a,
                calculation={'method':'exact interventional SHAP for a linear additive model',
                             'coefficients':beta.tolist(),'baseline':base.tolist()})


def compute_dependence(predict, matrix, feature_index, grid):
    a = finite_array(matrix, "matrix", ndim=2)
    g = finite_array(grid, "grid")
    if not isinstance(feature_index, int) or not 0 <= feature_index < a.shape[1]:
        raise ValueError("feature_index out of range")
    curves = []
    for value in g:
        changed = a.copy(); changed[:, feature_index] = value
        prediction = finite_array(predict(changed), "prediction")
        if prediction.shape != (len(a),):
            raise ValueError("predict must return one numeric prediction per sample")
        curves.append(prediction)
    ice = np.asarray(curves).T
    return dict(grid=g, curves=ice, response=ice.mean(0),
                calculation={"method": "interventional partial dependence", "feature_index": feature_index})


def compute_lift_gain(y_true, y_score):
    truth, score = finite_array(y_true, "y_true"), finite_array(y_score, "y_score")
    if truth.shape != score.shape or set(np.unique(truth)) != {0, 1}:
        raise ValueError("lift/gain needs aligned binary labels and scores")
    order = np.argsort(-score, kind="stable")
    fraction = np.arange(1, len(truth)+1) / len(truth)
    gain = np.cumsum(truth[order]) / truth.sum()
    return dict(population_fraction=fraction, gain=gain, lift=gain/fraction,
                calculation={"method": "ranked cumulative positives", "ties": "stable input order"})


def compute_partial_correlation(data, controls):
    x = finite_array(data, "data", ndim=2)
    z = finite_array(controls, "controls", ndim=2)
    if len(x) != len(z) or len(x) <= z.shape[1]+2:
        raise ValueError("controls must align with data and leave residual degrees of freedom")
    design = np.column_stack([np.ones(len(z)), z])
    if np.linalg.matrix_rank(design) < design.shape[1]:
        raise ValueError("controls are rank deficient")
    residual = x-design @ np.linalg.lstsq(design, x, rcond=None)[0]
    if np.any(np.std(residual, axis=0) < 1e-12):
        raise ValueError("partial correlation has constant residual variables")
    return dict(matrix=np.corrcoef(residual, rowvar=False),
                calculation={"method": "Pearson correlation of OLS residuals", "controls": z.shape[1]})


def compute_timeseries(time, values, *, window=None, period=None, max_lag=None):
    t, y = finite_array(time, "time"), finite_array(values, "values")
    if t.shape != y.shape or len(y) < 3 or not np.all(np.diff(t) > 0):
        raise ValueError("time and values must align with increasing time")
    result = {"time": t, "values": y, "calculation": {"method": "explicit time series transforms"}}
    if window is not None:
        if not isinstance(window, int) or not 1 <= window <= len(y):
            raise ValueError("window must be a valid integer")
        result.update(time=t[window-1:], center=np.convolve(y, np.ones(window)/window, mode="valid"), window=window)
    if max_lag is not None:
        if not isinstance(max_lag, int) or not 0 <= max_lag < len(y) or np.var(y) == 0:
            raise ValueError("max_lag must be valid and values nonconstant")
        c = y-y.mean(); acf = np.correlate(c, c, mode="full")[len(y)-1:len(y)+max_lag] / (c @ c)
        from scipy.linalg import toeplitz
        pacf = [1.]
        for lag in range(1, max_lag+1):
            pacf.append(float(np.linalg.solve(toeplitz(acf[:lag]), acf[1:lag+1])[-1]))
        result.update(lag=np.arange(max_lag+1), acf=acf, pacf=np.asarray(pacf))
    if period is not None:
        if not isinstance(period, int) or period < 2 or len(y) < 2*period or not np.allclose(np.diff(t), np.diff(t)[0]):
            raise ValueError("decomposition needs regular time and at least two periods")
        # Explicit centered moving mean with edge replication; decomposition retains every row.
        trend = np.convolve(np.pad(y, (period//2, (period-1)//2), mode="edge"), np.ones(period)/period, mode="valid")
        detrended = y-trend
        seasonal_pattern = np.array([detrended[i::period].mean() for i in range(period)])
        seasonal_pattern -= seasonal_pattern.mean()
        seasonal = seasonal_pattern[np.arange(len(y)) % period]
        result.update(trend=trend, seasonal=seasonal, residual=y-trend-seasonal, period=period)
    return result


def compute_coverage(observed, lower, upper, nominal):
    y = finite_array(observed, "observed")
    lo, hi = finite_array(lower, "lower", ndim=2), finite_array(upper, "upper", ndim=2)
    nominal = finite_array(nominal, "nominal")
    if lo.shape != hi.shape or lo.shape != (len(y), len(nominal)) or np.any(lo > hi) or np.any((nominal <= 0) | (nominal > 1)):
        raise ValueError("coverage bounds must be sample-by-level with legal nominal levels")
    return dict(nominal=nominal, empirical=np.mean((lo <= y[:, None]) & (y[:, None] <= hi), axis=0),
                calculation={"method": "empirical interval coverage", "n": len(y)})


def compute_ahp(matrix, *, labels=None):
    a = finite_array(matrix, "matrix", ndim=2)
    if a.shape[0] != a.shape[1] or not 2 <= len(a) <= 10 or np.any(a <= 0) or not np.allclose(a*a.T, 1):
        raise ValueError("AHP needs a positive reciprocal 2..10 square matrix")
    eigenvalues, eigenvectors = np.linalg.eig(a)
    index = np.argmax(eigenvalues.real)
    weights = np.abs(eigenvectors[:, index].real); weights /= weights.sum()
    random_index = [0, 0, 0, .58, .90, 1.12, 1.24, 1.32, 1.41, 1.45, 1.49][len(a)]
    ci = float((eigenvalues[index].real-len(a))/(len(a)-1))
    return dict(categories=labels or [f"指标{i+1}" for i in range(len(a))], values=weights,
                method="AHP principal eigenvector", consistency_ratio=ci/random_index if random_index else 0.)


def compute_probability_plot(values, *, distribution="norm"):
    y = finite_array(values, "values")
    if distribution not in {"norm", "expon", "logistic"}:
        raise ValueError("supported distributions: norm, expon, logistic")
    theoretical, ordered = stats.probplot(y, dist=distribution, fit=False)
    return dict(theoretical=np.asarray(theoretical), observed=np.asarray(ordered), distribution=distribution)

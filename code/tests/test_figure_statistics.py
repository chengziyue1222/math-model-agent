import matplotlib.pyplot as plt
import numpy as np
import pytest
from sklearn.metrics import auc, precision_recall_curve, roc_curve

from algorithms.figures import get_figure


def test_roc_and_pr_metadata_matches_sklearn():
    y_true = np.array([0, 0, 1, 1])
    y_score = np.array([0.1, 0.4, 0.35, 0.8])
    fpr, tpr, _ = roc_curve(y_true, y_score)
    expected_auc = auc(fpr, tpr)
    roc = get_figure("roc_curve")(data={"y_true": y_true, "y_score": y_score})
    assert roc._figure_metadata["auc"] == pytest.approx(expected_auc)
    precision, recall, _ = precision_recall_curve(y_true, y_score)
    pr = get_figure("pr_curve")(data={"y_true": y_true, "y_score": y_score})
    np.testing.assert_allclose(pr._figure_metadata["precision"], precision)
    np.testing.assert_allclose(pr._figure_metadata["recall"], recall)
    plt.close("all")


def test_correlation_matrix_metadata_is_numeric_result():
    data = np.array([[1.0, 2.0, 4.0], [2.0, 4.0, 3.0], [3.0, 8.0, 2.0], [4.0, 16.0, 1.0]])
    fig = get_figure("correlation_matrix")(data={"data": data})
    np.testing.assert_allclose(fig._figure_metadata["correlation"], np.corrcoef(data, rowvar=False))
    plt.close(fig)


def test_structured_contracts_and_string_communities():
    surface = get_figure("response_surface")(data={"x_grid": [0, 1], "y_grid": [0, 1], "z": [[0, 1], [1, 0]]})
    assert surface._figure_metadata["grid_shape"] == [2, 2]
    network = get_figure("community_network")(data={
        "nodes": ["A", "B", "C"], "edges": [("A", "B"), ("B", "C")],
        "community": ["C1", "C2", "C1"],
    })
    assert network._figure_metadata["community_mapping"] == {"C1": 0, "C2": 1}
    plt.close("all")


def test_formal_adapters_reject_invented_statistics():
    with pytest.raises(ValueError, match="calibration_curve requires fields"):
        get_figure("calibration_curve")(data={"values": [0.2, 0.3]})
    with pytest.raises(ValueError, match="robustness_envelope requires fields"):
        get_figure("robustness_envelope")(data={"values": [0.2, 0.3]})
    with pytest.raises(ValueError, match="tornado requires fields"):
        get_figure("tornado")(data={"values": [0.2, 0.3]})


def test_pareto_frontier_is_computed_from_objectives():
    fig = get_figure("pareto")(data={"x": [1, 2, 3, 4], "y": [4, 3, 3.5, 2]})
    assert fig._figure_metadata["frontier_size"] == 3
    plt.close(fig)


def test_pareto_ties_do_not_keep_dominated_points():
    fig = get_figure("pareto")(data={"x": [1, 1, 2, 3], "y": [4, 2, 3, 1]})
    assert set(fig._figure_metadata["frontier_indices"]) == {1, 3}
    plt.close(fig)


def test_forest_and_errorbar_preserve_declared_intervals():
    for key, center_field in [("forest", "estimate"), ("errorbar", "values")]:
        data = {"categories": ["A", "B"], center_field: [2., 4.],
                "lower": [1., 3.], "upper": [2.5, 6.], "interval_kind": "95% CI"}
        fig = get_figure(key)(data=data)
        assert fig._figure_metadata["interval_kind"] == "95% CI"
        segments = fig.axes[0].collections[0].get_segments()
        if key == "forest":
            np.testing.assert_allclose(segments[0][:, 0], [1., 2.5])
        else:
            np.testing.assert_allclose(segments[0][:, 1], [1., 2.5])
        data["lower"] = [3., 3.]
        with pytest.raises(ValueError, match="lower"):
            get_figure(key)(data=data)
    plt.close("all")


def test_pca_preserves_scores_loadings_and_axis_variance():
    scores = [[-1., 0.], [0., 1.], [1., -1.]]
    loadings = [[.8, .2], [-.3, .7]]
    fig = get_figure("pca_biplot")(data={"scores": scores, "loadings": loadings,
                                        "explained_variance": [.6, .3]})
    np.testing.assert_allclose(fig._figure_metadata["scores"], scores)
    np.testing.assert_allclose(fig._figure_metadata["loadings"], loadings)
    assert "60.0%" in fig.axes[0].get_xlabel()
    assert "30.0%" in fig.axes[0].get_ylabel()
    with pytest.raises(ValueError, match="scores"):
        get_figure("pca_biplot")(data={"scores": [1, 2], "loadings": loadings, "explained_variance": [.6, .3]})
    plt.close("all")


def test_sensitivity_reorders_pairs_without_changing_response():
    fig = get_figure("sensitivity")(data={"x": [3., 1., 2.], "response": [9., 1., 4.]})
    np.testing.assert_allclose(fig.axes[0].lines[0].get_xdata(), [1., 2., 3.])
    np.testing.assert_allclose(fig.axes[0].lines[0].get_ydata(), [1., 4., 9.])
    plt.close(fig)


@pytest.mark.parametrize("name", ["sankey", "alluvial"])
def test_flow_ribbons_preserve_nonnegative_values(name):
    from matplotlib.patches import PathPatch
    data = {"source": ["A", "B"], "target": ["B", "C"], "value": [4., 2.]}
    if name == "alluvial":
        data.update(source_stage=[0, 1], target_stage=[1, 2])
    fig = get_figure(name)(data=data)
    assert sum(isinstance(p, PathPatch) for p in fig.axes[0].patches) == 2
    assert fig._figure_metadata["value"] == [4., 2.]
    data["value"] = [4., -1.]
    with pytest.raises(ValueError, match="negative"):
        get_figure(name)(data=data)
    plt.close(fig)


def test_response_surface_grid_position_and_shape():
    fig = get_figure("response_surface")(data={"x_grid": [10., 20., 30.], "y_grid": [-5., 5.],
                                              "z": [[1., 2., 3.], [4., 5., 6.]]})
    assert fig.axes[0].get_xlim() == pytest.approx((10., 30.))
    assert fig.axes[0].get_ylim() == pytest.approx((-5., 5.))
    with pytest.raises(ValueError, match="shape"):
        get_figure("response_surface")(data={"x_grid": [1,2,3], "y_grid": [1,2], "z": [[1,2],[3,4]]})
    plt.close(fig)


@pytest.mark.parametrize("community", [["C1", "C2", "C1"], [0, 1, 0]])
def test_network_supports_integer_string_communities_and_declared_order(community):
    fig = get_figure("community_network")(data={"nodes": ["C", "A", "B"],
        "edges": [("A", "B")], "community": community})
    assert fig._figure_metadata["nodes"] == ["C", "A", "B"]
    assert len(fig._figure_metadata["community_labels"]) == 2
    plt.close(fig)


@pytest.mark.parametrize("community", [None, ["C1"], ["C1", "", "C2"]])
def test_missing_invalid_community_is_value_error(community):
    data = {"nodes": ["A", "B", "C"], "edges": [("A", "B")]}
    if community is not None:
        data["community"] = community
    with pytest.raises(ValueError, match="community"):
        get_figure("community_network")(data=data)


def test_formal_adapters_cannot_fabricate_statistical_meaning():
    for name in ["shap_summary", "taylor_diagram", "cluster_stability", "spatial_3d", "response_surface_opt"]:
        with pytest.raises(ValueError):
            get_figure(name)(data={"values": [1., 2., 3.]})
    with pytest.raises(ValueError, match="simulated"):
        get_figure("shap_summary")(data={"values": [1., 2., 3.]}, mode="preview")
    plt.close("all")


def test_dense_pca_keeps_all_loadings_and_limits_label_density():
    rng = np.random.default_rng(17)
    loadings = rng.normal(size=(80, 2))
    fig = get_figure("pca_biplot")(data={"scores": rng.normal(size=(100, 2)),
        "loadings": loadings, "explained_variance": [.4, .2]})
    assert len(fig._figure_metadata["loadings"]) == 80
    assert len(fig._figure_metadata["labeled_feature_indices"]) == 12
    dense = get_figure("pca_loadings")(data={"loadings": loadings})
    assert len(dense.axes) == 4
    assert sum(len(axis.patches) for axis in dense.axes) == 160
    assert sum(len(axis.get_yticklabels()) for axis in dense.axes) == 80
    plt.close("all")


def test_pca_preview_uses_one_model_for_scores_loadings_and_variance():
    from scripts.build_random_figure_previews import _make, SEED
    from algorithms.figures import DataContract
    fig = _make("pca_biplot", np.random.default_rng(SEED), DataContract(simulated=True))
    metadata = fig._figure_metadata
    scores, loadings = np.asarray(metadata["scores"]), np.asarray(metadata["loadings"])
    np.testing.assert_allclose(loadings.T @ loadings, np.eye(2), atol=1e-10)
    np.testing.assert_allclose(scores.mean(0), 0, atol=1e-10)
    covariance = np.cov(scores.T)
    assert abs(covariance[0, 1]) < 1e-10
    np.testing.assert_allclose(np.diag(covariance) / (6 * 90 / 89), metadata["explained_variance"], atol=1e-10)
    plt.close(fig)

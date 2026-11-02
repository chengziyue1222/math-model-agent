import matplotlib.pyplot as plt
import numpy as np
import pytest
from collections import defaultdict
from hashlib import sha256
from pathlib import Path

from algorithms.figures import DataContract, display_name, get_figure, get_spec, list_figures
from algorithms.figures.fixtures import classification_comparison, model_predictions, multivariate_matrix, network_edges, optimization_points, spatial_points, time_series
from algorithms.sci_figures import ChordDiagram, ChordNode, CvRocCurve, PairedRaincloud


def test_registry_covers_core_categories_and_returns_callable():
    names = set(list_figures())
    for name in {"histogram", "grouped_bar", "scatter", "time_series", "heatmap", "roc_curve", "convergence", "pca_scores", "tsne", "dependency_graph", "flowchart"}:
        assert name in names
        assert callable(get_figure(name))
        assert get_spec(name).category
    with pytest.raises(ValueError, match="groups"):
        get_figure("grouped_bar")(data={"categories": ["A", "B"], "values": [1, 2]})
    fig = get_figure("grouped_bar")(data={"categories": ["A", "B"], "values": [[1, 2], [2, 3]], "groups": ["G1", "G2"]})
    plt.close(fig)


def test_full_catalog_is_academic_and_structural_inputs_are_callable():
    names = list_figures()
    assert len(names) >= 155
    levels = {get_spec(name).implementation_level for name in names}
    assert levels == {"dedicated", "alias"}
    assert sum(get_spec(n).implementation_level == 'alias' for n in names) == 5
    assert all(get_spec(name).status != "implemented and reusable" for name in names)
    for label, data in {
        "火山图": {"x": np.array([-1.0, 0.2, 0.9]), "y": np.array([.01, .4, .001])},
        "桑基图": {"source": ["输入", "模型"], "target": ["模型", "输出"], "value": [2.0, 1.0]},
        "状态机图": {"nodes": ["输入", "输出"], "edges": [("输入", "输出")], "events": ['处理完成']},
    }.items():
        if get_spec(label).implementation_level == "adapter":
            fig = get_figure(label)(data=dict(data, simulated=True), mode="preview")
        else:
            fig = get_figure(label)(data=data)
        assert fig._figure_metadata["name_zh"] == display_name(get_spec(label).name)
        plt.close(fig)


def test_chinese_name_is_a_real_api_alias():
    assert len(list_figures(chinese=True)) == len(list_figures())
    assert display_name("histogram") == "直方图"
    assert get_spec("直方图").name == "histogram"
    fig = get_figure("直方图")([1.0, 2.0, 3.0])
    assert fig._figure_metadata["name"] == "histogram"
    assert fig._figure_metadata["name_zh"] == "直方图"
    plt.close(fig)
    fig = get_figure("tsne")(data={"embedding": np.array([[0., 1.], [1., 0.]])})
    plt.close(fig)


def test_data_contract_does_not_infer_independent_sample_size():
    contract = DataContract(source="results.csv", independent_unit="participant", simulated=False,
                            units={"response": "W"})
    assert contract.to_dict()["independent_unit"] == "participant"
    assert "n" not in contract.to_dict()
    with pytest.raises(ValueError):
        DataContract(source="", independent_unit="participant")


def test_real_roc_requires_labels_and_scores_and_does_not_back_calculate():
    with pytest.raises(ValueError, match="y_true"):
        CvRocCurve(models=[], simulate=False)
    y = np.array([0, 0, 1, 1])
    score = np.array([.1, .2, .8, .9])
    fig = CvRocCurve(y_true=y, y_score=score, simulate=False).make()
    assert fig._figure_metadata["data_mode"] == "real labels and prediction scores"
    plt.close(fig)


def test_chord_labels_use_sector_midpoint_and_metadata():
    diagram = ChordDiagram([ChordNode("A", "#336699", 1), ChordNode("B", "#CC6633", 2)], [("A", "B", 1)])
    layout = diagram._compute_layout()
    assert diagram._polar_point(1, layout["A"]["mid"]) != (0.0, 0.0)
    fig = diagram.make()
    assert fig._figure_metadata["label_geometry"] == "true sector midpoint in circular coordinates"
    plt.close(fig)


def test_modular_grouped_bar_requires_interval_semantics_for_errors():
    fn = get_figure("grouped_bar")
    with pytest.raises(ValueError, match="interval_kind"):
        fn(["A", "B"], [[1], [2]], groups=['G'], errors=[[.1], [.2]])
    fig = fn(["A", "B"], [[1], [2]], groups=['G'], errors=[[.1], [.2]], interval_kind="SE", contract=DataContract(source="synthetic", simulated=True))
    assert fig._figure_metadata["interval_kind"] == "SE"
    plt.close(fig)


def test_high_priority_contracts_reject_missing_or_invalid_structure():
    with pytest.raises(ValueError, match="x_grid"):
        get_figure("response_surface")(data={"x": [0, 1], "y": [0, 1], "z": [[0, 1], [1, 0]]})
    with pytest.raises(ValueError, match="interval_kind"):
        get_figure("forest")(data={"categories": ["A"], "estimate": [1.], "lower": [.8], "upper": [1.2]})
    with pytest.raises(ValueError, match="nodes"):
        get_figure("weighted_network")(data={"edges": [("A", "B")], "weights": [1.]})
    with pytest.raises(ValueError, match="source"):
        get_figure("桑基图")(data={"flows": [("A", "B", 1.)]})


def test_representative_contract_fixtures_have_required_semantics():
    fixtures = [classification_comparison(), time_series(), model_predictions(), multivariate_matrix(), network_edges(), spatial_points(), optimization_points()]
    assert len(fixtures) == 7
    assert all("contract_meta" in fixture and "independent_unit" in fixture["contract_meta"] for fixture in fixtures)
    assert network_edges()["weights"].__len__() == len(network_edges()["edges"])
    assert spatial_points()["longitude"].shape == spatial_points()["latitude"].shape


def test_exported_catalog_has_no_exact_duplicate_pngs_when_present():
    root = Path(__file__).parents[2] / "output" / "figure-library-gallery-academic"
    if not root.exists():
        pytest.skip("gallery output has not been built")
    hashes = defaultdict(list)
    for path in root.glob("*.png"):
        if path.stem in list_figures() and get_spec(path.stem).implementation_level == "alias":
            continue
        hashes[sha256(path.read_bytes()).hexdigest()].append(path.name)
    assert [names for names in hashes.values() if len(names) > 1] == []


def test_paired_raincloud_records_pairing_status():
    data = {("pre", "A"): np.array([1., 2.]), ("post", "A"): np.array([2., 3.])}
    palette = {"A": {"edge": "#333333", "fill": "#8899AA"}}
    fig = PairedRaincloud(data, ["A"], ["pre", "post"], palette,
                          pair_ids={("pre", "A"): np.array(["p1", "p2"]),
                                    ("post", "A"): np.array(["p1", "p2"])},
                          independent_unit="participant").make()
    assert fig._figure_metadata["paired"] is True
    assert fig._figure_metadata["independent_unit"] == "participant"
    plt.close(fig)


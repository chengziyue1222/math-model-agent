"""Check actual numerical marks, missing states and saved-fit semantics."""
import matplotlib.pyplot as plt
import numpy as np
import pytest

from algorithms.figures import get_figure, get_spec
from algorithms.figures.compute import compute_matrix_statistics
from algorithms.figures.practical import FIELDS, calendar_positions, dates_of, person_fraction_height, person_visible_area
from algorithms.figures.practical_examples import example


@pytest.mark.parametrize("name", FIELDS)
def test_structured_previews_and_aliases(name):
    spec = get_spec(name)
    assert get_spec(spec.name_zh).name == name
    fig = get_figure(spec.name_zh)(data=example(name), mode="preview")
    try:
        fig.canvas.draw()
        assert fig._figure_metadata["simulated"]
        assert not fig._figure_metadata["paper_suitable"]
        assert set(spec.required_fields) <= set(fig._figure_metadata["input_data"])
    finally:
        plt.close(fig)


@pytest.mark.parametrize("name", FIELDS)
def test_catalogue_example_preserves_formal_contract(name):
    from algorithms.figures.examples import example_data
    data = example_data(name)
    assert data["contract"].simulated
    fig = get_figure(name)(data=data, mode="formal")
    try:
        fig.canvas.draw()
        assert fig._figure_metadata["data_contract"]["simulated"]
        assert not fig._figure_metadata["paper_suitable"]
    finally:
        plt.close(fig)


def test_polar_radial_stack_heights_and_angular_widths():
    data = dict(categories=["甲", "乙"], groups=["A", "B"], values=[[1, 3], [2, 0]])
    for orientation in ("radial", "angular"):
        fig = get_figure("polar_stacked_bar")(data=data, orientation=orientation, percent=True)
        try:
            np.testing.assert_allclose(fig._figure_metadata["displayed_values"], [[25, 75], [100, 0]])
            marks = fig.axes[0].patches
            if orientation == "radial":
                np.testing.assert_allclose([p.get_height() for p in marks], [25, 100, 75, 0])
            else:
                np.testing.assert_allclose([p.get_width() for p in marks], np.array([.25, .75, 1, 0])*2*np.pi)
        finally:
            plt.close(fig)


def test_sparkline_missing_and_shared_limits():
    fig = get_figure("sparkline_matrix")(data=example("sparkline_matrix"))
    try:
        assert len({ax.get_ylim() for ax in fig.axes}) == 1
        assert not fig.axes[-1].lines
        assert any(t.get_text() == "缺失" for t in fig.axes[-1].texts)
    finally:
        plt.close(fig)


def test_calendar_leap_day_real_coordinates_and_duplicate_rejection():
    dates = dates_of(["2024-02-28", "2024-02-29", "2024-03-01"])
    assert calendar_positions(dates, 2024) == [(8, 2), (8, 3), (8, 4)]
    with pytest.raises(ValueError, match="duplicate"):
        dates_of(["2024-02-29", "2024-02-29 12:00"])
    with pytest.raises(ValueError):
        dates_of(["2023-02-29"])
    for layout in ("horizontal", "vertical"):
        fig = get_figure("calendar_heatmap")(data=example("calendar_heatmap"), layout=layout)
        try:
            assert len(fig._figure_metadata["positions"]) == 5
            assert fig._figure_metadata["zero_dates"] == ["2023-12-31"]
        finally:
            plt.close(fig)


def test_bubble_area_proportion_and_zero():
    fig = get_figure("bubble_matrix")(data=example("bubble_matrix"))
    try:
        sizes = fig.axes[0].collections[0].get_sizes()
        np.testing.assert_allclose(sizes, np.array([0, 2, 8, 1, 3, 4])/8*180)
    finally:
        plt.close(fig)


def test_matrix_statistics_known_values_constant_and_missing():
    observations = [[1, 3, 5], [2, 5, 5], [3, 7, 5]]
    kw = dict(labels=["A", "B", "C"], variable_units=["m", "s", "kg"], missing="raise")
    correlation = compute_matrix_statistics(observations, **kw)
    np.testing.assert_allclose(correlation["matrix"][:2, :2], 1)
    assert np.isnan(correlation["matrix"][2]).all()
    covariance = compute_matrix_statistics(observations, kind="covariance", **kw)
    np.testing.assert_allclose(covariance["matrix"], [[1, 2, 0], [2, 4, 0], [0, 0, 0]])
    with pytest.raises(ValueError, match="missing"):
        compute_matrix_statistics([[1, 2, 3], [np.nan, 2, 3]], **kw)
    cleaned = compute_matrix_statistics([*observations, [np.nan, 4, 5]], **{**kw, "missing": "complete_case"})
    assert cleaned["calculation"]["n"] == 3 and cleaned["calculation"]["original_n"] == 4


def test_regression_never_fits_or_invents_interval():
    fig = get_figure("regression_curve")(data=example("regression_curve"))
    try:
        assert not fig._figure_metadata["fit_performed"]
        assert len(fig.axes[0].collections) == 1  # observations, no interval
        assert any(line.get_linestyle() == "--" for line in fig.axes[0].lines)
    finally:
        plt.close(fig)


def test_icon_fraction_visible_area_not_height():
    # The limb/torso/head widths differ, so half area is not half height.
    assert 0 < person_fraction_height(.5) < 1
    assert person_fraction_height(.5) != .5
    assert person_fraction_height(0) == 0
    assert person_fraction_height(1) == 1
    np.testing.assert_allclose(person_visible_area(person_fraction_height(.3))/person_visible_area(1), .3, atol=1e-12)
    fig = get_figure("pictogram")(categories=["甲"], values=[2.5], icon_value=1)
    try:
        assert fig._figure_metadata["fractions"] == [1, 1, .5]
    finally:
        plt.close(fig)


@pytest.mark.parametrize("fraction", [.001, .01, .13, .3, .5, .67, .9, .999])
def test_rounded_person_partial_fill_retains_exact_visible_area(fraction):
    height = person_fraction_height(fraction)
    assert person_visible_area(height)/person_visible_area(1) == pytest.approx(fraction, abs=1e-12)


def test_narrow_person_array_reflows_without_rounding_or_losing_labels():
    data = dict(categories=["积极（长期综合测量与约束条件）", "中性", "消极"],
                values=[20, 67, 13], icon_value=10)
    wide = get_figure("pictogram")(data=data, config={"width_mm": 150})
    narrow = get_figure("pictogram")(data=data, config={"width_mm": 75})
    explicit = get_figure("pictogram")(data={**data, "columns": 3},
                                      config={"width_mm": 75, "height_mm": 140})
    try:
        assert wide._figure_metadata['columns'] == 10
        assert narrow._figure_metadata['columns'] == 5
        assert explicit._figure_metadata['columns'] == 3
        assert narrow.get_figheight() > wide.get_figheight()
        assert explicit.get_figheight()*25.4 == pytest.approx(140)
        for fig in [wide, narrow, explicit]:
            meta = fig._figure_metadata
            assert meta['category_icon_counts'] == [2, 7, 2]
            np.testing.assert_allclose(meta['fractions'], [1, 1]+[1]*6+[.7, 1, .3])
            captions = [text.get_text().replace('\n', '') for text in fig.axes[0].texts]
            assert captions == [f'{label}：{value}' for label, value in zip(data['categories'], data['values'])]
    finally:
        for fig in [wide, narrow, explicit]:
            plt.close(fig)


def test_silhouette_clips_to_height_segments():
    fig = get_figure("pictogram")(categories=["A", "B", "C"], values=[20, 67, 13], pictogram_mode="silhouette")
    try:
        fig.canvas.draw()
        # All disjoint silhouette parts in a segment share the same clipping
        # rectangle; the check must not depend on the old six-block anatomy.
        boxes = {(round(p.get_clip_box().y0, 6), round(p.get_clip_box().height, 6))
                 for p in fig.axes[0].patches}
        heights = [height for _, height in sorted(boxes) if height < max(h for _, h in boxes)]
        np.testing.assert_allclose(np.array(heights)/sum(heights), [.2, .67, .13])
    finally:
        plt.close(fig)


def test_whole_case_waffle_preserves_counts_and_rejects_rounding():
    data = dict(categories=["A", "B", "C", "unknown"], values=[18, 12, 1, 9], array_layout="waffle", icon_value=1)
    fig = get_figure("pictogram")(data=data)
    try:
        assert fig._figure_metadata["category_icon_counts"] == [18, 12, 1, 9]
        assert fig._figure_metadata['icon_geometry'] == 'rounded-standing-person-v2'
        # Forty distinct icon placements survive independently of the polygon
        # count used to draw a person.
        assert len({tuple(p.get_clip_box().bounds) for p in fig.axes[0].patches}) == 40
    finally:
        plt.close(fig)
    with pytest.raises(ValueError, match="do not round"):
        get_figure("pictogram")(data={**data, "values": [18.5, 12, 1, 9]})


@pytest.mark.parametrize("name,updates", [
    ("polar_stacked_bar", {"values": [[-1, 2]]}),
    ("pictogram", {"icon_value": 0}),
    ("bubble_matrix", {"values": [[1, np.inf]]}),
    ("matrix_pie", {"groups": ["错"]}),
    ("sparkline_matrix", {"series": [[None]]}),
    ("correlation_heatmap", {"matrix": [[1, 2], [2, 1]], "labels": ["A", "B"]}),
    ("regression_curve", {"lower": [0]}),
    ("calendar_heatmap", {"layout": "invalid"}),
])
def test_invalid_inputs_allocate_no_figures(name, updates):
    before = plt.get_fignums()
    with pytest.raises(ValueError):
        get_figure(name)(data={**example(name), **updates})
    assert plt.get_fignums() == before

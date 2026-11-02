"""Regressions discovered by actually reading exported five-format proofs."""
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
import numpy as np
import pytest

from algorithms.figures import get_figure


@pytest.mark.parametrize('width', [75,150])
def test_bland_altman_reference_labels_match_sample_limits_and_fit(width):
    reference=np.array([1.,3.,4.,8.])
    comparison=reference+np.array([.1,-.4,.7,.2])
    fig=get_figure('bland_altman')(data=dict(reference=reference,comparison=comparison),
                                 config=dict(width_mm=width,height_mm=110),mode='preview',simulated=True)
    diff=comparison-reference
    limits=diff.mean()+np.array([-1,1])*1.96*diff.std(ddof=1)
    np.testing.assert_allclose(fig._figure_metadata['limits_of_agreement'],limits)
    np.testing.assert_allclose(fig.axes[0].collections[0].get_offsets(),
                               np.column_stack(((reference+comparison)/2,diff)))
    expected=[diff.mean(),limits[1],limits[0]]
    for line,value in zip(fig.axes[0].lines,expected):
        np.testing.assert_allclose(line.get_ydata(),[value,value])
    fig.canvas.draw()
    renderer=fig.canvas.get_renderer()
    legend=fig.legends[0]
    text=' '.join(t.get_text() for t in legend.get_texts())
    assert all(term in text for term in ('平均偏差','一致性上限','一致性下限'))
    assert '样本标准差' in legend.get_title().get_text()
    assert '置信' not in text
    for value in expected:
        assert f'{value:.3g}' in text
    box=legend.get_window_extent(renderer)
    assert fig.bbox.contains(box.x0,box.y0) and fig.bbox.contains(box.x1,box.y1)
    assert not box.overlaps(fig.axes[0].get_window_extent(renderer))
    plt.close(fig)


def test_bland_altman_rejects_undefined_single_pair_sample_deviation():
    with pytest.raises(ValueError,match='at least two pairs'):
        get_figure('bland_altman')(data=dict(reference=[1.],comparison=[2.]),mode='preview',simulated=True)


@pytest.mark.parametrize('width', [75,150])
def test_calibration_endpoint_markers_actually_paint_beyond_boundary_without_domain_change(width):
    fig=get_figure('calibration_curve')(data=dict(probability=[0.,1.],observed_rate=[0.,1.]),
                                      config=dict(width_mm=width,height_mm=100),mode='preview',simulated=True)
    fig.canvas.draw()
    axis=fig.axes[0]
    assert axis.get_xlim()==(0.,1.) and axis.get_ylim()==(0.,1.)
    np.testing.assert_array_equal(axis.lines[0].get_xydata(),[[0,0],[1,1]])
    rgba=np.asarray(fig.canvas.buffer_rgba())/255
    color=np.asarray(to_rgba(axis.lines[0].get_color()))[:3]
    matches=np.max(np.abs(rgba[:,:,:3]-color),axis=2)<.05
    height=matches.shape[0]
    for point,edge in [((0,0),'lower'),((1,1),'upper')]:
        px,py=axis.transData.transform(point)
        col,row=int(round(px)),int(round(height-py))
        patch=matches[max(row-5,0):row+6,max(col-5,0):col+6]
        assert patch.any()
        # At least a complete row of colored marker interior beyond the axis:
        # the previous clipped output has no such pixels above/right of (1,1).
        if edge=='upper':
            assert matches[row-3:row-1,col-1:col+2].any()
            assert matches[row-1:row+2,col+1:col+3].any()
        else:
            assert matches[row+1:row+3,col-1:col+2].any()
            assert matches[row-1:row+2,col-3:col-1].any()
    plt.close(fig)


@pytest.mark.parametrize('width',[75,150])
def test_control_chart_legend_explains_exactly_the_supplied_outliers(width):
    data=dict(time=[0,1,2,3],values=[-2,0,2,1],center=[0]*4,
              lower=[-1]*4,upper=[1]*4,interval_kind='caller-defined control limits')
    fig=get_figure('control_chart')(data=data,config=dict(width_mm=width,height_mm=100),mode='preview',simulated=True)
    axis=fig.axes[0]
    np.testing.assert_array_equal(axis.collections[0].get_offsets(),[[0,-2],[2,2]])
    assert fig._figure_metadata['out_of_control']==[0,2]
    assert '超出控制限' in [t.get_text() for t in fig.legends[0].get_texts()]
    fig.canvas.draw()
    assert not fig.legends[0].get_window_extent().overlaps(axis.get_window_extent())
    renderer=fig.canvas.get_renderer()
    for tick in axis.get_xticklabels():
        position=tick.get_position()[0]
        if axis.get_xlim()[0] <= position <= axis.get_xlim()[1]:
            box=tick.get_window_extent(renderer)
            assert fig.bbox.contains(box.x0,box.y0) and fig.bbox.contains(box.x1,box.y1)
    plt.close(fig)


def test_explicit_multiline_legend_recipe_keeps_its_breaks_and_position():
    from algorithms.figure_config import load_figure_config
    from algorithms.figures.styles import finish
    from matplotlib.lines import Line2D

    fig,_=plt.subplots(constrained_layout=True)
    text='一致性上限\n均差 + 1.96s\n0.690'
    fig.legend(handles=[Line2D([],[],label=text)],loc='outside upper center')
    original=fig.legends[0]
    finish(fig,load_figure_config(dict(width_mm=150,height_mm=110)))
    assert fig.legends[0] is original
    assert fig.legends[0].get_texts()[0].get_text()==text
    plt.close(fig)


def test_trajectory_keeps_order_arrows_and_explains_rank_not_physical_time():
    data=dict(embedding=[[0,0],[3,1],[1,2]],time=[5,1,3])
    fig=get_figure('embedding_trajectory')(data=data,mode='preview',simulated=True)
    axis=fig.axes[0]
    np.testing.assert_array_equal(axis.lines[0].get_xydata(),[[3,1],[1,2],[0,0]])
    np.testing.assert_array_equal(axis.collections[0].get_array(),[0,1,2])
    np.testing.assert_array_equal(axis.collections[1].get_offsets(),[[3,1]])
    np.testing.assert_array_equal(axis.collections[2].get_offsets(),[[0,0]])
    assert sum(hasattr(t,'arrow_patch') for t in axis.texts)==2
    assert [t.get_text() for t in fig.legends[0].get_texts()]==['起点','终点']
    assert ''.join(fig.axes[1].get_ylabel().split())=='时间排序序号（从0开始）'
    plt.close(fig)


def test_long_legends_keep_different_units_for_identically_named_entries():
    from algorithms.figure_config import load_figure_config
    from algorithms.figures.styles import finish
    from matplotlib.lines import Line2D

    fig,axis=plt.subplots(constrained_layout=True)
    label='这是需要完整保留说明的同名观测序列'
    for title in ('流量单位m³/s','长度单位mm'):
        fig.legend(handles=[Line2D([],[],label=label)],title=title)
    finish(fig,load_figure_config(dict(width_mm=150,height_mm=150)))
    labels=[t.get_text() for t in fig.legends[0].get_texts()]
    assert len(labels)==2
    assert '流量单位m³/s' in labels[0] and '长度单位mm' in labels[1]
    assert all(''.join(label.split()) in ''.join(t.split()) for t in labels)
    plt.close(fig)


@pytest.mark.parametrize('coordinates,label',[
    ([0,1,2],'迭代次数'),
    ([0,.342857,.685714],'迭代坐标（调用者提供）'),
])
def test_convergence_labels_supplied_coordinates_without_rounding(coordinates,label):
    fig=get_figure('convergence')(data=dict(iterations=coordinates,objective=[3.,1.,1.5]),
                                 mode='preview',simulated=True)
    assert ''.join(fig.axes[0].get_xlabel().split())==label
    np.testing.assert_array_equal(fig.axes[0].lines[0].get_xdata(),coordinates)
    np.testing.assert_array_equal(fig.axes[0].lines[0].get_ydata(),[3.,1.,1.5])
    plt.close(fig)


def test_convergence_keeps_explicit_coordinate_unit_caption():
    fig=get_figure('convergence')(data=dict(iterations=[0.,.5,1.],objective=[3.,2.,1.]),
                                 xlabel='归一化迭代进度',simulated=True,mode='preview')
    assert fig.axes[0].get_xlabel()=='归一化迭代进度'
    plt.close(fig)


@pytest.mark.parametrize('text,width',[
    ('完整统计口径（长期综合测量指标）',12),
    ('embedding_trajectory：完整中文说明',20),
    ('完整说明（保持来源）【原值】',5),
])
def test_caption_wrapping_keeps_punctuation_with_its_text(text,width):
    from algorithms.figures.styles import wrap_label

    actual=wrap_label(text,width)
    assert ''.join(actual.split())==''.join(text.split())
    assert all(not line.startswith(('）','】','：',')',']',':')) for line in actual.splitlines())
    assert all(not line.endswith(('（','【','(', '[')) for line in actual.splitlines())

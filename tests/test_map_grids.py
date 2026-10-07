"""The map grids published in Oldgrowth (scripts/gen/map_grids.py): height levels from the physics surface, the
vision blocker cells, deterministic gzip. numpy runs on the owner's PC; CI has none, so these skip there."""
import gzip
import os
import sys

import pytest

np = pytest.importorskip("numpy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts", "gen"))

import map_grids as mg  # noqa: E402

GRID = {"w": 4, "h": 3, "min_x": 0.0, "min_y": 0.0, "edge": 64.0}


def test_a_flat_square_raises_the_cells_under_it():
    # two triangles covering x 0..128, y 0..128 at z 256: the 2 x 2 cells under it, nothing elsewhere
    verts = np.array([[0, 0, 256], [128, 0, 256], [128, 128, 256], [0, 128, 256]], dtype=float)
    tris = np.array([[0, 1, 2], [0, 2, 3]])
    z = mg.rasterize_max_z(verts, tris, GRID)
    assert np.isfinite(z[:2, :2]).all() and (z[:2, :2] == 256).all() and not np.isfinite(z[2:, :]).any()


def test_levels_count_128_steps_from_the_river():
    z = np.full((10, 10), 128.0)
    z[0, :5] = 384.0
    z[1, 0] = -np.inf
    lv, z_river = mg.levels(z)
    assert z_river == 128 and lv[5, 5] == 0 and lv[0, 0] == 2 and lv[1, 0] == mg.NODATA


def test_a_blocker_node_marks_its_cell_only_from_default_ents():
    ents = [{"classname": "ent_fow_blocker_node", "_lump": "default_ents", "origin": [70.0, 130.0, 0.0]},
            {"classname": "ent_fow_blocker_node", "_lump": "world_layer_x", "origin": [10.0, 10.0, 0.0]},
            {"classname": "ent_dota_tree", "_lump": "default_ents", "origin": "200 10 0"}]
    fow = mg.fow_grid(ents, GRID)
    assert fow.sum() == 1 and fow[2, 1] == 1                     # row = y / 64, column = x / 64


def test_the_gzip_is_the_same_bytes_every_time(tmp_path):
    a, b = str(tmp_path / "a.gz"), str(tmp_path / "b.gz")
    mg._write_gz(a, b"cells")
    mg._write_gz(b, b"cells")
    with open(a, "rb") as fa, open(b, "rb") as fb:
        assert fa.read() == fb.read()
    assert gzip.decompress(open(a, "rb").read()) == b"cells"

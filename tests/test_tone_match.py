"""The colour look of our in-game map pictures (scripts/gen/tone_match.py; the owner 2026-10-01: "our map is too
bright, it should look like leamare's"): a colour lookup table fitted once on 7.41, applied to every picture."""
import os
import sys

import numpy as np
from PIL import Image

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "scripts", "gen"))
import tone_match as tm  # noqa: E402


def _picture(path, tint):
    rng = np.random.default_rng(7)
    px = rng.uniform(0.15, 0.85, size=(64, 64, 3)) * np.array(tint)
    Image.fromarray((np.clip(px, 0, 1) * 255).astype(np.uint8)).save(path)
    return Image.open(path).convert("RGB")


def test_the_fitted_table_carries_one_pictures_colours_onto_the_other(tmp_path):
    ours = _picture(tmp_path / "ours.png", (1.0, 1.0, 0.8))             # warm and bright, as the game shows it
    ref = _picture(tmp_path / "ref.png", (0.8, 0.9, 0.8))               # darker, greener
    lut = tm.table(tm.fit(str(tmp_path / "ours.png"), str(tmp_path / "ref.png")))
    got = np.asarray(tm.apply(ours, lut), np.float64).reshape(-1, 3).mean(axis=0)
    want = np.asarray(ref, np.float64).reshape(-1, 3).mean(axis=0)
    assert np.abs(got - want).max() < 4                                 # of 255


def test_the_contrast_survives_a_washed_out_fit_was_the_first_try(tmp_path):
    ours = _picture(tmp_path / "ours.png", (1.0, 1.0, 1.0))
    ref = _picture(tmp_path / "ref.png", (0.9, 0.9, 0.9))
    lut = tm.table(tm.fit(str(tmp_path / "ours.png"), str(tmp_path / "ref.png")))
    got = np.asarray(tm.apply(ours, lut), np.float64)
    assert got.std() > 0.8 * np.asarray(ref, np.float64).std()


def test_the_table_survives_saving(tmp_path, monkeypatch):
    monkeypatch.setattr(tm, "LUT", str(tmp_path / "lut.png"))
    v = np.linspace(0, 1, tm.SIZE)
    b, g, r = np.meshgrid(v, v, v, indexing="ij")
    ident = np.stack([r.ravel(), g.ravel(), b.ravel()], axis=1)
    tm.save(ident)
    assert np.abs(tm.load() - ident).max() <= 0.5 / 255 + 1e-9
    im = Image.new("RGB", (8, 8), (40, 120, 200))
    assert np.asarray(tm.apply(im)).reshape(-1, 3)[0].tolist() == [40, 120, 200]


def test_the_stored_table_is_there_and_darkens_the_lime_grass():
    assert os.path.exists(tm.LUT)
    lime = Image.new("RGB", (4, 4), (150, 170, 60))                     # the game's grass
    r, g, b = np.asarray(tm.apply(lime)).reshape(-1, 3)[0]
    assert g < 170 and r < 150

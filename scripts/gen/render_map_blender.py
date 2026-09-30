"""Render the Dota map from above with Blender, from a glTF export of the game's own map (no screenshots, no
third-party tiles). Run by scripts/gen/render_map.py, not by hand:

    blender -b --factory-startup -P scripts/gen/render_map_blender.py -- <glb> <out.png> <x0> <x1> <y0> <y1> <px>
                                                                          [probe]

x0..x1 / y0..y1: the world rectangle (game units) the picture covers — the one our map images use
(data/terrain_map_meta.json), so the site's markers land where they did. px: the width in pixels; the height
follows the rectangle. The map is rendered in tiles (one camera per tile) and stitched by the caller.
"probe" instead prints where the importer put the map, to check the axes.

Light as the map sets it: env_global_light angles [66, 0, 0] (pitch 66° down, from the west), colour 216 208 207;
a soft sky of the map's ambient colour.
"""
import math
import os
import sys

import bpy

INCH = 0.0254            # the exporter writes metres; a game unit is an inch
TILES = 4                # 4 x 4 tiles


def args():
    a = sys.argv[sys.argv.index("--") + 1:]
    return a[0], a[1], *map(float, a[2:6]), int(a[6]), (a[7] if len(a) > 7 else ""), (a[8] if len(a) > 8 else "")


def _lin(c):
    """An sRGB colour (the material files' tints) -> linear, as Blender wants."""
    return [((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92 for v in c]


def _node(nt, kind, **inputs):
    n = nt.nodes.new(kind)
    for k, v in inputs.items():
        n.inputs[k].default_value = v
    return n


def _math(nt, op, a, b=None):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            nt.links.new(v, n.inputs[i])
    return n.outputs[0]


def _image(nt, path, vector, non_color=False):
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(path, check_existing=True)
    if non_color:
        t.image.colorspace_settings.name = "Non-Color"
    nt.links.new(vector, t.inputs["Vector"])
    return t


def _smooth(nt, weight, mask, soft):
    """ApplyBlendModulation: smoothstep(max(0, mask - soft), min(1, mask + soft), weight)."""
    lo = _math(nt, "MAXIMUM", _math(nt, "SUBTRACT", mask, soft), 0.0)
    hi = _math(nt, "MINIMUM", _math(nt, "ADD", mask, soft), 1.0)
    r = nt.nodes.new("ShaderNodeMapRange")
    r.interpolation_type = "SMOOTHSTEP"
    r.clamp = True
    nt.links.new(weight, r.inputs["Value"])
    nt.links.new(lo, r.inputs["From Min"])
    nt.links.new(hi, r.inputs["From Max"])
    return r.outputs["Result"]


def build_blend(mat, spec):
    """The ground's multiblend material as ValveResourceFormat's renderer draws it (multiblend.frag.slang): per layer
    colour x tint (tint <-> tintB by the tint mask), layers 1-3 laid over layer 0 by the vertex weights
    (_TEXCOORD_1) softened against each layer's reveal mask by _TEXCOORD_2, all times the painted vertex tint
    (_TEXCOORD_3, sRGB)."""
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = _node(nt, "ShaderNodeBsdfPrincipled", Roughness=0.9)
    bsdf.inputs["Specular IOR Level"].default_value = 0.15
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    uv = nt.nodes.new("ShaderNodeUVMap").outputs["UV"]
    attr = []
    for i in (1, 2, 3):
        a = nt.nodes.new("ShaderNodeAttribute")
        a.attribute_name = f"_TEXCOORD_{i}"
        attr.append(a)
    wsep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(attr[0].outputs["Color"], wsep.inputs["Color"])
    ssep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(attr[1].outputs["Color"], ssep.inputs["Color"])
    colors, alphas = [], []
    for i, L in enumerate(spec["layers"]):
        m = nt.nodes.new("ShaderNodeMapping")
        m.vector_type = "POINT"
        m.inputs["Location"].default_value = (0.5 + L["offset"][0], 0.5 + L["offset"][1], 0)
        m.inputs["Rotation"].default_value = (0, 0, math.radians(L["rotate"]))
        s = 1.0 / (L["scale"] or 1.0)
        m.inputs["Scale"].default_value = (s, s, 1)
        nt.links.new(uv, m.inputs["Vector"])
        vec = m.outputs["Vector"]
        col = _image(nt, L["color"], vec).outputs["Color"] if L["color"] else None
        if col is None:
            colors.append(None)
            alphas.append(1.0)
            continue
        tint = _node(nt, "ShaderNodeMix", Factor=1.0)
        tint.data_type = "RGBA"
        tint.inputs[6].default_value = (*_lin(L["tintB"]), 1)       # A
        tint.inputs[7].default_value = (*_lin(L["tint"]), 1)        # B
        if spec.get("tintmask") and L["tintmask"]:
            tm = _image(nt, L["tintmask"], vec, non_color=True)
            ch = nt.nodes.new("ShaderNodeSeparateColor")
            nt.links.new(tm.outputs["Color"], ch.inputs["Color"])
            nt.links.new(tm.outputs["Alpha"] if i == 3 else ch.outputs[min(i, 2)], tint.inputs["Factor"])
        mul = _node(nt, "ShaderNodeMix", Factor=1.0)
        mul.data_type = "RGBA"
        mul.blend_type = "MULTIPLY"
        nt.links.new(col, mul.inputs[6])
        nt.links.new(tint.outputs[2], mul.inputs[7])
        colors.append(mul.outputs[2])
        alphas.append(_image(nt, L["reveal"], vec, non_color=True).outputs["Color"] if L["reveal"] else 1.0)
    # the weights
    b = [None, None, None, None]
    rest = 1.0
    for i in (1, 2, 3):
        if i >= len(colors) or colors[i] is None:
            b[i] = 0.0
            continue
        bw = _smooth(nt, wsep.outputs[i - 1], alphas[i] if not isinstance(alphas[i], float) else 1.0,
                     ssep.outputs[i - 1])
        b[i] = bw if i == 1 else _math(nt, "MINIMUM", bw, rest)
        rest = _math(nt, "SUBTRACT", rest, b[i])
    b[0] = rest
    total = None
    for i, c in enumerate(colors):
        if c is None or isinstance(b[i], float) and b[i] == 0.0:
            continue
        sc = _node(nt, "ShaderNodeVectorMath")
        sc.operation = "SCALE"
        nt.links.new(c, sc.inputs[0])
        if isinstance(b[i], float):
            sc.inputs["Scale"].default_value = b[i]
        else:
            nt.links.new(b[i], sc.inputs["Scale"])
        if total is None:
            total = sc.outputs[0]
        else:
            add = _node(nt, "ShaderNodeVectorMath")
            add.operation = "ADD"
            nt.links.new(total, add.inputs[0])
            nt.links.new(sc.outputs[0], add.inputs[1])
            total = add.outputs[0]
    # x the painted vertex tint (sRGB -> linear), x a gain for Blender's lighting
    gamma = _node(nt, "ShaderNodeGamma", Gamma=2.2)
    nt.links.new(attr[2].outputs["Color"], gamma.inputs["Color"])
    tinted = _node(nt, "ShaderNodeVectorMath")
    tinted.operation = "MULTIPLY"
    nt.links.new(total, tinted.inputs[0])
    nt.links.new(gamma.outputs[0], tinted.inputs[1])
    gain = _node(nt, "ShaderNodeVectorMath")
    gain.operation = "SCALE"
    gain.inputs["Scale"].default_value = GROUND_GAIN
    nt.links.new(tinted.outputs[0], gain.inputs[0])
    nt.links.new(gain.outputs[0], bsdf.inputs["Base Color"])


GROUND_GAIN = 1.6        # the game lights its ground ~2x brighter than a plain diffuse surface (x2 in the shader)


def fix_materials(manifest):
    """The exporter's quirks: every reflectance map went into Emission (a white glowing ground) — off; the ground
    multiblends rebuilt from the manifest; water (exported plain white) dark teal; river flow overlays hidden."""
    import json
    import re
    man = {}
    if manifest and os.path.exists(manifest):
        with open(manifest, encoding="utf-8") as f:
            man = json.load(f)
    for mat in bpy.data.materials:
        if not mat.use_nodes:
            continue
        base = re.sub(r"\.\d{3}$", "", mat.name)
        if base in man:
            build_blend(mat, man[base])
            continue
        bsdf = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if not bsdf:
            continue
        bsdf.inputs["Emission Strength"].default_value = 0.0
        low = base.lower()
        if "water" in low:
            for l in list(bsdf.inputs["Base Color"].links):
                mat.node_tree.links.remove(l)
            bsdf.inputs["Base Color"].default_value = (0.020, 0.055, 0.060, 1)
            bsdf.inputs["Roughness"].default_value = 0.15
        elif "riverflow" in low or "river_flow" in low:
            for l in list(bsdf.inputs["Alpha"].links):
                mat.node_tree.links.remove(l)
            bsdf.inputs["Alpha"].default_value = 0.0


def world_to_blender(x, y):
    """Game (x east, y north) -> Blender after the glTF importer (Z up), turned a quarter: checked with the probe
    (Dire Ancient game (5528, 5000) -> Blender (5000, -5528); Radiant fountain (-7456, -6938) -> (-6936, 7512))."""
    return y * INCH, -x * INCH


CAMERA_TURN = -math.pi / 2          # so the picture's up is the game's north (+y) and its right the game's east


def setup(glb):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=glb)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 16
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "Standard"
    world = bpy.data.worlds.new("sky")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (63 / 255, 144 / 255, 169 / 255, 1)
    bg.inputs["Strength"].default_value = 0.35
    scene.world = world
    sun_data = bpy.data.lights.new("sun", type="SUN")
    sun_data.color = (216 / 255, 208 / 255, 207 / 255)
    sun_data.energy = 3.2
    sun_data.angle = math.radians(2)
    sun = bpy.data.objects.new("sun", sun_data)
    # 66° down, shining towards the game's +x = Blender's -y: its -Z tipped 24° about X
    sun.rotation_euler = (math.radians(-(90 - 66)), 0.0, 0.0)
    scene.collection.objects.link(sun)
    return scene


def probe():
    import mathutils
    lo = mathutils.Vector((1e9, 1e9, 1e9))
    hi = -lo
    names = []
    for ob in bpy.context.scene.objects:
        if ob.type != "MESH":
            continue
        for c in ob.bound_box:
            w = ob.matrix_world @ mathutils.Vector(c)
            lo = mathutils.Vector(map(min, lo, w))
            hi = mathutils.Vector(map(max, hi, w))
        if any(k in ob.name.lower() for k in ("ancient", "fountain", "fort", "tower")):
            names.append((ob.name, tuple(round(v / INCH) for v in ob.matrix_world.translation)))
    print("PROBE bounds (game units):", tuple(round(v / INCH) for v in lo), tuple(round(v / INCH) for v in hi))
    for n in names[:40]:
        print("PROBE", n)


def render(scene, out, x0, x1, y0, y1, px):
    cam_data = bpy.data.cameras.new("cam")
    cam_data.type = "ORTHO"
    cam_data.clip_start, cam_data.clip_end = 1.0, 2000.0
    cam = bpy.data.objects.new("cam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    w, h = x1 - x0, y1 - y0
    tw, th = w / TILES, h / TILES
    scene.render.resolution_x = px // TILES
    scene.render.resolution_y = round(px * h / w) // TILES
    scene.render.resolution_percentage = 100
    cam_data.sensor_fit = "HORIZONTAL"
    cam_data.ortho_scale = tw * INCH
    for row in range(TILES):                 # row 0 = the top (north) of the picture
        for col in range(TILES):
            cx, cy = world_to_blender(x0 + tw * (col + 0.5), y1 - th * (row + 0.5))
            cam.location = (cx, cy, 500.0)
            cam.rotation_euler = (0.0, 0.0, CAMERA_TURN)
            scene.render.filepath = f"{out}.tile_{row}_{col}.png"
            bpy.ops.render.render(write_still=True)
            print(f"TILE {row} {col} done", flush=True)


def main():
    glb, out, x0, x1, y0, y1, px, mode, manifest = args()
    scene = setup(glb)
    if mode == "probe":
        probe()
        return
    fix_materials(manifest)
    render(scene, out, x0, x1, y0, y1, px)


main()

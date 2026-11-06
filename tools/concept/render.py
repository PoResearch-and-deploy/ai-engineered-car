"""Koncepció-render (Blender bpy, EEVEE): sötét stúdió + TRON-rács, egységes kamera.
Futtatás: /home/claude/work/feas/bpyenv/bin/python render.py race|truck|crane|all [--res 1600x1000] [--samples 64] [--out dir]
"""
import sys, os, math, argparse
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from models import MODELS

MESH = "/home/claude/work/video/render_v3/cache/meshes.npz"
COLORS = {"dark": ("#22252c", 0.45, 0), "red": ("#c8202a", 0.30, 0), "white": ("#e9e9e6", 0.32, 0), "orange": ("#E8650A", 0.32, 0),
          "yellow": ("#EBA000", 0.32, 0), "tyre": ("#121316", 0.85, 0), "rim": ("#c9cdd2", 0.35, 0.1), "axle": ("#3b4048", 0.4, 0),
          "pin": ("#2a2d33", 0.45, 0), "metal": ("#b8c2cc", 0.28, 0.5), "light": ("#fff2c0", 0.2, 0), "rope": ("#15161a", 0.5, 0)}


def lin(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c] + [1.0]


def build(name, res, samples, out):
    import bpy
    from mathutils import Matrix, Vector
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE_NEXT"; sc.eevee.taa_render_samples = samples
    try:
        sc.eevee.use_shadows = True; sc.eevee.use_raytracing = False; sc.eevee.fast_gi_method = 'GLOBAL_ILLUMINATION'
    except Exception as e: print("eevee", e)
    W, H = res; sc.render.resolution_x, sc.render.resolution_y = W, H; sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = 'AgX'
    try: sc.view_settings.look = 'AgX - Punchy'
    except Exception: pass
    sc.render.film_transparent = False
    # anyagok
    MAT = {}
    for k, (h, r, mtl) in COLORS.items():
        m = bpy.data.materials.new(k); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
        b.inputs['Base Color'].default_value = lin(h); b.inputs['Roughness'].default_value = r; b.inputs['Metallic'].default_value = mtl
        if k == "light":
            b.inputs['Emission Color'].default_value = lin(h); b.inputs['Emission Strength'].default_value = 4.0
        MAT[k] = m
    # modell
    Ms = np.load(MESH); mdl = MODELS[name](); meshes = {}
    pts = []
    for p, T, col in mdl.items:
        if p not in meshes:
            V, F = Ms["V_" + p], Ms["F_" + p]
            me = bpy.data.meshes.new("M_" + p); me.from_pydata(V.tolist(), [], F.tolist()); me.validate()
            try: me.shade_smooth(); me.set_sharp_from_angle(angle=math.radians(35))
            except Exception: pass
            me.materials.append(MAT["dark"]); meshes[p] = me
        o = bpy.data.objects.new(p, meshes[p]); sc.collection.objects.link(o)
        o.material_slots[0].link = 'OBJECT'; o.material_slots[0].material = MAT[col]
        S = np.eye(4); S[:3, :3] *= 0.001; S[:3, 3] = T[:3, 3] * 0.001
        M = np.eye(4); M[:3, :3] = T[:3, :3] * 0.001; M[:3, 3] = T[:3, 3] * 0.001
        o.matrix_world = Matrix(M.tolist())
        V = Ms["V_" + p][::7]
        pts.append((T[:3, :3] @ V.T).T + T[:3, 3])
    P = np.vstack(pts) * 0.001; lo, hi = P.min(0), P.max(0); ctr = (lo + hi) / 2
    print(name, "parts", len(mdl.items), "bbox mm", (lo * 1000).round(0), (hi * 1000).round(0))
    # padló: sötét, finom rács + narancs kontúr kör
    bpy.ops.mesh.primitive_plane_add(size=30.0, location=(ctr[0], ctr[1], 0)); g = bpy.context.object
    m = bpy.data.materials.new("floor"); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; Lk = nt.links
    for n in list(N): N.remove(n)
    out_ = N.new('ShaderNodeOutputMaterial'); bs = N.new('ShaderNodeBsdfPrincipled')
    bs.inputs['Base Color'].default_value = lin("#0b0e14"); bs.inputs['Roughness'].default_value = 0.35
    tc = N.new('ShaderNodeTexCoord'); sep = N.new('ShaderNodeSeparateXYZ'); Lk.new(tc.outputs['Object'], sep.inputs[0])

    def mth(op, a, b=None):
        x = N.new('ShaderNodeMath'); x.operation = op
        for i, y in enumerate([a, b]):
            if y is None: continue
            if isinstance(y, (int, float)): x.inputs[i].default_value = y
            else: Lk.new(y, x.inputs[i])
        return x.outputs[0]

    def line(c, step, w):
        f = mth('FRACT', mth('DIVIDE', c, step)); d = mth('MINIMUM', f, mth('SUBTRACT', 1.0, f))
        return mth('LESS_THAN', d, w / step)
    gl = mth('MAXIMUM', line(sep.outputs[0], 0.04, 0.0007), line(sep.outputs[1], 0.04, 0.0007))
    r = mth('SQRT', mth('ADD', mth('POWER', sep.outputs[0], 2.0), mth('POWER', sep.outputs[1], 2.0)))
    fade = mth('SUBTRACT', 1.0, mth('MINIMUM', 1.0, mth('DIVIDE', r, 0.55)))
    em = mth('MULTIPLY', gl, mth('MULTIPLY', fade, 0.9))
    bs.inputs['Emission Color'].default_value = lin("#3b6fd8")
    Lk.new(em, bs.inputs['Emission Strength'])
    Lk.new(bs.outputs[0], out_.inputs[0]); g.data.materials.append(m)
    # világ: sötétkék gradiens
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; bg = w.node_tree.nodes['Background']
    bg.inputs[0].default_value = lin("#0d1220"); bg.inputs[1].default_value = 0.6
    # fények: kulcs (meleg), töltő, kék és narancs perem
    def area(nm, loc, size, energy, col):
        ld = bpy.data.lights.new(nm, 'AREA'); ld.size = size; ld.energy = energy; ld.color = [x for x in lin(col)[:3]]
        o = bpy.data.objects.new(nm, ld); sc.collection.objects.link(o); o.location = loc
        c = o.constraints.new('TRACK_TO'); c.target = tgt
    tgt = bpy.data.objects.new("tgt", None); sc.collection.objects.link(tgt); tgt.location = tuple(ctr * [1, 1, 0.6])
    area("key", (ctr[0] + 0.35, ctr[1] - 0.45, 0.55), 0.5, 26, "#fff4e6")
    area("fill", (ctr[0] + 0.5, ctr[1] + 0.5, 0.3), 0.8, 7, "#dfe8ff")
    area("rimb", (ctr[0] - 0.55, ctr[1] + 0.3, 0.35), 0.4, 30, "#7fa6ff")
    area("rimo", (ctr[0] - 0.4, ctr[1] - 0.5, 0.2), 0.3, 18, "#F28C28")
    # kamera: 3/4 elölről, balról, enyhén felülről; távolság a befoglaló méretből
    cd = bpy.data.cameras.new("cam"); cd.lens = 50; cd.sensor_width = 36; cd.clip_start = 0.005
    cam = bpy.data.objects.new("cam", cd); sc.collection.objects.link(cam); sc.camera = cam
    az, el = math.radians(-38), math.radians(17)
    size = max(hi - lo); dist = size * 2.05
    look = ctr * [1, 1, 0.75]
    cam.location = tuple(look + dist * np.array([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)]))
    c = cam.constraints.new('TRACK_TO'); t2 = bpy.data.objects.new("lk", None); sc.collection.objects.link(t2); t2.location = tuple(look); c.target = t2
    os.makedirs(out, exist_ok=True)
    sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = os.path.join(out, f"{name}.png")
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("which"); ap.add_argument("--res", default="800x500")
    ap.add_argument("--samples", type=int, default=16); ap.add_argument("--out", default=os.path.join(HERE, "out"))
    a = ap.parse_args(); W, H = map(int, a.res.split("x"))
    for n in (MODELS if a.which == "all" else [a.which]):
        build(n, (W, H), a.samples, a.out)

"""LEGO-útmutató-stílusú minta: a bal első futómű-sarok (A6d geometria, render_v3 cache) 4 lépésben.
Blender Workbench (lapos, körvonalas) -> PIL kompozíció (alkatrész-keret, lépésszám, kiemelés, nyíl).
Futtatás: /home/claude/work/feas/bpyenv/bin/python instr.py   -> out_instr/step_1..4.png, thumbs
"""
import os, sys, math, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
RC = "/home/claude/work/video/render_v3/cache"
OUT = os.path.join(HERE, "out_instr"); os.makedirs(OUT, exist_ok=True)

STEPS = [[8, 9, 10, 53, 54, 55],      # alsó lengőkar
         [17, 18, 11],                # rugóstagok + felső kar
         [0, 3, 4, 2, 1, 12, 13, 5],  # kerékhordozó + gömbcsapok + kerékagy + nyomtávrúd
         [6, 7]]                      # kerék
COL = {"23801": "#2b2d31", "92909": "#2b2d31", "32494": "#9aa0a6", "6628": "#2b2d31", "2736": "#9aa0a6", "15038": "#c9cdd2",
       "44771": "#26272b", "31794": "#2b2d31", "32523": "#2b2d31", "57515": "#2b2d31", "32005": "#2b2d31", "76537": "#d8572a",
       "32073": "#7b8087", "4519": "#7b8087", "32123a": "#9aa0a6"}
# (az útmutató saját olvashatósági palettája: tengelyek/perselyek szürkék, a rugóstag narancs – mint a gyári Technic-útmutatókban)


def hex2(c): return [int(c[i:i + 2], 16) / 255 for i in (1, 3, 5)]


def main():
    import bpy
    from mathutils import Matrix
    D = np.load(os.path.join(RC, "scene.npz")); Ms = np.load(os.path.join(RC, "meshes.npz")); T = np.load(os.path.join(RC, "B_forgoasztal.npz"))["T"][0]
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'OBJECT'; sh.show_object_outline = True; sh.object_outline_color = (0.08, 0.08, 0.09)
    sh.show_cavity = True; sh.cavity_type = 'BOTH'; sh.show_shadows = False; sh.show_specular_highlight = True
    sc.display.render_aa = '16'
    sc.view_settings.view_transform = 'Standard'
    sc.render.film_transparent = True
    sc.render.resolution_x, sc.render.resolution_y = 1400, 1000
    ids = sorted({i for s in STEPS for i in s}); objs = {}; meshes = {}
    pts = []
    for i in ids:
        p = str(D["parts"][i])
        if p not in meshes:
            me = bpy.data.meshes.new(p); me.from_pydata(Ms["V_" + p].tolist(), [], Ms["F_" + p].tolist()); me.validate()
            try: me.shade_smooth(); me.set_sharp_from_angle(angle=math.radians(35))
            except Exception: pass
            meshes[p] = me
        o = bpy.data.objects.new(f"o{i}", meshes[p]); sc.collection.objects.link(o)
        M = T[i].astype(float).copy(); M[:3, :] *= 1e-3; M[3] = [0, 0, 0, 1]; M[:3, :3] = T[i][:3, :3]; M[:3, :3] *= 1e-3
        o.matrix_world = Matrix(M.tolist()); objs[i] = o
        pts.append((T[i][:3, :3] @ Ms["V_" + p][::5].T).T + T[i][:3, 3])
    P = np.vstack(pts) * 1e-3; ctr = (P.min(0) + P.max(0)) / 2
    cd = bpy.data.cameras.new("c"); cd.type = 'ORTHO'; cd.ortho_scale = 0.16
    cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
    dirv = np.array([0.75, 0.85, 0.62]); dirv /= np.linalg.norm(dirv)
    cam.location = tuple(ctr + dirv * 1.0)
    tg = bpy.data.objects.new("t", None); sc.collection.objects.link(tg); tg.location = tuple(ctr)
    c = cam.constraints.new('TRACK_TO'); c.target = tg; c.up_axis = 'UP_Y'
    meta = {"steps": []}

    def shot(path):
        sc.render.filepath = path; bpy.ops.render.render(write_still=True)

    done = []
    for k, st in enumerate(STEPS):
        vis = set(done + st)
        for i, o in objs.items():
            o.hide_render = i not in vis
            base = np.array(hex2(COL.get(str(D["parts"][i]), "#2b2d31")))
            if i in done: base = base * 0.45 + 0.55 * np.array([0.93, 0.95, 0.97])   # előző lépés: halványítva
            o.color = (*base, 1.0)
        shot(os.path.join(OUT, f"s{k + 1}_col.png"))
        for i, o in objs.items(): o.color = (1, 0, 1, 1) if i in st else (1, 1, 1, 1)
        sh.show_object_outline = False; sh.show_cavity = False; sh.light = 'FLAT'
        shot(os.path.join(OUT, f"s{k + 1}_mask.png"))
        sh.show_object_outline = True; sh.show_cavity = True; sh.light = 'STUDIO'
        cnt = {}
        for i in st: cnt[str(D["parts"][i])] = cnt.get(str(D["parts"][i]), 0) + 1
        meta["steps"].append({"new": cnt}); done += st
    # alkatrész-bélyegképek: minden új elem egyedül, saját kerettel
    sc.render.resolution_x, sc.render.resolution_y = 300, 300
    seen = set()
    for i, o in objs.items():
        p = str(D["parts"][i])
        if p in seen: continue
        seen.add(p)
        for j, oo in objs.items(): oo.hide_render = j != i
        o.color = (*hex2(COL.get(p, "#2b2d31")), 1)
        V = (T[i][:3, :3] @ Ms["V_" + p].T).T * 1e-3 + T[i][:3, 3] * 1e-3
        cc = (V.min(0) + V.max(0)) / 2; tg.location = tuple(cc); cam.location = tuple(cc + dirv * 1.0)
        cd.ortho_scale = float(np.max(V.max(0) - V.min(0))) * 1.25
        shot(os.path.join(OUT, f"t_{p}.png"))
    json.dump(meta, open(os.path.join(OUT, "meta.json"), "w"), indent=1)


if __name__ == "__main__":
    main()

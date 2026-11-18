"""Super-resolução x4 (Real-ESRGAN realesr-general-x4v3, SRVGGNetCompact) sem PyTorch:
lê o .pth (zip+pickle) com um unpickler próprio, monta o grafo ONNX e roda no onnxruntime (CPU).
Uso: from sr import Upscaler; up = Upscaler(models_dir); big = up(rgb_uint8)  # (h,w,3) -> (4h,4w,3)"""
import os, pickle, zipfile, collections
import numpy as np

def load_pth(path):
    zf = zipfile.ZipFile(path); root = zf.namelist()[0].split("/")[0]
    dt = {"FloatStorage": np.float32, "HalfStorage": np.float16, "DoubleStorage": np.float64, "LongStorage": np.int64}
    class Stor:
        def __init__(s, name): s.name = name
    def rebuild(storage, offset, size, stride, *a):
        buf = np.frombuffer(zf.read(f"{root}/data/{storage[1]}"), dtype=storage[0])
        n = int(np.prod(size)) if len(size) else 1
        arr = np.lib.stride_tricks.as_strided(buf[offset:], shape=size, strides=[s * buf.itemsize for s in stride]) if len(size) else buf[offset:offset + 1].reshape(())
        return np.array(arr, dtype=np.float32)
    class U(pickle.Unpickler):
        def find_class(s, mod, name):
            if name == "_rebuild_tensor_v2": return rebuild
            if name.endswith("Storage"): return dt[name]
            if name == "OrderedDict": return collections.OrderedDict
            raise pickle.UnpicklingError(f"{mod}.{name}")
        def persistent_load(s, pid):  # ('storage', dtype, key, location, numel)
            return (pid[1], pid[2])
    sd = U(zf.open(f"{root}/data.pkl")).load()
    return sd.get("params", sd.get("params_ema", sd))

def build_onnx(sd, out, scale=4):
    import onnx
    from onnx import helper as h, TensorProto as T, numpy_helper as nh
    keys = sorted({int(k.split(".")[1]) for k in sd}, key=int)
    nodes, inits, x = [], [], "inp"
    for idx in keys:
        w = sd[f"body.{idx}.weight"]
        if w.ndim == 4:
            inits += [nh.from_array(w, f"w{idx}"), nh.from_array(sd[f"body.{idx}.bias"], f"b{idx}")]
            nodes.append(h.make_node("Conv", [x, f"w{idx}", f"b{idx}"], [f"y{idx}"], pads=[1, 1, 1, 1])); x = f"y{idx}"
        else:
            inits.append(nh.from_array(w.reshape(-1, 1, 1), f"a{idx}"))
            nodes.append(h.make_node("PRelu", [x, f"a{idx}"], [f"y{idx}"])); x = f"y{idx}"
    nodes.append(h.make_node("DepthToSpace", [x], ["ps"], blocksize=scale, mode="CRD"))
    inits.append(nh.from_array(np.array([1, 1, scale, scale], np.float32), "sc"))
    nodes.append(h.make_node("Resize", ["inp", "", "sc"], ["up"], mode="nearest"))
    nodes.append(h.make_node("Add", ["ps", "up"], ["out"]))
    g = h.make_graph(nodes, "srvgg", [h.make_tensor_value_info("inp", T.FLOAT, [1, 3, None, None])],
                     [h.make_tensor_value_info("out", T.FLOAT, [1, 3, None, None])], inits)
    m = h.make_model(g, opset_imports=[h.make_opsetid("", 17)]); m.ir_version = 8
    onnx.save(m, out)

class Upscaler:
    def __init__(self, models_dir, threads=None):
        import onnxruntime as ort
        p = f"{models_dir}/esrgan/realesr-general-x4v3.onnx"
        if not os.path.exists(p): build_onnx(load_pth(f"{models_dir}/esrgan/realesr-general-x4v3.pth"), p)
        o = ort.SessionOptions()
        if threads: o.intra_op_num_threads = threads
        self.s = ort.InferenceSession(p, o, providers=["CPUExecutionProvider"])
    def __call__(self, rgb):
        x = (rgb.astype(np.float32) / 255.0).transpose(2, 0, 1)[None]
        y = self.s.run(None, {"inp": x})[0][0]
        return (np.clip(y, 0, 1).transpose(1, 2, 0) * 255 + 0.5).astype(np.uint8)

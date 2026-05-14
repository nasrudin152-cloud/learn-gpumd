#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import argparse
import numpy as np


def fmt(x):
    return f"{float(x):.16g}"


def load_type_map(path):
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def load_types(path):
    arr = np.loadtxt(path, dtype=int)
    arr = np.atleast_1d(arr).astype(int)
    return arr.tolist()


def reshape_box(box, nframes):
    box = np.asarray(box)
    if box.shape == (nframes, 3, 3):
        return box
    if box.size == nframes * 9:
        return box.reshape(nframes, 3, 3)
    raise ValueError(f"box shape not understood: {box.shape}")


def reshape_per_atom(arr, nframes, natoms):
    arr = np.asarray(arr)
    if arr.shape == (nframes, natoms, 3):
        return arr
    if arr.size == nframes * natoms * 3:
        return arr.reshape(nframes, natoms, 3)
    raise ValueError(f"per-atom array shape not understood: {arr.shape}")


def reshape_virial(virial, nframes):
    if virial is None:
        return None
    virial = np.asarray(virial)
    if virial.shape == (nframes, 3, 3):
        return virial.reshape(nframes, 9)
    if virial.size == nframes * 9:
        return virial.reshape(nframes, 9)
    raise ValueError(f"virial shape not understood: {virial.shape}")


def write_frame(fh, species, cell, pos, force, energy, virial=None, source=None):
    natoms = len(species)
    fh.write(f"{natoms}\n")

    lattice = " ".join(fmt(x) for x in np.asarray(cell).reshape(9))
    header_items = [
        f'Lattice="{lattice}"',
        f"energy={fmt(energy)}",
        "Properties=species:S:1:pos:R:3:force:R:3",
    ]

    if virial is not None:
        vir = " ".join(fmt(x) for x in np.asarray(virial).reshape(9))
        header_items.append(f'virial="{vir}"')

    if source is not None:
        header_items.append(f'source="{source}"')

    fh.write(" ".join(header_items) + "\n")

    for s, p, f in zip(species, pos, force):
        fh.write(
            f"{s} {fmt(p[0])} {fmt(p[1])} {fmt(p[2])} "
            f"{fmt(f[0])} {fmt(f[1])} {fmt(f[2])}\n"
        )


def collect_data_dirs(root):
    data_dirs = []
    for set_dir in sorted(root.rglob("set.000")):
        data_dir = set_dir.parent
        if (data_dir / "type.raw").exists() and (data_dir / "type_map.raw").exists():
            data_dirs.append(data_dir)
    # 去重
    data_dirs = sorted(set(data_dirs))
    return data_dirs


def which_split(data_dir):
    name = data_dir.name
    if name == "validation_data":
        return "test"
    # training_data 和其他目录（如 dpgen_supply/001）默认归入 train
    return "train"


def process_one_dir(data_dir, train_fh, test_fh, all_fh=None, with_virial=False):
    set_dir = data_dir / "set.000"

    type_map_file = data_dir / "type_map.raw"
    type_file = data_dir / "type.raw"
    box_file = set_dir / "box.npy"
    coord_file = set_dir / "coord.npy"
    energy_file = set_dir / "energy.npy"
    force_file = set_dir / "force.npy"
    virial_file = set_dir / "virial.npy"

    required = [type_map_file, type_file, box_file, coord_file, energy_file, force_file]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        print(f"[SKIP] missing files in {data_dir}:")
        for m in missing:
            print("   ", m)
        return 0

    type_map = load_type_map(type_map_file)
    atom_types = load_types(type_file)
    natoms = len(atom_types)
    species = [type_map[i] for i in atom_types]

    energy = np.load(energy_file).reshape(-1)
    nframes = len(energy)

    box = reshape_box(np.load(box_file), nframes)
    coord = reshape_per_atom(np.load(coord_file), nframes, natoms)
    force = reshape_per_atom(np.load(force_file), nframes, natoms)

    virial = None
    if with_virial and virial_file.exists():
        virial = reshape_virial(np.load(virial_file), nframes)

    split = which_split(data_dir)
    main_fh = train_fh if split == "train" else test_fh

    count = 0
    rel_source = str(data_dir)

    for i in range(nframes):
        v = virial[i] if virial is not None else None
        write_frame(
            main_fh, species, box[i], coord[i], force[i], energy[i],
            virial=v, source=rel_source
        )
        if all_fh is not None:
            write_frame(
                all_fh, species, box[i], coord[i], force[i], energy[i],
                virial=v, source=rel_source
            )
        count += 1

    print(f"[OK] {data_dir} -> {split} ({count} frames)")
    return count


def main():
    parser = argparse.ArgumentParser(
        description="Merge DeepMD/DPGEN-style labeled datasets into GPUMD extxyz."
    )
    parser.add_argument("root", help="root directory, e.g. /home/marunlin/gpumd/surface-reconstruction/Dataset")
    parser.add_argument("--train", default="train.xyz", help="output train xyz")
    parser.add_argument("--test", default="test.xyz", help="output test xyz")
    parser.add_argument("--all", default=None, help="optional merged all-in-one xyz")
    parser.add_argument(
        "--with-virial",
        action="store_true",
        help="write virial if virial.npy exists"
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    data_dirs = collect_data_dirs(root)

    if not data_dirs:
        raise RuntimeError(f"No valid dataset dirs found under: {root}")

    total_train = 0
    total_test = 0

    with open(args.train, "w", encoding="utf-8") as train_fh, \
         open(args.test, "w", encoding="utf-8") as test_fh, \
         (open(args.all, "w", encoding="utf-8") if args.all else open("/dev/null", "w")) as all_fh:

        real_all_fh = None if args.all is None else all_fh

        for d in data_dirs:
            n = process_one_dir(
                d, train_fh, test_fh, all_fh=real_all_fh, with_virial=args.with_virial
            )
            if which_split(d) == "train":
                total_train += n
            else:
                total_test += n

    print()
    print(f"Done.")
    print(f"train frames = {total_train}")
    print(f"test  frames = {total_test}")
    print(f"train file   = {args.train}")
    print(f"test  file   = {args.test}")
    if args.all:
        print(f"all   file   = {args.all}")


if __name__ == "__main__":
    main()

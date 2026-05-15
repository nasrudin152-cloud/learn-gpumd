#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import numpy as np
from ase.io import read


def cell_heights(cell):
    """
    对任意 3x3 晶胞矩阵，计算三组平行晶面间距 h_a, h_b, h_c
    cell[0]=a, cell[1]=b, cell[2]=c
    """
    a = np.array(cell[0], dtype=float)
    b = np.array(cell[1], dtype=float)
    c = np.array(cell[2], dtype=float)

    V = abs(np.dot(a, np.cross(b, c)))
    if V < 1e-12:
        raise ValueError("Cell volume is too small or zero.")

    h_a = V / np.linalg.norm(np.cross(b, c))
    h_b = V / np.linalg.norm(np.cross(a, c))
    h_c = V / np.linalg.norm(np.cross(a, b))

    return h_a, h_b, h_c


def safe_cutoff(cell):
    """
    最大安全径向截断半径 = min(h_a, h_b, h_c) / 2
    """
    hs = cell_heights(cell)
    return 0.5 * min(hs), hs


def main():
    if len(sys.argv) < 2:
        print("用法: python3 check_cutoff_from_trainxyz.py train.xyz")
        sys.exit(1)

    xyzfile = sys.argv[1]

    frames = read(xyzfile, index=":")
    if len(frames) == 0:
        print("没有读到任何结构。")
        sys.exit(1)

    global_min_rcut = None
    global_min_frame = None

    print("{:>8s} {:>12s} {:>12s} {:>12s} {:>14s}".format(
        "Frame", "h_a(Å)", "h_b(Å)", "h_c(Å)", "r_cut_max(Å)"
    ))

    for i, atoms in enumerate(frames):
        cell = atoms.cell.array
        rcut, hs = safe_cutoff(cell)

        print("{:8d} {:12.6f} {:12.6f} {:12.6f} {:14.6f}".format(
            i, hs[0], hs[1], hs[2], rcut
        ))

        if (global_min_rcut is None) or (rcut < global_min_rcut):
            global_min_rcut = rcut
            global_min_frame = i

    print("\n最严格的一帧:")
    print("  frame index   = {}".format(global_min_frame))
    print("  max safe rcut = {:.6f} Å".format(global_min_rcut))
    print("建议实际 cutoff 略小一些，例如 {:.3f} Å".format(global_min_rcut - 0.2))


if __name__ == "__main__":
    main()

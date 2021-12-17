#!/usr/bin/env python3
"""
3D array float write benchmark

Note: A reasonable minimum file size is necessary to get useful results, say
50-100 MB or more file size.
Too-small files bias results unfairly against fixed MPI overhead, whereas real-world
MPI problems of interest are likely to be larger.
"""

from __future__ import annotations
import typing as T
import time
import subprocess
import shutil
import argparse
from pathlib import Path

R = Path(__file__).parent.resolve()

TIMEOUT = 600


def cli() -> dict[str, T.Any]:
    p = argparse.ArgumentParser(description="Benchmark slab")
    p.add_argument(
        "-B",
        "--binary_dir",
        help="Path to the binary directory",
        default=R / "../build",
    )
    p.add_argument(
        "-n", help="total size of slab", type=int, nargs=3, default=[10000, 32, 64]
    )
    p.add_argument("-Nrun", help="number of test runs", type=int, default=5)
    p.add_argument("-np", help="number of MPI processes", type=int)
    P = p.parse_args()

    bin_dir = Path(P.binary_dir).resolve()
    if not bin_dir.is_dir():
        raise NotADirectoryError(
            f"{bin_dir} is not a directory. Please build HDF5 benchmarks with cmake as per Readme."
        )

    print(f"Slab size: {P.n}")

    params = {
        "bin_dir": bin_dir,
        "Nrun": P.Nrun,
        "lx": P.n,
        "np": P.np,
    }

    return params


def serial_runner(
    exe_name: str,
    bin_dir: Path,
    Nrun: int,
    lx: tuple[int, int, int],
    comp_lvl: int,
    np: int = None,
) -> float:
    """
    Serial without MPI
    """

    exe = shutil.which(exe_name, path=bin_dir)
    if not exe:
        raise FileNotFoundError(f"{exe_name} not found in {bin_dir}")

    args = list(map(str, lx)) + [
        "-o",
        "out.h5",
        "-Nrun",
        str(Nrun),
        "-comp",
        str(comp_lvl),
    ]
    if np:
        args += ["-np", str(np)]

    tic = time.monotonic()
    subprocess.check_call([exe] + args, timeout=TIMEOUT)

    return time.monotonic() - tic


def mpi_runner(
    exe_name: str,
    bin_dir: Path,
    Nrun: int,
    lx: tuple[int, int, int],
    comp_lvl: int,
    np: int = None,
) -> float:
    """
    Runner frontend uses HWLOC to compute physical core count
    """

    runner_exe = shutil.which("runner", path=bin_dir)
    if not runner_exe:
        raise FileNotFoundError(f"runner not found in {bin_dir}")

    exe = shutil.which(exe_name, path=bin_dir)
    if not exe:
        raise FileNotFoundError(f"{exe_name} not found in {bin_dir}")
    mpiexec = shutil.which("mpiexec")
    if not mpiexec:
        raise FileNotFoundError("mpiexec not found")
    args = list(map(str, lx)) + [
        "-exe",
        exe,
        "-o",
        "out.h5",
        "-mpiexec",
        mpiexec,
        "-Nrun",
        str(Nrun),
        "-comp",
        str(comp_lvl),
    ]

    if np:
        args += ["-np", str(np)]

    tic = time.monotonic()
    subprocess.check_call([runner_exe] + args, timeout=TIMEOUT)

    return time.monotonic() - tic


if __name__ == "__main__":
    t = {}
    P = cli()
    for comp in (0, 1, 3, 5):
        # %% Serial (no MPI at all)
        t[f"serial_comp{comp}"] = serial_runner(
            "slab_serial", P["bin_dir"], P["Nrun"], P["lx"], comp_lvl=comp, np=P["np"]
        )
        # %% MPI transfer to root (inefficient relative to HDF5-MPI)
        t[f"mpi_root_comp{comp}"] = mpi_runner(
            "slab_mpi_serial",
            P["bin_dir"],
            P["Nrun"],
            P["lx"],
            comp_lvl=comp,
            np=P["np"],
        )
        # %% HDF5-MPI layer (most efficient general I/O approach for parallel computation)
        t[f"mpi_hdf5_comp{comp}"] = mpi_runner(
            "slab_mpi", P["bin_dir"], P["Nrun"], P["lx"], comp_lvl=comp, np=P["np"]
        )

    print("-----------------------")
    print("slab benchmark results:")
    for k, v in t.items():
        print(f"{k}: {v:0.2f} sec")

"""Command-line interface for las-filter package."""
import argparse
import sys
from pathlib import Path
from . import core

def parse_args(argv):
    p = argparse.ArgumentParser(prog="las-filter", description="Filter and downsample LAS/LAZ point clouds")
    p.add_argument("input", help="Input LAS file or directory")
    p.add_argument("output", help="Output file or directory")
    p.add_argument("--downsample", type=int, default=None, help="Downsample to N points (final)")
    p.add_argument("--algo", choices=["zor"], default="zor", help="Cleaning algorithm")
    p.add_argument("--M", type=int, default=100, help="Grid size for local filter")
    p.add_argument("--K", type=int, default=10, help="Number of neighbors for local mean")
    p.add_argument("--sigma", type=float, default=2.0, help="Sigma multiplier for local filtering")
    return p.parse_args(argv)

def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    inp = Path(args.input)
    out = Path(args.output)
    if inp.is_dir():
        out.mkdir(parents=True, exist_ok=True)
        print(f"Processing directory {inp} -> {out}")
        if args.downsample is not None:
            # apply full_filter_las per file with target downsample
            for fn in inp.iterdir():
                if not fn.name.lower().endswith((".las", ".laz")):
                    continue
                try:
                    las = core.load_las_points(str(fn))[2]
                except Exception as e:
                    print(f"Failed to read {fn}: {e}")
                    continue
                las = core.full_filter_las(las, args.downsample)
                out_file = out / fn.name
                las.write(str(out_file))
                print(f"{fn.name}: wrote {len(las.points)} points")
        else:
            results = core.process_directory(str(inp), str(out), M=args.M, K=args.K, sigma_multiplier=args.sigma)
            for name, kept in results.items():
                print(f"{name}: kept {kept} points")
    elif inp.is_file():
        if out.exists() and out.is_dir():
            out_file = out / inp.name
        else:
            out_file = out
        print(f"Processing file {inp} -> {out_file}")
        if args.downsample is not None:
            # read, apply full_filter_las and write
            try:
                las = core.load_las_points(str(inp))[2]
            except Exception as e:
                raise SystemExit(f"Failed to read input file: {e}")
            las = core.full_filter_las(las, args.downsample)
            las.write(str(out_file))
            print(f"Kept points: {len(las.points)}")
        else:
            kept = core.process_las_file(str(inp), str(out_file), M=args.M, K=args.K, sigma_multiplier=args.sigma)
            print(f"Kept points: {kept}")
    else:
        raise SystemExit("Input path does not exist")

if __name__ == "__main__":
    main()

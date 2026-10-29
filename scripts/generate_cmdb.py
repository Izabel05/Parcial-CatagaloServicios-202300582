"""Genera dispositivos en un lote reproducible sin borrar datos existentes."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.database.migrate import migrate
from backend.app.services.cmdb_generator import generate_devices


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=202300582)
    parser.add_argument('--count', type=int, default=5000)
    parser.add_argument('--responsable-id', type=int, required=True)
    args = parser.parse_args()
    migrate()
    print(json.dumps(generate_devices(args.seed, args.count, args.responsable_id), ensure_ascii=False))


if __name__ == '__main__':
    main()

"""Prepara datos de evaluación sin borrar ni restablecer los tickets existentes."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.app.services.demo_service import prepare_demo


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed',type=int,default=202300582)
    parser.add_argument('--rotate-passwords',action='store_true',help='Rotar únicamente las claves demo y revocar sus sesiones')
    args=parser.parse_args()
    report,credentials=prepare_demo(args.seed,args.rotate_passwords)
    print(json.dumps(report,ensure_ascii=False,default=str))
    for account in credentials:
        print(json.dumps(account,ensure_ascii=False),file=sys.stderr)
    return 0


if __name__=='__main__': sys.exit(main())

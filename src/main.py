## Utils ##
from utils import init

## Print ##
from rich import print as pprint
def print(*args, **kwargs):
    pprint(f"[bold green]Main -> {' '.join([str(_) for _ in args])} [/bold green]",**kwargs)



## Args ##
import argparse
parser = argparse.ArgumentParser(
                    prog = 'Mobile Cog Testing suite',
                    description = 'This program allows the developer to simulate running on a target mobile TCore version.',
                    epilog = 'For any inquiries contact artur@tcore.io')

parser.add_argument('--cog_path', required=False)
parser.add_argument('-v','--version', default="1") # 0 indicates latest
parser.add_argument('--pre', default="0")     # 0 indicates latest
parser.add_argument('--headless-init', action='store_true', default=False)     # 0 indicates latest
parser.add_argument('--interactive',
                       action='store_true',
                       help='launches interactive shell')

if __name__ == "__main__":
    args = parser.parse_args()
    # Create run-time
    system = init.Init(
        args.cog_path,
        args.version,
        args.pre,
        not args.interactive
    )

    if args.headless_init:
        print("Completed init!")
        quit(0)

    elif args.cog_path is None:
        print("No cog_path specified?")
        quit(0)

    if args.interactive:
        print("Starting runtime in interactive mode")
        system.run_env()
    
    else:
        system.run_session()
    
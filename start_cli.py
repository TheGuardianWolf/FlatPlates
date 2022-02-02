import os
from flatplates.interface import ScaleCLI


def main(window=None):
    cli = ScaleCLI()
    cli.setup(os.getcwd())
    cli.measurement()
    cli.cleanup()


if __name__ == "__main__":
    main()

"""CLI for the floras package."""
import typer
from floras.scripts.install_utils import download_and_install_spot
from pathlib import Path

app = typer.Typer()


@app.command(name="from-json")
def from_json(
    filename: str = typer.Option(
        ..., "--filename", "-f", help="Path to the JSON file"
            )
        ):
    """Run the test synthesis with the given JSON file."""
    if filename is None:
        print("Error: No filename provided. Use '--filename <file>' or \
            '-f <file>' to specify a json file.")
        return
    # Check if the file exists
    file_path = Path(filename)
    if not file_path.exists():
        print(f"Error: The file '{filename}' does not exist.")
        return

    try:
        from floras.main import find_test_environment
    except ImportError:
        print("Error: 'spot' is not installed. Run 'floras fetch_spot' \
            or install spot using conda first.")
        return

    print(f"Setting up the test environment for file: {filename}")
    d, flow = find_test_environment(filename)


@app.command(name="fetch-spot")
def fetch_spot():
    """Download and install spot."""
    download_and_install_spot()
    print("Spot has been successfully installed.")


@app.command()
def help():
    """Show help."""

    print("""Available floras functions:
    - from_json: Execute the process with a JSON file
      (e.g., `floras from_json -f file.json` or `floras from_json --filename file.json`)
    - fetch_spot: Download and install spot

    For the floras documentation and installation instructions please
        visit the website: https://floras.readthedocs.io.
    """)

from pathlib import Path
import zipfile

import click


class BadArchiveError(OSError):
    pass


def unzip_one(file: Path, dest: Path, member) -> Path:
    """Extract a specific file from a zip file.

    Args:
        member: The exact name of the archive member
    Returns: The normalized path created
    """
    with zipfile.ZipFile(file, 'r') as ezip:
        first_bad_file = ezip.testzip()
        if first_bad_file:
            raise BadArchiveError(
                f"The archive contains at least one bad file: {first_bad_file}")
        zipinf = None
        for _m in ezip.infolist():
            if _m.filename == member:
                zipinf = _m
        if zipinf is None:
            raise ValueError(f"Did not find archive member {member} in {file}")
        fpath = ezip.extract(member=zipinf, path=dest)
        return Path(fpath)


def unzip(file: Path, dest: Path):
    """Uncompress the whole zip archive and delete the zip.

    Args:
        file: The Path to the zip.
        dest: The Path to the destination directory.

    Returns:
        None
    """
    with zipfile.ZipFile(file, 'r') as ezip:
        first_bad_file = ezip.testzip()
        if first_bad_file:
            raise BadArchiveError(
                f"The archive contains at least one bad file: {first_bad_file}")
        ezip.extractall(path=dest)
    file.unlink()



@click.command()
@click.argument('filename', type=click.Path(exists=True))
@click.argument('outdir', type=click.Path(exists=True))
def unzip_csv(filename, outdir):
    tile_id = filename.split("_")[0]
    outdir_tile = Path(outdir) / tile_id
    outdir_tile.mkdir(exist_ok=True)
    unzip(Path(filename), Path(outdir_tile))


if __name__ == "__main__":
    unzip_csv()
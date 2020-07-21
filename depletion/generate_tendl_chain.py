#!/usr/bin/env python3

import os
from pathlib import Path
import tarfile
from zipfile import ZipFile

import openmc.deplete as dep
import openmc.data

from utils import download


NEUTRON_LIB = 'https://tendl.web.psi.ch/tendl_2019/tar_files/TENDL-n.tgz'
DECAY_LIB = 'https://www.oecd-nea.org/dbdata/jeff/jeff33/downloads/JEFF33-rdd.zip'
NFY_LIB = 'https://www.oecd-nea.org/dbdata/jeff/jeff33/downloads/JEFF33-nfy.asc'

# Modify list of transmutation reactions
dep.chain.TRANSMUTATION_REACTIONS = list(dep.chain._REACTIONS.keys())


def extract(filename, path=".", verbose=True):
    # Determine function to open archive
    if Path(filename).suffix == '.zip':
        func = ZipFile
    else:
        func = tarfile.open

    # Open archive and extract files
    with func(filename, 'r') as fh:
        if verbose:
            print(f'Extracting {filename}...')
        fh.extractall(path)


def fix_jeff33_nfy(path):
    new_path = path.with_name(path.name + '_fixed')
    if not new_path.exists():
        with path.open('r') as f:
            data = f.read()
        with new_path.open('w') as f:
            # Write missing TPID line
            f.write(" "*66 + "   1 0  0    0\n")
            f.write(data)
    return new_path


def main():
    endf_dir = Path("tendl-download")

    neutron_tgz = download(NEUTRON_LIB, output_path=endf_dir)
    decay_zip = download(DECAY_LIB, output_path=endf_dir)
    nfy_file = download(NFY_LIB, output_path=endf_dir)

    #extract(neutron_tgz, endf_dir / 'neutrons')
    extract(decay_zip, endf_dir / 'decay')
    nfy_file_fixed = fix_jeff33_nfy(nfy_file)

    neutron_files = list((endf_dir / "neutrons").glob("*.tendl"))
    decay_files = list((endf_dir / "decay").glob('*.ASC'))
    nfy_evals = openmc.data.endf.get_evaluations(nfy_file_fixed)

    chain = dep.Chain.from_endf(decay_files, nfy_evals, neutron_files)
    chain.export_to_xml('chain_tendl2019_jeff33.xml')


if __name__ == '__main__':
    main()

"""Main module."""

__author__ = """Diane Knappett"""
__contact__ = 'diane.knappett@stfc.ac.uk'
__copyright__ = "Copyright 2020 United Kingdom Research and Innovation"
__license__ = "BSD - see LICENSE file in top-level package directory"

import os, glob, re
import hashlib
from pathlib import Path

import logging

# Set up module-level logger
logging.basicConfig()
logger = logging.getLogger(__name__)


def nested_list(d: str, remove_base=False) -> list:
    r = []
    for i in os.listdir(d):

        pth = os.path.join(d, i)
        if os.path.isdir(pth):
            r.extend(nested_list(pth))
        else:
            if remove_base:
                pth = pth.replace(remove_base, "")
            r.append(pth)

    return sorted(r)


def dirs_match(d1: str, d2: str, basedir1: str, basedir2: str) -> bool:
    errs = 0
    l1 = nested_list(d1, remove_base=basedir1)
    l2 = nested_list(d2, remove_base=basedir2)

    if l1 != l2:
        print(f"[ERROR] dirs have different listed contents: {d1} vs {d2}")
        return

    for i in d1:
        i1 = os.path.join(d1, i)
        i2 = os.path.join(d2, i)

        if os.path.isfile(i1):
            s1, s2 = [size(item) for item in (i1, i2)]
            if s1 != s2:
                print(f"[ERROR] Files differ in size: {i1} = {s1} vs {i2} = {s2}")
                errs += 1
            else:
                m1, m2 = [md5(item) for item in (i1, i2)]
                if m1 != m2:
                    print(f"[ERROR] Files differ in MD5: {i1} vs {i2}")
                    errs += 1

    res = True if errs == 0 else False
    return res    


def md5(f: str, blocksize: int=65536) -> str:
    hash = hashlib.md5()

    with open(f, "rb") as f:
        for block in iter(lambda: f.read(blocksize), b""):
            hash.update(block)
    return hash.hexdigest()


def size(f: str) -> int:
    return os.path.getsize(f)


def identify_dirs(d: str, pattern: str=r"v\d{8}") -> list:
    r = []
    for dr, subdirs, files in os.walk(d):
        if any([re.match(pattern, sdir) for sdir in subdirs]):
            r.append(dr)

    return r


def find_versions(dr):
    return sorted([os.path.basename(v) for v in glob.glob(f"{dr}/v20??????")])


class VersionDir:
    def __init__(self, dr):
        self.dr = dr
        self.as_path = Path(dr)
        self.base, self.version = os.path.split(dr)

class ArchiveDir:
    def __init__(self, dr):
        self.dr = dr
        self.exists = os.path.isdir(dr)
        self.versions = find_versions(dr)
        self._latest_path = Path(f"{dr}/latest")
        self.latest = self._latest_path.readlink().as_posix() if self._latest_path.is_symlink() else False
        self._check_valid()

    def _check_valid(self):
        errs = 0
        if not os.path.isdir(self.dr):
            errs += 1
            print(f"[ERROR] Archive container directory is missing: {self.dr}")
        elif not self.versions:
            errs += 1
            print(f"[ERROR] No version directories found in container directory: {self.dr}")
        
        if not self.latest:
            errs += 1
            print(f"[ERROR] No latest link in container directory: {self.dr}")
        elif self._latest_path.readlink().as_posix() != self.versions[-1]:
            errs += 1
            print(f"[ERROR] latest link is not pointing to most recent version in: {self.dr}")

        self.valid = True if errs == 0 else False


def main(bd1: str, bd2: str) -> None:
    for d1 in identify_dirs(bd1):
        gws_dir = VersionDir(d1)
        gws_versions = find_versions(gws_dir.dr)
        arc_dir = ArchiveDir(d1.replace(bd1, bd2))

        if gws_dir.as_path.is_symlink() and gws_dir.as_path.readlink().as_posix() == arc_dir:
            logger.info(f"[INFO] Already linked: {gws_dir}")
            continue

        for gws_version in reversed(gws_versions):
            gv_path, av_path = [os.path.join(bdir, gws_version) for bdir in (gws_dir.dr, arc_dir.dr)]
            print(f"[INFO] Working on: {gv_path}")
            print(f"              and: {av_path}")

            if gws_version < arc_dir.latest:
                print(f"[ACTION] Delete old version in GWS: {gv_path}")
            elif gws_version == arc_dir.latest:
                if dirs_match(gv_path, av_path, bd1, bd2):
                    logger.warning(f"[ACTION] Delete {gv_path} and symlink to: {av_path}")
            else:
                print(f"[WARNING] GWS version is newer than archive dir: {gv_path} newer than {av_path}")
                print(f"          And latest link points to {Path(gws_dir + '/latest').readlink()}")




test_data = [
    [
        "/gws/pw/j07/ukcp18/pre-archive/ukcp18/data/land-prob/global/glb/rcp85/cdf/b8110/30y/tasAnom",
        "/badc/ukcp18/data/land-prob/global/glb/rcp85/cdf/b8110/30y/tasAnom",
        True
    ]
]

def test_main():
    td1, td2, outcome = test_data[0]
    res = main(td1, td2)


test_main()
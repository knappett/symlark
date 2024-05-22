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
logger.setLevel(logging.DEBUG)


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
        logger.error(f"Dirs have different listed contents: {d1} vs {d2}")
        return

    for i in l1:
        i1 = os.path.join(d1, i.lstrip("/"))
        i2 = os.path.join(d2, i.lstrip("/"))
        logger.debug(f"Comparing at file level: {i}")

        if os.path.isfile(i1):
            print(f"Comparing files: {i1} AND {i2}")
            s1, s2 = [size(item) for item in (i1, i2)]

            if s1 != s2:
                logger.error(f"Files differ in size: {i1} = {s1} vs {i2} = {s2}")
                errs += 1
            else:
                m1, m2 = [md5(item) for item in (i1, i2)]
                if m1 != m2:
                    logger.error(f"Files differ in MD5: {i1} vs {i2}")
                    errs += 1

    res = True if errs == 0 else False
    return res    


def delete_dir(dr):
    logger.warning(f"Deleting files in: {dr}")
    for fname in os.listdir(dr):
        os.remove(f"{dr}/{fname}")

    logger.warning(f"Deleting directory: {dr}")
    os.rmdir(dr)


def symlink(target, symlink, relative=False):
    logger.warning(f"Symlinking {symlink} to: {target}")

    if relative:
        cwd = os.getcwd()
        os.chdir(os.path.dirname(target))
        os.symlink(os.path.basename(target), symlink)
        os.chdir(cwd)
    else:
        os.symlink(target,symlink)


def md5(f: str, blocksize: int=65536) -> str:
    hash = hashlib.md5()
    logger.debug(f"Calculating MD5 for: {f}")

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
    return sorted([os.path.basename(v) for v in glob.glob(f"{dr}/v????????")])


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
        valid = True
        if not os.path.isdir(self.dr):
            valid = False
            logger.error(f"Archive container directory is missing: {self.dr}")
        elif not self.versions:
            valid = False
            logger.error(f"No version directories found in container directory: {self.dr}")
        
        if not self.latest:
            valid = False
            logger.error(f"No latest link in container directory: {self.dr}")
        elif self._latest_path.readlink().as_posix() != self.versions[-1]:
            valid = False
            logger.error(f"Latest link is not pointing to most recent version in: {self.dr}")

        self.valid = valid


def main(base_dir1: str, base_dir2: str) -> None:

    for dr in (base_dir1, base_dir2):
        if not os.path.isdir(dr):
            logger.error(f"Top-level directory does not exist: {dr}")
            return

    # Ensure paths are absolute, not relative, so that they can be used to create symlinks
    base_dir1 = os.path.abspath(base_dir1)
    base_dir2 = os.path.abspath(base_dir2)

    gws_dirs_to_check = identify_dirs(base_dir1)

    if not gws_dirs_to_check:
        logger.error(f"No content found in directory: {base_dir1}")

    for d1 in gws_dirs_to_check:
        gws_dir = VersionDir(d1)
        gws_versions = find_versions(gws_dir.dr)

        arc_dir = ArchiveDir(d1.replace(base_dir1, base_dir2))
        arc_versions = find_versions(arc_dir.dr)

        # If archive dir is invalid then needs fixing before other checks can be done
        if not arc_dir.valid:
            continue

        # Check that most recent archive version is not greater than most recent GWS version
        # If it is then create a symlink in the GWS and rerun identify_dirs list (or prefix it)
        most_recent_arc = (list(reversed(arc_versions))[0])
        most_recent_gws = (list(reversed(gws_versions))[0])
        if most_recent_arc > most_recent_gws:
            logger.warning("Most recent archive version directory newer than most recent GWS version directory.")
            # Create symlink from GWS to archive
            gv_path, av_path = [os.path.join(bdir, most_recent_arc) for bdir in (gws_dir.dr, arc_dir.dr)]
            symlink(av_path, gv_path)
            # Append the new GWS symlink version to the gws_versions list
            gws_versions.append(os.path.basename(gv_path))

        # Loop through all GWS versions and check them
        for gws_version in reversed(gws_versions):
            gv_path, av_path = [os.path.join(bdir, gws_version) for bdir in (gws_dir.dr, arc_dir.dr)]
            logger.debug(f"[INFO] Working on: {gv_path}")
            logger.debug(f"              and: {av_path}")

            # If the GWS version is older than the latest archive version: delete the GWS version
            if gws_version < arc_dir.latest:
                if os.path.islink(gv_path):
                    os.remove(gv_path)
                    logger.warning(f"[ACTION] Deleted symlink to older version: {gv_path}")
                else:
                    delete_dir(gv_path)
                    logger.warning(f"[ACTION] Deleted old version in GWS: {gv_path}")
            
            # If they are the same:
            elif gws_version == arc_dir.latest:

                # TODO: find a better solution than ".endswith(av_path)" - should match equivalence
                if Path(gv_path).is_symlink(): #and Path(gv_path).readlink().as_posix().endswith(av_path):
                    logger.info(f"{gv_path} correctly points to: {av_path}")
                elif dirs_match(gv_path, av_path, base_dir1, base_dir2):
                    logger.info(f"Found matching directories, so deleting and symlinking.")
                    delete_dir(gv_path)
                    symlink(av_path, gv_path)
                    logger.warning(f"[ACTION] Deleted {gv_path} and symlinked to: {av_path}")

                arc_latest_link=Path(arc_dir.dr + '/latest')
                logger.warning(f"    Archive latest link points to {arc_latest_link.readlink()}")

                gws_latest_link=Path(gws_dir.dr + '/latest')
                if os.path.exists(gws_latest_link):
                    logger.warning(f"    GWS latest link points to {gws_latest_link.readlink()}")
                    os.remove(gws_latest_link.as_posix())
                else:
                    logger.warning(f"    No latest link exists for {gv_path}")
                symlink(gv_path,'latest',relative=True)                

            # If the GWS version is newer: then maybe this is ready for ingestion, or needs attention
            else:
                logger.warning(f"GWS version is newer than archive dir: {gv_path} newer than {arc_dir.dr}/{arc_dir.latest}")
                latest_link=Path(gws_dir.dr + '/latest')
                if os.path.exists(latest_link):
                    logger.warning(f"    And latest link points to {latest_link.readlink()}")
                else:
                    logger.warning(f"    No latest link exists for {gv_path}")



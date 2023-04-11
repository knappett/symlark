from pathlib import Path
import os

import logging
from symlark.symlark import main


# NOTE: caplog is a special pytest "fixture" - that will capture log
# content from the python logger
def test_finding_our_feet(caplog):
    gws_dir, arc_dir = ("/gws/pw/j07/ukcp18/pre-archive/ukcp18/data/land-prob/global/glb/rcp85/cdf/b8110/30y/tasAnom",
            "/badc/ukcp18/data/land-prob/global/glb/rcp85/cdf/b8110/30y/tasAnom")

    caplog.set_level(logging.DEBUG)
    main(gws_dir, arc_dir)

    expected_log_msg = ("[ACTION] Delete "
                        "/gws/pw/j07/ukcp18/pre-archive/ukcp18/data/land-prob/global/glb/rcp85/cdf/b8110/30y/tasAnom/ann/v20190429 "
                        "and symlink to: "
                        "/badc/ukcp18/data/land-prob/global/glb/rcp85/cdf/b8110/30y/tasAnom/ann/v20190429")
    assert len(caplog.records) == 1
    assert caplog.records[0].message == expected_log_msg

    # We would expect to check file system things as well
 #   assert Path("/gws/pw/j07/ukcp18/pre-archive/ukcp18/data/land-prob/global/glb/rcp85/cdf/b8110/30y/tasAnom/ann/v20190429").readlink().as_posix("/badc/ukcp18/data/land-prob/global/glb/rcp85/cdf/b8110/30y/tasAnom/ann/v20190429) == 


def check_dir(dr):
    if not os.path.isdir(dr):
        os.makedirs(dr)


def setup_container_dir(basedir, versions, latest, arc_links=None):
    check_dir(basedir)
    for version in versions:
        check_dir(f"{basedir}/{version}")

    if latest:
        pass # Would create symlink here 

    if arc_links:
        pass # Link to archive equivalent


def test_single_version_duplicate_changed_to_symlink(caplog):
    setup_container_dir("test_gws", ["v20220202"], latest="v20220202")
    setup_container_dir("test_arc", ["v20220202"], latest="v20220202")

#    main(f"test_gws", "test_arc")
    # Now check the logs are correct
    # And check the file system is correct



def test_single_version_already_correctly_symlinked(caplog):
    setup_container_dir("test_arc", ["v20220203"], latest="v20220203")
    setup_container_dir("test_gws", [], latest="v20220203", arc_links={
        "v20220203": "test_arc/v20220203"
    })


    main(f"test_gws", "test_arc")
    # Assert log says: f"[INFO] Already linked: {gws_dir}"

    # Now check the logs are correct
    # And check the file system is correct
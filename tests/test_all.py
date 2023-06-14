from pathlib import Path
import os
import shutil

import logging
from symlark.symlark import main

TOP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEST_DATA = "tests/TEST_DATA"
TEST_GWS = f"{TEST_DATA}/test_gws"
TEST_ARC = f"{TEST_DATA}/test_arc"
TEST_GWS_TO_ARC = f"../../../{TEST_ARC}"


def _delete_test_data():
    if os.path.isdir(TEST_DATA):
        shutil.rmtree(TEST_DATA)

def setup_function():
    # Will be run before each test is run
    _delete_test_data()

def teardown_function():
    # Will be run after each test is run
    _delete_test_data()


def check_dir(dr):
    if not os.path.isdir(dr):
        os.makedirs(dr)


def create_files(dr, n=3, fnames=None):
    fnames = fnames or [f"file_{i+1}.nc" for i in range(n)]
    [open(f"{dr}/{fname}", "w") for fname in fnames]


def setup_container_dir(basedir, versions, latest=None, arc_links=None):
    check_dir(basedir)

    for version in versions:
        dr = f"{basedir}/{version}"
        check_dir(dr)
        create_files(dr)

    if latest:
        os.chdir(basedir)
        os.symlink(latest, "latest")
    
    if arc_links:
        for arc_link, av_dir in arc_links.items():
            target = f"{TEST_GWS_TO_ARC}/{av_dir}"
            print(target)
            print(arc_link)
            os.symlink(target, arc_link) 

    os.chdir(TOP_DIR)


def test_single_version_already_correctly_symlinked(caplog):
    setup_container_dir(TEST_ARC, ["v20220203"], latest="v20220203")
    setup_container_dir(TEST_GWS, [], latest="v20220203", arc_links={
        "v20220203": "v20220203"
    })

    caplog.set_level(logging.INFO)
    main(TEST_GWS, TEST_ARC)
    assert caplog.records[0].message == f"{TEST_GWS}/v20220203 correctly points to: {TEST_ARC}/v20220203"


def test_top_level_dir_does_not_exist(caplog):
    setup_container_dir(TEST_GWS, [])

    caplog.set_level(logging.INFO)
    NO_DIR = "no-arc-dir"
    main(TEST_GWS, NO_DIR)

    assert caplog.records[0].message == f"Top-level directory does not exist: {NO_DIR}"


def test_no_content_in_gws_dir(caplog):
    setup_container_dir(TEST_GWS, [])
    setup_container_dir(TEST_ARC, [])

    caplog.set_level(logging.INFO)
    main(TEST_GWS, TEST_ARC)

    assert caplog.records[0].message == f"No content found in directory: {TEST_GWS}"


def test_single_version_needs_deleting_and_symlink(caplog):
    setup_container_dir(TEST_ARC, ["v20220203"], latest="v20220203")
    setup_container_dir(TEST_GWS, ["v20220203"], latest="v20220203", arc_links=None)

    caplog.set_level(logging.INFO)
    main(TEST_GWS, TEST_ARC)

    gv_dir = f"{TEST_GWS}/v20220203"
    av_dir = f"{TEST_ARC}/v20220203"

    assert caplog.records[0].message == f"Deleting files in: {gv_dir}"
    assert caplog.records[1].message == f"Deleting directory: {gv_dir}"
    assert caplog.records[2].message == f"Symlinking {gv_dir} to: {av_dir}"
    assert caplog.records[3].message == f"[ACTION] Deleted {gv_dir} and symlinked to: {av_dir}"


def test_old_gws_version_needs_deleting_and_symlink(caplog):
    setup_container_dir(TEST_ARC, ["v20110101", "v20220203"], latest="v20220203")
    setup_container_dir(TEST_GWS, ["v20110101"], latest="v20220203", arc_links={
        "v20220203": "v20220203"
    })

    caplog.set_level(logging.INFO)
    main(TEST_GWS, TEST_ARC)

    gv_dir2 = f"{TEST_GWS}/v20220203"
    av_dir2 = f"{TEST_ARC}/v20220203"

    gv_dir = f"{TEST_GWS}/v20110101"
    av_dir = f"{TEST_ARC}/v20110101"

    assert caplog.records[0].message == f"{gv_dir2} correctly points to: {av_dir2}"
    assert caplog.records[1].message == f"Deleting files in: {gv_dir}"
    assert caplog.records[2].message == f"Deleting directory: {gv_dir}"
    assert caplog.records[3].message == f"Symlinking {gv_dir} to: {av_dir}"
    assert caplog.records[4].message == f"[ACTION] Deleted old version in GWS: {gv_dir}"
    
def test_newer_gws_than_archive(caplog):
    # Create an archive directory with one version v20220203
    setup_container_dir(TEST_ARC, ["v20220203"])
    
    # Create a GWS that points to archive version above
    setup_container_dir(TEST_GWS, [], arc_links={"v20220203": "v20220203"})
    
    # Create a GWS called v24440404 that holds data
    setup_container_dir(TEST_GWS, ["v24440404"])
    
    caplog.set_level(logging.INFO)

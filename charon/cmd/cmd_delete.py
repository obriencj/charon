"""
Copyright (C) 2022 Red Hat, Inc. (https://github.com/Commonjava/charon)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

         http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from typing import List

from charon.config import get_config
from charon.utils.archive import detect_npm_archive, NpmArchiveType
from charon.pkgs.maven import handle_maven_del
from charon.pkgs.npm import handle_npm_del
from charon.cmd.internal import (
    _decide_mode, _validate_prod_key,
    _get_local_repo, _get_buckets,
    _get_ignore_patterns, _safe_delete
)
from click import command, option, argument

import traceback
import logging
import os
import sys

logger = logging.getLogger(__name__)


@argument(
    "repo",
    type=str,
)
@option(
    "--product",
    "-p",
    help="""
        The product key, will combine with version to decide
        the metadata of the files in tarball.
    """,
    nargs=1,
    required=True,
    multiple=False,
)
@option(
    "--version",
    "-v",
    help="""
        The product version, will combine with product to decide
        the metadata of the files in tarball.
    """,
    required=True,
    multiple=False,
)
@option(
    "--target",
    "-t",
    'targets',
    help="""
    The target to do the deletion, which will decide which s3 bucket
    and what root path where all files will be deleted from.
    Can accept more than one target.
    """,
    required=True,
    multiple=True,
)
@option(
    "--root_path",
    "-r",
    default="maven-repository",
    help="""The root path in the tarball before the real maven paths,
            will be trailing off before uploading
    """,
)
@option(
    "--ignore_patterns",
    "-i",
    multiple=True,
    help="""
    The regex patterns list to filter out the files which should
    not be allowed to upload to S3. Can accept more than one pattern.
    """,
)
@option(
    "--work_dir",
    "-w",
    help="""
    The temporary working directory into which archives should
    be extracted, when needed.
    """,
)
@option(
    "--debug",
    "-D",
    help="Debug mode, will print all debug logs for problem tracking.",
    is_flag=True,
    default=False
)
@option(
    "--quiet",
    "-q",
    help="Quiet mode, will shrink most of the logs except warning and errors.",
    is_flag=True,
    default=False
)
@option("--dryrun", "-n", is_flag=True, default=False)
@command()
def delete(
    repo: str,
    product: str,
    version: str,
    targets: List[str],
    root_path="maven-repository",
    ignore_patterns: List[str] = None,
    work_dir: str = None,
    debug=False,
    quiet=False,
    dryrun=False
):
    """Roll back all files in a released product REPO from
    Ronda Service. The REPO points to a product released
    tarball which is hosted in a remote url or a local path.
    """
    tmp_dir = work_dir
    try:
        _decide_mode(product, version, is_quiet=quiet, is_debug=debug)
        if dryrun:
            logger.info("Running in dry-run mode,"
                        "no files will be deleted.")
        if not _validate_prod_key(product, version):
            return
        conf = get_config()
        if not conf:
            sys.exit(1)

        aws_profile = os.getenv("AWS_PROFILE") or conf.get_aws_profile()
        if not aws_profile:
            logger.error("No AWS profile specified!")
            sys.exit(1)

        archive_path = _get_local_repo(repo)
        npm_archive_type = detect_npm_archive(archive_path)
        product_key = f"{product}-{version}"
        manifest_bucket_name = conf.get_manifest_bucket()
        buckets = _get_buckets(targets, conf)
        if npm_archive_type != NpmArchiveType.NOT_NPM:
            logger.info("This is a npm archive")
            tmp_dir, succeeded = handle_npm_del(
                archive_path,
                product_key,
                buckets=buckets,
                aws_profile=aws_profile,
                dir_=work_dir,
                cf_enable=conf.is_aws_cf_enable(),
                dry_run=dryrun,
                manifest_bucket_name=manifest_bucket_name
            )
            if not succeeded:
                sys.exit(1)
        else:
            ignore_patterns_list = None
            if ignore_patterns:
                ignore_patterns_list = ignore_patterns
            else:
                ignore_patterns_list = _get_ignore_patterns(conf)
            logger.info("This is a maven archive")
            tmp_dir, succeeded = handle_maven_del(
                archive_path,
                product_key,
                ignore_patterns_list,
                root=root_path,
                buckets=buckets,
                aws_profile=aws_profile,
                dir_=work_dir,
                cf_enable=conf.is_aws_cf_enable(),
                dry_run=dryrun,
                manifest_bucket_name=manifest_bucket_name
            )
            if not succeeded:
                sys.exit(1)
    except Exception:
        print(traceback.format_exc())
        sys.exit(2)  # distinguish between exception and bad config or bad state
    finally:
        if not debug:
            _safe_delete(tmp_dir)
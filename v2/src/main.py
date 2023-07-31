import dataclasses
import pathlib

import runner
import scheduler
import xmltodict  # type: ignore

# mypy: allow_any_expr
# pylint: disable=protected-access


@dataclasses.dataclass(frozen=True)
class _Test:
    schedule: tuple[runner.Variant, ...]
    failure_count: int
    success_count: int
    errors: None = None


DIR = pathlib.Path("/home/solo/git/robotmk/v2/data/retry_suite/")

FAILURE = runner.Variant(variablefile=None, argumentfile=None)
SUCCESS = runner.Variant(variablefile=DIR / "retry_variables.yaml", argumentfile=None)

TESTS = (
    _Test(
        schedule=(SUCCESS,),
        failure_count=0,
        success_count=2,
    ),
    _Test(
        schedule=(FAILURE,),
        failure_count=1,
        success_count=1,
    ),
    _Test(
        schedule=(SUCCESS, SUCCESS),
        failure_count=0,
        success_count=2,
    ),
    _Test(
        schedule=(SUCCESS, FAILURE),
        failure_count=0,
        success_count=2,
    ),
    _Test(
        schedule=(FAILURE, SUCCESS),
        failure_count=1,
        success_count=2,
    ),
    _Test(
        schedule=(FAILURE, FAILURE),
        failure_count=2,
        success_count=1,
    ),
)


def _read_result(merged: pathlib.Path, test: _Test) -> None:
    with merged.open(encoding="utf-8") as file:
        content = file.read()
    parsed_content = xmltodict.parse(content)
    summary = parsed_content["robot"]["statistics"]["total"]["stat"]
    assert int(summary["@pass"]) == test.success_count
    assert int(summary["@fail"]) == test.failure_count
    assert parsed_content["robot"]["errors"] == test.errors


def version_one() -> None:
    for test in TESTS:
        config = scheduler._SuiteConfig(
            execution_interval_seconds=10,
            python_executable=pathlib.Path("python"),
            robot_target=DIR / "suite.robot",
            working_directory=pathlib.Path("/tmp/outputdir/"),
            variants=test.schedule,
            retry_strategy=runner.RetryStrategy.INCREMENTAL,
            env=None,
        )
        retry_runner = scheduler._SuiteRetryRunner(config)
        retry_runner()
        print(retry_runner._final_outputs)
        _read_result(retry_runner._final_outputs[-1], test)


version_one()

DIR = pathlib.Path("/home/solo/git/robotmk/v2/data/retry_rcc/")

FAILURE = runner.Variant(variablefile=None, argumentfile=None)
SUCCESS = runner.Variant(variablefile=DIR / "retry_variables.yaml", argumentfile=None)

TESTS = (
    _Test(
        schedule=(SUCCESS,),
        failure_count=0,
        success_count=2,
    ),
    _Test(
        schedule=(FAILURE,),
        failure_count=1,
        success_count=1,
    ),
    _Test(
        schedule=(SUCCESS, SUCCESS),
        failure_count=0,
        success_count=2,
    ),
    _Test(
        schedule=(SUCCESS, FAILURE),
        failure_count=0,
        success_count=2,
    ),
    _Test(
        schedule=(FAILURE, SUCCESS),
        failure_count=1,
        success_count=2,
    ),
    _Test(
        schedule=(FAILURE, FAILURE),
        failure_count=2,
        success_count=1,
    ),
)


def version_two() -> None:
    for test in TESTS:
        config = scheduler._SuiteConfig(
            execution_interval_seconds=10,
            python_executable=pathlib.Path("python"),
            robot_target=DIR / "suite.robot",
            working_directory=pathlib.Path("/tmp/outputdir/"),
            variants=test.schedule,
            retry_strategy=runner.RetryStrategy.INCREMENTAL,
            env=scheduler._RCC(robot_yaml=DIR / "robot.yaml"),
        )
        retry_runner = scheduler._SuiteRetryRunner(config)
        retry_runner()
        print(retry_runner._final_outputs)
        _read_result(retry_runner._final_outputs[-1], test)


version_two()

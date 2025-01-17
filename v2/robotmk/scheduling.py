"""Scheduler"""

import datetime
import pathlib
import subprocess
from collections.abc import Iterable
from typing import Final

from apscheduler.schedulers.base import BaseScheduler  # type: ignore[import]
from apscheduler.triggers.interval import IntervalTrigger  # type: ignore[import]
from robot import rebot  # type: ignore[import]

from robotmk.api import Result, create_result
from robotmk.attempt import Attempt, Identifier, RetrySpec, create_attempts
from robotmk.config import (
    ConfigRCC,
    ConfigSystemPython,
    RCCEnvironmentSpec,
    SuiteSpecification,
    UserSessionConfig,
)
from robotmk.environment import RCCEnvironment, ResultCode, SystemEnvironment
from robotmk.session import CurrentSession, UserSession


def schedule_suites(
    config: ConfigSystemPython | ConfigRCC,
    scheduler: BaseScheduler,
) -> BaseScheduler:
    for suite_specification in config.suite_specifications():
        scheduler.add_job(
            _SuiteRetryRunner(suite_specification),
            name=suite_specification.name,
            trigger=IntervalTrigger(
                seconds=suite_specification.config.execution_interval_seconds
            ),
            next_run_time=datetime.datetime.now(),
        )
    return scheduler


def _environment(
    suite_name: str,
    config: RCCEnvironmentSpec | None,
) -> RCCEnvironment | SystemEnvironment:
    if config is None:
        return SystemEnvironment()
    return RCCEnvironment(
        robot_yaml=config.robot_yaml_path,
        binary=config.binary_path,
        controller="robotmk",
        space=suite_name,
    )


def _session(
    suite_name: str,
    environment: RCCEnvironmentSpec | None,
    session: UserSessionConfig | None,
) -> CurrentSession | UserSession:
    env = _environment(suite_name, environment)
    if session:
        return UserSession(
            user_name=session.user_name,
            environment=env,
        )
    return CurrentSession(environment=env)


class _SuiteRetryRunner:  # pylint: disable=too-few-public-methods
    def __init__(self, suite_specification: SuiteSpecification) -> None:
        self._suite_spec: Final = suite_specification
        self._session: Final = _session(
            suite_specification.name,
            suite_specification.rcc_env,
            suite_specification.config.session,
        )

    def __call__(self) -> None:
        retry_spec = RetrySpec(
            identifier=Identifier(
                name=self._suite_spec.name,
                timestamp=datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
                # be compatible with Windows and Linux folder name restrictions
                .replace(":", "."),
            ),
            robot_target=self._suite_spec.config.robot_target,
            working_directory=self._suite_spec.working_directory,
            variants=self._suite_spec.config.variants,
            strategy=self._suite_spec.config.retry_strategy,
        )
        self._prepare_run(retry_spec.output_directory())

        outputs = self._run_attempts_until_successful(create_attempts(retry_spec))

        if not outputs:
            return  # Untested

        final_output = retry_spec.output_directory() / "merged.xml"
        final_log = retry_spec.output_directory() / "merged.html"
        rebot(*outputs, output=final_output, report=None, log=final_log)

        xml = final_output.read_text(encoding="utf-8")
        html = final_log.read_text(encoding="utf-8")
        result = create_result(retry_spec.identifier.name, xml, html)
        self._write_result_file_atomic(
            result=result,
            suite_working_directory=retry_spec.output_directory(),
        )

    def _prepare_run(self, output_dir: pathlib.Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        if (build_command := self._session.environment.build_command()) is not None:
            _process = subprocess.run(build_command, check=True)

    def _run_attempts_until_successful(
        self,
        attempts: Iterable[Attempt],
    ) -> list[pathlib.Path]:
        outputs = []
        for attempt in attempts:
            match self._session.run(attempt):
                case ResultCode.ALL_TESTS_PASSED:
                    outputs.append(attempt.output_xml_file())
                case ResultCode.ROBOT_COMMAND_FAILED if attempt.output_xml_file().exists():
                    outputs.append(attempt.output_xml_file())
                    continue
            break
        return outputs

    def _write_result_file_atomic(
        self,
        *,
        result: Result,
        suite_working_directory: pathlib.Path,
    ) -> None:
        intermediate_result_path = suite_working_directory / "result.json"
        intermediate_result_path.write_text(
            result.model_dump_json(),
            encoding="utf-8",
        )
        intermediate_result_path.replace(
            suite_result_file(
                suite_results_directory(self._suite_spec.results_directory),
                self._suite_spec.name,
            )
        )


def suite_results_directory(results_directory: pathlib.Path) -> pathlib.Path:
    return results_directory / "suites"


def suite_result_file(
    suite_results_dir: pathlib.Path,
    suite_name: str,
) -> pathlib.Path:
    return suite_results_dir / f"{suite_name}.json"

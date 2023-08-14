import dataclasses
import enum
import pathlib
import subprocess
from collections.abc import Sequence


class ResultCode(enum.Enum):
    ALL_TESTS_PASSED = "all_tests_passed"
    ROBOT_COMMAND_FAILED = "robot_command_failed"
    RCC_ERROR = "rcc_error"


@dataclasses.dataclass(frozen=True)
class RCCEnvironment:
    robot_yaml: pathlib.Path
    binary: str

    def build_command(self) -> list[str]:
        return [
            self.binary,
            "holotree",
            "variables",
            "--json",
            "-r",
            str(self.robot_yaml),
        ]

    def wrap_for_execution(self, command: Sequence[str]) -> list[str]:
        rcc_command = [
            self.binary,
            "task",
            "script",
            "-r",
            str(self.robot_yaml),
            "--",
        ]
        return [
            *rcc_command,
            *command,
        ]

    @staticmethod
    def create_result_code(process: subprocess.CompletedProcess[str]) -> ResultCode:
        if process.returncode == 0:
            return ResultCode.ALL_TESTS_PASSED
        if process.returncode == 10:
            return ResultCode.ROBOT_COMMAND_FAILED
        return ResultCode.RCC_ERROR


@dataclasses.dataclass(frozen=True)
class RobotEnvironment:
    def build_command(self) -> None:
        return None

    def wrap_for_execution(self, command: Sequence[str]) -> Sequence[str]:
        return command

    @staticmethod
    def create_result_code(process: subprocess.CompletedProcess[str]) -> ResultCode:
        if process.returncode == 0:
            return ResultCode.ALL_TESTS_PASSED
        return ResultCode.ROBOT_COMMAND_FAILED

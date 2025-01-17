from base64 import b64encode
from datetime import datetime

from pydantic import Base64Bytes, BaseModel

from robotmk import parse_xml


class Test(BaseModel, frozen=True):
    name: str
    id_: str
    status: parse_xml.Outcome
    starttime: datetime
    endtime: datetime


class Result(BaseModel, frozen=True):
    suite_name: str
    tests: list[Test]
    xml: str
    html: Base64Bytes


# TODO: This function depends on `parse_xml` and therefore   # pylint: disable=fixme
# cannot be part of the API! We have to find a different location.
def create_result(suite_name: str, xml: str, html: str) -> Result:
    rebot = parse_xml.parse_rebot(xml)
    tests = [
        Test(
            name=t.name,
            id_=t.id_,
            status=t.status.status,
            starttime=t.status.starttime,
            endtime=t.status.endtime,
        )
        for t in _obtain_tests(rebot)
    ]
    return Result(
        suite_name=suite_name,
        tests=tests,
        xml=xml,
        html=b64encode(bytes(html, "utf-8")),
    )


def _obtain_tests(output: parse_xml.Rebot) -> list[parse_xml.Test]:
    result = []
    suites = output.robot.suite.copy()
    while suites:
        current_suite = suites.pop()
        suites.extend(current_suite.suite)
        result.extend(current_suite.test)
    return result

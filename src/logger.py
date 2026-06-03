import datetime
from enum import Enum
from pydantic import BaseModel, Field

from src.config import SAGE_SERVER, SAGE_ENV, SAGE_GROUP, POD_NAME, SAGE_SYSTEM


class LogLevel(str, Enum):
    FATAL = "FATAL"
    ERROR = "ERROR"
    WARN = "WARN"
    INFO = "INFO"
    DEBUG = "DEBUG"
    TRACE = "TRACE"


class LogData(BaseModel):
    timestamp: str = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%S.%fZ"
        ),
        alias="@timestamp",
    )
    dc: str = SAGE_SERVER
    env: str = SAGE_ENV
    group: str = SAGE_GROUP
    system: str = SAGE_SYSTEM
    inst: str = POD_NAME
    level: LogLevel = LogLevel.INFO
    msg: str

    class Config:
        populate_by_name = (
            True
        )


def stdout_log(msg: str, level: LogLevel = LogLevel.ERROR):
    log_entry = LogData(msg=msg, level=level)
    log_json = log_entry.model_dump_json(by_alias=True)
    print(log_json)

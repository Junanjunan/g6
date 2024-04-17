"""환경설정 관련 API Router"""
from enum import Enum
from typing_extensions import Annotated, Union, Dict
from fastapi import APIRouter, Request, Path
from fastapi.encoders import jsonable_encoder

from api.v1.models.config import (
    HtmlBaseResponse, MemoResponse, PolicyResponse, RegisterResponse
)
from api.v1.models.response import response_500

router = APIRouter(
    prefix="/config",
    responses={**response_500}
)


class ResponseEnum(Enum):
    HTML = {
        "class": HtmlBaseResponse,
        "description": "HTML을 구성하는데 필요한 설정 정보를 조회합니다."
    }
    POLICY = {
        "class": PolicyResponse,
        "description": "회원가입 약관을 조회합니다."
    }
    MEMBER = {
        "class": RegisterResponse,
        "description": "회원가입에 필요한 기본환경설정 정보를 조회합니다.<br>(회원가입 약관, 개인정보 수집 및 허용 약관)"
    }
    MEMO = {
        "class": MemoResponse,
        "description": "쪽지 발송 시, 1건당 소모되는 포인트 설정 정보를 조회합니다."
    }

    @classmethod
    def get_type_description(cls, dict_info: dict):
        type_description = ""
        for key, value in dict_info.items():
            type_description += f"- {key}: {value.annotation.__name__}\n"
        return type_description

    @classmethod
    def config_description(cls):
        description = """### response_type:환경설정 종류 ###\n\n"""
        for i in cls:
            description += f"**{i.name.lower()}**: {i.value['description']}\n\n {cls.get_type_description(i.value['class'].model_fields)}\n\n"
        return description


@router.get("/{response_type}",
            description=ResponseEnum.config_description(),
            summary="환경설정 조회")
async def read_config(
    request: Request,
    response_type: Annotated[str, Path(title="환경설정 종류", description="환경설정 종류")]
) -> Dict[str, Union[str, int]]:
    """
    환경설정 종류에 따라 설정 정보를 조회합니다.
    API 문서에 적용되는 상세설명은 @router.get 데코레이터의 description에 정의되어 있습니다.
    """
    validate_model: ResponseEnum = getattr(ResponseEnum, response_type.upper(), None)
    if not validate_model:
        return {"message": "환경설정 종류가 잘못되었습니다."}
    response_class = validate_model.value
    config = response_class["class"].model_construct(**request.state.config.__dict__)
    config_json = jsonable_encoder(config)
    return config_json
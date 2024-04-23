"""인기 검색어 API Router"""
from datetime import date
from typing import List
from typing_extensions import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.exc import SQLAlchemyError

from api.v1.lib.popular import PopularServiceAPI
from api.v1.models.popular import (
    CreatePopularRequest, PopularRequest, PopularResponse
)
from api.v1.models.response import MessageResponse, response_409, response_422, response_500
from lib.popular import get_populars


router = APIRouter()


@router.get("/populars",
            summary="인기 검색어 목록 조회",
            responses={**response_422, **response_500})
async def read_populars(
    data: Annotated[PopularRequest, Depends()]
) -> List[PopularResponse]:
    """
    인기 검색어 목록을 조회합니다.
    - TTLCache(Time-To-Live) 캐시를 사용하여 조회합니다.
    """
    try:
        return get_populars(data.limit, data.day)
    except SQLAlchemyError as e:
        return HTTPException(status_code=500, detail=str(e))


@router.post("/populars",
             summary="인기 검색어 등록",
             responses={**response_409, **response_422, **response_500})
async def create_popular(
    request: Request,
    service: Annotated[PopularServiceAPI, Depends()],
    data: CreatePopularRequest
) -> MessageResponse:
    """
    인기 검색어를 등록합니다.
    """
    service.create_popular(request, data.fields, data.word)

    return {
        "message": "인기 검색어가 등록되었습니다."
    }


@router.delete("/populars",
                summary="인기 검색어 삭제",
                responses={**response_422, **response_500})
async def delete_popular(
    service: Annotated[PopularServiceAPI, Depends()],
    base_date: date = Query(default=date.today(),
                            title="삭제 날짜",
                            description="삭제 기준 일")
) -> MessageResponse:
    """
    입력일 기준 이전 날짜로 등록된 인기 검색어를 삭제합니다.
    """
    rowconut = service.delete_populars(base_date)
    return {
        "message": f"인기 검색어가 {rowconut}건 삭제되었습니다."
    }
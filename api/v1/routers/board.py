from typing_extensions import Annotated, Dict, List

from fastapi import APIRouter, Depends, Request, Path, HTTPException, status, UploadFile, File, Form
from fastapi.responses import RedirectResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy import update

from core.database import db_session
from core.models import Board, Group, WriteBaseModel, Member
from lib.board_lib import insert_board_new, set_write_delay
from lib.common import dynamic_create_write_table
from lib.dependencies import common_search_query_params
from api.v1.models import responses
from api.v1.dependencies.board import (
    get_current_member, get_member_info, get_board, get_group,
    validate_write, validate_delete_comment,
    validate_upload_file_write, get_write
)
from api.v1.models.board import WriteModel, CommentModel, ResponseWriteModel, ResponseBoardModel
from response_handlers.board import(
    ListPostServiceAPI, CreatePostServiceAPI, ReadPostServiceAPI,
    UpdatePostServiceAPI, DeletePostServiceAPI, GroupBoardListServiceAPI,
    CreateCommentServiceAPI
)


router = APIRouter()

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

@router.get("/group/{gr_id}",
            summary="게시판그룹 목록 조회",
            response_description="게시판그룹 목록을 반환합니다.",
            responses={**responses}
            )
async def api_group_board_list(
    request: Request,
    db: db_session,
    member: Annotated[Member, Depends(get_current_member)],
    group: Annotated[Group, Depends(get_group)],
    gr_id: str = Path(...),
) -> Dict:
    """
    게시판그룹의 모든 게시판 목록을 보여줍니다.
    """
    group_board_list_service = GroupBoardListServiceAPI(
        request, db, gr_id, member
    )
    group = group_board_list_service.group
    group_board_list_service.check_mobile_only()
    boards = group_board_list_service.get_boards_in_group()

    # 데이터 유효성 검증 및 불필요한 데이터 제거한 게시판 목록 얻기
    filtered_boards = []
    for board in boards:
        board_json = jsonable_encoder(board)
        board_api = ResponseBoardModel.model_validate(board_json)
        filtered_boards.append(board_api)

    return jsonable_encoder({"group": group, "boards": filtered_boards})


@router.get("/{bo_table}",
            summary="게시판 조회",
            response_description="게시판 정보, 글 목록을 반환합니다.",
            responses={**responses}
            )
async def api_list_post(
    request: Request,
    db: db_session,
    member_info: Annotated[Dict, Depends(get_member_info)],
    board: Annotated[Board, Depends(get_board)],
    search_params: Annotated[dict, Depends(common_search_query_params)],
    bo_table: str = Path(...),
) -> Dict:
    """
    지정된 게시판의 글 목록을 보여줍니다.
    """
    list_post_service = ListPostServiceAPI(
        request, db, bo_table, board, member_info["member"], search_params
    )

    board_json = jsonable_encoder(board)
    board = ResponseBoardModel.model_validate(board_json)

    content = {
        "categories": list_post_service.categories,
        "board": board,
        "writes": list_post_service.get_writes(search_params),
        "total_count": list_post_service.get_total_count(),
        "current_page": search_params['current_page'],
        "prev_spt": list_post_service.prev_spt,
        "next_spt": list_post_service.next_spt,
    }
    
    return jsonable_encoder(content)


@router.get("/{bo_table}/{wr_id}",
            summary="게시판 개별 글 조회",
            response_description="게시판 개별 글을 반환합니다.",
            response_model=ResponseWriteModel,
            responses={**responses}
            )
async def api_read_post(
    request: Request,
    db: db_session,
    write: Annotated[WriteBaseModel, Depends(get_write)],
    board: Annotated[Board, Depends(get_board)],
    member: Annotated[Member, Depends(get_current_member)],
    bo_table: str = Path(...),
    wr_id: str = Path(...),
) -> Dict:
    """
    지정된 게시판의 글을 개별 조회합니다.
    """
    read_post_service = ReadPostServiceAPI(
        request, db, bo_table, board, wr_id, write, member
    )
    content = jsonable_encoder(read_post_service.write)
    additional_content = jsonable_encoder({
        "images": read_post_service.images,
        "normal_files": read_post_service.normal_files,
        "links": read_post_service.get_links(),
        "comments": read_post_service.get_comments(),
    })
    content.update(additional_content)
    read_post_service.validate_secret()
    read_post_service.validate_repeat()
    read_post_service.block_read_comment()
    read_post_service.validate_read_level()
    read_post_service.check_scrap()
    read_post_service.check_is_good()
    model_validated_content = ResponseWriteModel.model_validate(content)
    db.commit()
    return model_validated_content


@router.post("/{bo_table}",
             summary="게시판 글 작성",
             response_description="글 작성 성공 여부를 반환합니다.",
             responses={**responses}
             )
async def api_create_post(
    request: Request,
    db: db_session,
    member_info: Annotated[Dict, Depends(get_member_info)],
    wr_data: Annotated[WriteModel, Depends(validate_write)],
    board: Annotated[Board, Depends(get_board)],
    bo_table: str = Path(...),
) -> Dict:
    """
    지정된 게시판에 새 글을 작성합니다.
    """
    create_post_service = CreatePostServiceAPI(
        request, db, bo_table, board, member_info["member"]
    )
    create_post_service.validate_secret_board(wr_data.secret, wr_data.html, wr_data.mail)
    create_post_service.validate_post_content(wr_data.wr_subject)
    create_post_service.validate_post_content(wr_data.wr_content)
    create_post_service.is_write_level()
    create_post_service.arrange_data(wr_data, wr_data.secret, wr_data.html, wr_data.mail)
    write = create_post_service.save_write(wr_data.parent_id, wr_data)
    insert_board_new(bo_table, write)
    create_post_service.add_point(write)
    create_post_service.send_write_mail_(write, wr_data.parent_id)
    create_post_service.set_notice(write.wr_id, wr_data.notice)
    set_write_delay(create_post_service.request)
    create_post_service.save_secret_session(write.wr_id, wr_data.secret)
    create_post_service.delete_cache()
    redirect_url = create_post_service.get_redirect_url(write)
    db.commit()
    return RedirectResponse(redirect_url, status_code=303)
    

@router.put("/{bo_table}/{wr_id}",
            summary="게시판 글 수정",
            response_description="글 수정 성공 여부를 반환합니다.",
            responses={**responses}
            )
async def api_update_post(
    request: Request,
    db: db_session,
    member_info: Annotated[Dict, Depends(get_member_info)],
    wr_data: Annotated[WriteModel, Depends(validate_write)],
    board: Annotated[Board, Depends(get_board)],
    bo_table: str = Path(...),
    wr_id: str = Path(...),
) -> Dict:
    """
    지정된 게시판의 글을 수정합니다.
    """
    update_post_service = UpdatePostServiceAPI(
        request, db, bo_table, board, member_info["member"], wr_id
    )
    update_post_service.validate_restrict_comment_count()
    write = get_write(update_post_service.db, update_post_service.bo_table, update_post_service.wr_id)
    
    update_post_service.validate_secret_board(wr_data.secret, wr_data.html, wr_data.mail)
    update_post_service.validate_post_content(wr_data.wr_subject)
    update_post_service.validate_post_content(wr_data.wr_content)
    update_post_service.arrange_data(wr_data, wr_data.secret, wr_data.html, wr_data.mail)
    update_post_service.save_secret_session(wr_id, wr_data.secret)
    update_post_service.save_write(write, wr_data)
    update_post_service.set_notice(write.wr_id, wr_data.notice)
    update_post_service.update_children_category(wr_data)
    update_post_service.delete_cache()
    db.commit()
    return {"result": "updated"}


@router.delete("/{bo_table}/{wr_id}",
                summary="게시판 글 삭제",
                response_description="글 삭제 성공 여부를 반환합니다.",
                responses={**responses}
               )
async def api_delete_post(
    request: Request,
    db: db_session,
    member_info: Annotated[Dict, Depends(get_member_info)],
    board: Annotated[Board, Depends(get_board)],
    write: Annotated[WriteBaseModel, Depends(get_write)],
    bo_table: str = Path(...),
    wr_id: str = Path(...),
) -> Dict:
    """
    지정된 게시판의 글을 삭제합니다.
    """
    delete_post_api = DeletePostServiceAPI(
        request, db, bo_table, board, wr_id, write, member_info["member"]
    )
    delete_post_api.delete_write()
    return {"result": "deleted"}


@router.post("/uploadfile/{bo_table}/{wr_id}",
            summary="파일 업로드",
            response_description="파일 업로드 성공 여부를 반환합니다.",
            responses={**responses}
            )
async def api_upload_file(
    request: Request,
    db: db_session,
    member_info: Annotated[Dict, Depends(get_member_info)],
    board: Annotated[Board, Depends(get_board)],
    write: Annotated[WriteBaseModel, Depends(validate_upload_file_write)],
    bo_table: str = Path(...),
    files: List[UploadFile] = File(..., alias="bf_file[]"),
    file_content: list = Form(None, alias="bf_content[]"),
    file_dels: list = Form(None, alias="bf_file_del[]"),
) -> Dict:
    """
    파일 업로드
    """
    create_post_service = CreatePostServiceAPI(
        request, db, bo_table, board, member_info["member"]
    )
    create_post_service.upload_files(write, files, file_content, file_dels)
    return {"result": "uploaded"}


@router.post("/{bo_table}/{wr_parent}/comment",
            summary="댓글 작성",
            response_description="댓글 작성 성공 여부를 반환합니다.",
            responses={**responses}
            )
async def api_create_comment(
    request: Request,
    db: db_session,
    member: Annotated[Member, Depends(get_current_member)],
    board: Annotated[Board, Depends(get_board)],
    comment_data: CommentModel,
    bo_table: str = Path(...),
    wr_parent: str = Path(...),
):
    """
    댓글 등록
    """
    create_comment_service = CreateCommentServiceAPI(
        request, db, bo_table, board, member
    )
    parent_write = create_comment_service.get_parent_post(wr_parent, is_reply=False)
    create_comment_service.validate_comment_level()
    create_comment_service.validate_point()
    create_comment_service.validate_post_content(comment_data.wr_content)
    comment = create_comment_service.save_comment(comment_data, parent_write)
    create_comment_service.add_point(comment)
    create_comment_service.send_write_mail_(comment, parent_write)
    insert_board_new(bo_table, comment)
    db.commit()
    return {"result": "created"}


@router.put("/{bo_table}/{wr_parent}/comment/{wr_id}",
            summary="댓글 수정",
            response_description="댓글 수정 성공 여부를 반환합니다.",
            responses={**responses}
            )
async def api_update_comment(
    request: Request,
    db: db_session,
    comment_data: CommentModel,
    board: Annotated[Board, Depends(get_board)],
    member: Annotated[Member, Depends(get_current_member)],
    bo_table: str = Path(...),
    wr_id: str = Path(...),
) -> Dict:
    """
    댓글 수정
    """
    create_comment_service = CreateCommentServiceAPI(
        request, db, bo_table, board, member
    )
    write_model = create_comment_service.write_model
    create_comment_service.get_parent_post(wr_id, is_reply=False)
    comment = db.get(write_model, comment_data.comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail=f"{wr_id} : 존재하지 않는 댓글입니다.")

    create_comment_service.validate_post_content(comment_data.wr_content)
    comment.wr_content = create_comment_service.get_cleaned_data(comment_data.wr_content)
    comment.wr_option = comment_data.wr_option or "html1"
    comment.wr_last = create_comment_service.g5_instance.get_wr_last_now(write_model.__tablename__)
    db.commit()

    return {"result": "updated"}


@router.delete("/{bo_table}/{wr_parent}/comment/{wr_id}",
                summary="댓글 삭제",
                response_description="댓글 삭제 성공 여부를 반환합니다.",
                responses={**responses}
               )
async def api_delete_comment(
    db: db_session,
    comment: Annotated[WriteBaseModel, Depends(validate_delete_comment)],
    bo_table: str = Path(...),
):
    """
    댓글 삭제
    """
    write_model = dynamic_create_write_table(bo_table)

    # 댓글 삭제
    db.delete(comment)

    # 게시글에 댓글 수 감소
    db.execute(
        update(write_model).values(wr_comment=write_model.wr_comment - 1)
        .where(write_model.wr_id == comment.wr_parent)
    )

    db.commit()

    return {"result": "deleted"}
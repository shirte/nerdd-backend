from fastapi import APIRouter, Query, WebSocketException, status
from fastapi.encoders import jsonable_encoder
from fastapi.websockets import WebSocket, WebSocketDisconnect, WebSocketState

from ..data import RecordNotFoundError, Repository
from .jobs import augment_job

__all__ = ["get_job_ws", "get_results_ws", "websockets_router"]

websockets_router = APIRouter(prefix="/websocket")


# Note: we need the slash-less and slash version of the routes, because fastapi does not redirect
# from the slash-less version to the slash version (as in normal routes).
@websockets_router.websocket("/jobs/{job_id}")
@websockets_router.websocket("/jobs/{job_id}/")
async def get_job_ws(websocket: WebSocket, job_id: str):
    app = websocket.app
    repository: Repository = app.state.repository

    await websocket.accept()

    try:
        async for _, internal_job in repository.get_job_with_result_changes(job_id):
            job = await augment_job(internal_job, websocket)
            await websocket.send_json(jsonable_encoder(job))
    except RecordNotFoundError as e:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason="Job not found"
        ) from e
    except WebSocketDisconnect:
        # dlient disconnected, no action needed
        pass
    except:
        if websocket.application_state != WebSocketState.DISCONNECTED:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        raise
    finally:
        if websocket.application_state != WebSocketState.DISCONNECTED:
            await websocket.close(code=status.WS_1000_NORMAL_CLOSURE)


# Note: we need the slash-less and slash version of the routes, because fastapi does not redirect
# from the slash-less version to the slash version (as in normal routes).
@websockets_router.websocket("/jobs/{job_id}/results")
@websockets_router.websocket("/jobs/{job_id}/results/")
async def get_results_ws(websocket: WebSocket, job_id: str, page: int = Query()):
    app = websocket.app
    repository: Repository = app.state.repository

    await websocket.accept()

    try:
        try:
            job = await repository.get_job_by_id(job_id)
        except RecordNotFoundError as e:
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION, reason="Job not found"
            ) from e

        page_size = job.page_size

        # num_entries might not be available, yet
        # we assume it to be positive infinity in that case
        if job.num_entries_total is None:
            num_entries = float("inf")
        else:
            num_entries = job.num_entries_total

        page_zero_based = page - 1

        # check if page is clearly out of range
        if page_zero_based < 0 or page_zero_based * page_size >= num_entries:
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION, reason="Page out of range"
            )

        first_mol_id = page_zero_based * page_size
        last_mol_id = min(first_mol_id + page_size, num_entries) - 1

        async for _, new in repository.get_result_changes(job_id, first_mol_id, last_mol_id):
            if new is not None:
                await websocket.send_json(jsonable_encoder(new))
    except WebSocketDisconnect:
        # dlient disconnected, no action needed
        pass
    except:
        if websocket.application_state != WebSocketState.DISCONNECTED:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        raise
    finally:
        if websocket.application_state != WebSocketState.DISCONNECTED:
            await websocket.close(code=status.WS_1000_NORMAL_CLOSURE)

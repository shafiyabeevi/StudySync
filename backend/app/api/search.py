"""
Reference search API endpoint.
Uses Tavily to find academic books and resources.
"""
from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import AuthenticatedUser, get_current_user
from app.services.reference_search import search_references
from app.schemas.models import SearchRequest, SearchResponse, ReferenceResult, ErrorResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/search-references",
    response_model=SearchResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def search(
    request: SearchRequest,
    _user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Search for reference books and academic resources on a topic.
    Returns deduplicated results from trusted academic sources.
    """
    try:
        results = await search_references(request.topic)
        return SearchResponse(
            topic=request.topic,
            results=[ReferenceResult(**r) for r in results],
            total=len(results),
        )
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Search endpoint error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Reference search is temporarily unavailable. Please try again."
        )

import logging
from fastapi import HTTPException, APIRouter

from .models import geocodeDataModel
from ...dependence import (
    googleServicesDepend,
)

router = APIRouter(prefix="/googleServices")
logger = logging.getLogger(__name__)


@router.post("/geocode", response_model=geocodeDataModel.Response)
def get_geocoding(
    googleServices: googleServicesDepend,
    location: geocodeDataModel.Request,
) -> geocodeDataModel.Response:
    """
    Get the location information for a given geocode.
    """
    longitude = location.longitude
    latitude = location.latitude
    try:
        logger.debug(f"Performing geocode location lookup for {(longitude, latitude)=}")
        response = googleServices.geoLocationLookup(longitude, latitude)
    except Exception as e:
        logger.error(f"Got exeception of {e}")
        if "Config Error" in str(e):
            raise HTTPException(status_code=500, detail="Cannot perform geolocation lookup")
        raise HTTPException(status_code=400, detail="Error performing geolocation lookup")
    logger.debug(f"Got location of {response}")
    return geocodeDataModel.Response(location=response)

# @router.post("/stt")
# This is in v1, I am not bothered to move it
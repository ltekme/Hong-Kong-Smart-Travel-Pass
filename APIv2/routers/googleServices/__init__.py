from fastapi import APIRouter

from .models import (
    geocodeDataModel,
    SpeechToTextModel,
)
from ...dependence import googleServicesDepend
from ...config import logger


router = APIRouter(prefix="/googleServices")


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
    logger.debug(f"Performing geocode location lookup for {(longitude, latitude)=}")
    response = googleServices.geoLocationLookup(longitude, latitude)
    logger.debug(f"Got location of {response} for {(longitude, latitude)=}")
    return geocodeDataModel.Response(location=response)


@router.post("/stt")
def speechToText(
    googleServices: googleServicesDepend,
    request: SpeechToTextModel.Request,
) -> SpeechToTextModel.Response:
    """
    Transcribe base64 audio data 
    """
    logger.debug(f"Performing transcribe for {request.audioData[10:]=}")
    response = googleServices.speechToText(request.audioData)
    logger.debug(f"Respondign to transcribe {request.audioData[10:]=} - {response[10:]=}")
    return SpeechToTextModel.Response(
        message=response
    )

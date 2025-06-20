from fastapi import APIRouter

from .models import geocodeDataModel
from .models import SpeechToTextModel
from APIv2.dependence import dbSessionDepend
from APIv2.dependence import getGoogleServiceDepend
from APIv2.logger import logger


router = APIRouter(prefix="/googleServices")


@router.post("/geocode", response_model=geocodeDataModel.Response)
def get_geocoding(
    dbSession: dbSessionDepend,
    getGoogleService: getGoogleServiceDepend,
    location: geocodeDataModel.Request,
) -> geocodeDataModel.Response:
    """
    Get the location information for a given geocode.
    """
    longitude = location.longitude
    latitude = location.latitude
    logger.debug(f"Performing geocode location lookup for {(longitude, latitude)=}")
    response = getGoogleService(dbSession, None).geoLocationLookup(longitude, latitude)
    logger.debug(f"Got location of {response} for {(longitude, latitude)=}")
    return geocodeDataModel.Response(location=response)


@router.post("/stt")
def speechToText(
    dbSession: dbSessionDepend,
    getGoogleService: getGoogleServiceDepend,
    request: SpeechToTextModel.Request,
) -> SpeechToTextModel.Response:
    """
    Transcribe base64 audio data 
    """
    logger.debug(f"Performing transcribe for {request.audioData[:10]=}")
    if not request.audioData or not request.audioData.startswith("data:audio"):
        return SpeechToTextModel.Response(
            message="No Audio"
        )
    dataSplit = request.audioData.split(",")
    dataSection = len(dataSplit)
    if dataSection > 2 or dataSection < 1:
        return SpeechToTextModel.Response(
            message="No Audio"
        )
    response = getGoogleService(dbSession, None).speechToText(dataSplit[1])
    logger.debug(f"Respondign to transcribe {request.audioData[:10]=} - {response[:10]=}")
    return SpeechToTextModel.Response(
        message=response
    )

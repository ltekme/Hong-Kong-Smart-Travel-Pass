export const facebookAppId = process.env.REACT_APP_FACEBOOK_APP_ID; // .env
export const enableAvatar = process.env.REACT_APP_ENABLE_AVATAR !== "false";

export const defaultApiUrl = process.env.REACT_APP_DEFAULT_API_BASE_URL;
export const chatLLMApiUrl = `${defaultApiUrl}/v2/chatLLM`;
export const geolocationApiUrl = `${defaultApiUrl}/v2/googleServices/geocode`;
export const sttApiUrl = `${defaultApiUrl}/v1/stt`;
export const userPofileAuthApiUrl = `${defaultApiUrl}/v2/user/auth`;
export const requestProfileSummoryApiUrl = `${defaultApiUrl}/v2/user/requestProfileSummory`;
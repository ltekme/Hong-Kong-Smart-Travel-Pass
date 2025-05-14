export const facebookAppId = process.env.REACT_APP_FACEBOOK_APP_ID; // .env
export const enableAvatar = process.env.REACT_APP_ENABLE_AVATAR !== "false";

export const defaultApiUrl = process.env.REACT_APP_DEFAULT_API_BASE_URL || "/api";
export const chatLLMApiUrl = `${defaultApiUrl}/v2/chatLLM`;
export const chatLLMApiRecallUrl = `${defaultApiUrl}/v2/chatLLM/recall`;
export const chatLLMchatIDRequestApiUrl = `${defaultApiUrl}/v2/chatLLM/request`;
export const geolocationApiUrl = `${defaultApiUrl}/v2/googleServices/geocode`;
export const sttApiUrl = `${defaultApiUrl}/v1/stt`;
export const userPofileAuthApiUrl = `${defaultApiUrl}/v2/profile/auth`;
export const userPofilePersonalizationApiUrl = `${defaultApiUrl}/v2/profile/summory`;
export const requestProfileSummoryApiUrl = `${defaultApiUrl}/v2/profile/summory/request`;
export const pingUserSessionApiUrl = `${defaultApiUrl}/v2/profile/auth/ping`;

export const userMenuActivationCommand = `/menu`
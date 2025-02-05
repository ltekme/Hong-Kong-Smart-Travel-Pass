export interface IFacebookProfile {
  id: string;
  name: string;
  gender: string;
  accessToken: string;
  profilePicture?: string;
  sessionExpire?: number;
  sessionId?: string;
}

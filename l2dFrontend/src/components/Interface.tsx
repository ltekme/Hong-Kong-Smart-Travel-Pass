export interface IFacebookProfile {
  id: string;
  name: string;
  gender: string;
  accessToken: string;
  profilePicture?: string;
  sessionExpire?: number;
  sessionId?: string;
}


export interface IMessage {
  role: "user" | "ai" | "loading",
  media?: string[],
  placeHolder?: boolean,
  text?: string,
  time?: string,
  error?: boolean,
}

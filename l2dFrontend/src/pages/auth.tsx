import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { loginCognitoUrl } from "../Config";
import Swal from "sweetalert2";
import { getCognotoUser } from "../../src/components/APIService";
import { getSessionInfo } from "../../src/components/ParamStore";

export const AuthPage = () => {
    const navigate = useNavigate();

    useEffect(() => {
        const sessionInfo = getSessionInfo()
        if (sessionInfo.kind === "Authenticated") {
            Swal.fire({
                title: "Already authenticated as " + sessionInfo.username,
                showDenyButton: false,
                showCancelButton: false,
                confirmButtonText: "Continue",
                allowEscapeKey: false,
                allowOutsideClick: false,
            }).then((result) => {
                if (result.isConfirmed) {
                    navigate('/');
                } else if (result.isDenied) {
                    navigate('/');
                }
            });
        }
        Swal.fire({
            title: "You are about to be redirected to login",
            showDenyButton: true,
            showCancelButton: false,
            confirmButtonText: "Continue",
            denyButtonText: `Go back`,
            allowEscapeKey: false,
            allowOutsideClick: false,
        }).then((result) => {
            if (result.isConfirmed) {
                window.location.href = loginCognitoUrl
            } else if (result.isDenied) {
                navigate('/');
            }
        });
    }, [])

    return (<></>)
}

export const AuthCallbackPage = () => {
    const navigate = useNavigate();
    useEffect(() => {
        let exec = async () => {
            const search = window.location.toString().split("#")[1];
            console.debug(search);
            const urlParam = new URLSearchParams(search);
            console.debug(urlParam.keys())
            if (!urlParam.has("access_token")) {
                Swal.fire({
                    icon: "error",
                    title: "Oops...",
                    text: "Missing Access Token",
                    showCancelButton: false,
                    showDenyButton: true,
                    denyButtonText: "Try again",
                    confirmButtonText: "Head Back To Home",
                    allowEscapeKey: false,
                    allowOutsideClick: false,
                }).then((result) => {
                    if (result.isConfirmed) {
                        navigate("/");
                    } else if (result.isDenied) {
                        navigate("/auth/login");
                    }
                });
                return
            }
            try {
                let userInfo = await getCognotoUser({ accessToken: urlParam.get("access_token") });
                Swal.fire({
                    icon: "success",
                    title: `Authenticated as ${userInfo.username}`,
                    showCancelButton: false,
                    showDenyButton: false,
                    confirmButtonText: "Continue",
                    allowEscapeKey: false,
                    allowOutsideClick: false,
                }).then((result) => {
                    if (result.isConfirmed) {
                        navigate("/");
                    } else if (result.isDenied) {
                        navigate("/auth/login");
                    }
                });
            } catch {
                Swal.fire({
                    icon: "error",
                    title: "Oops...",
                    text: "Error during Authentication",
                    showCancelButton: false,
                    showDenyButton: true,
                    denyButtonText: "Try again",
                    confirmButtonText: "Head Back To Home",
                    allowEscapeKey: false,
                    allowOutsideClick: false,
                }).then((result) => {
                    if (result.isConfirmed) {
                        navigate("/");
                    } else if (result.isDenied) {
                        navigate("/auth/login");
                    }
                });
            }
        }
        exec()
    })
    return (<></>)
}
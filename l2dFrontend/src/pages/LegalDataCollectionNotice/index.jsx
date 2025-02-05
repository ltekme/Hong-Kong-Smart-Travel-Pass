import { useEffect, useState, useCallback } from "react";
import ReactMarkdown from "react-markdown";

import enAgg from "./mdc/eng.md";
import zhAgg from "./mdc/zh.md";
import "./index.css";

import Swal from 'sweetalert2'
import withReactContent from 'sweetalert2-react-content'

const MySwal = withReactContent(Swal)


export const LegalDataCollectionNotice = ({
  setConfirmAgree, defaultLang = "zh"
}) => {


  const [mdContent, setMdContent] = useState("");
  const [mdContentLang, setMdContentLang] = useState(defaultLang);

  useEffect(() => {
    const contentLangMap = {
      en: enAgg,
      zh: zhAgg
    };

    console.debug("[LegalDataCollectionNotice] Reading File " + contentLangMap[mdContentLang]);
    fetch(contentLangMap[mdContentLang])
      .then(data => data.text())
      .then(text => {
        // console.log(text);
        setMdContent(text);
      })
      .catch((err) => {
        console.error(err);
      });

  }, [mdContentLang]);

  const handleLanguageChange = useCallback((lang) => {
    setMdContentLang(lang);
  }, []);

  useEffect(() => {
    const show = async () => {
      const result = await MySwal.fire({
        html: (
          <div className="markdown-container">
            <ReactMarkdown>{mdContent}</ReactMarkdown>
          </div>
        ),
        // icon: 'question',
        input: "checkbox",
        inputValue: 1,
        inputPlaceholder: mdContentLang === "zh" ? "本人已閱讀及同意遵守上述條款及細則" : "I have read and agreed to be bound by the above terms and conditions",
        confirmButtonText: mdContentLang === "zh" ? "同意" : "Agree",
        cancelButtonText: mdContentLang === "zh" ? "拒絕" : "Cancel",
        denyButtonText: mdContentLang === "zh" ? "English" : "中文",
        showCancelButton: true,
        showDenyButton: true,
        showCloseButton: false,
        cancelButtonColor: "#d33",
        confirmButtonColor: "#01B468",
        backdrop: true,
        timer: 100000000,
        heightAuto: true,
        timerProgressBar: true,
        customClass: {
          denyButton: 'custom-deny-button',
        },
        allowOutsideClick: false,
        allowEscapeKey: false,
        inputValidator: (result) => {
          return !result && `${mdContentLang === "zh" ? "你需要同意上述條款" : "You need to agree with T&C"}`;
        }
      });

      if (result.isDenied) {
        handleLanguageChange(mdContentLang === "zh" ? "en" : "zh");
      }

      if (result.value) {
        Swal.fire({
          icon: "success",
          title: mdContentLang === "zh" ? "你已同意條款" : "You agreed with T&C :)",
          showConfirmButton: false,
          timer: 1500,
          backdrop: `rgba(0,0,123,0.4)`
        });
        setConfirmAgree(true);
      }
    };

    const timerId = setTimeout(show, 0);
    return () => clearTimeout(timerId);

  }, [mdContent, handleLanguageChange, mdContentLang, setConfirmAgree]);


};
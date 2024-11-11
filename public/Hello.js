import { useState } from "react"
import "./css/style.css"
import "./css/font-awesome.min.css"

export const Hello = () => {
    const [userName, setUserName] = useState("there");

    return <>
    <div id="hello2">
    <h1 class="title">Hello, {userName}</h1>
    <p class="subtitle">How can I help you today?</p>
    </div>

    {/* Login Thrid Part */}
    <section class="w3l-hotair-form">
      <div class="container">

          <div class="workinghny-form-grid">
              <div class="main-hotair">
                  <div class="alert-close">
                      <span class="fa fa-close"></span>
                  </div>
                  <div class="content-wthree">
                      <h2>To Connect With Your Social Media</h2>
                      <div class="social-icons w3layouts">
                          <ul>
                              <li>
                                  <a href="/" class="facebook"><span class="fa fa-facebook"></span> </a>
                              </li>
                              <li>
                                  <a href="/" class="twitter"><span class="fa fa-twitter"></span> </a>
                              </li>
                              <li>
                                  <a href="/" class="pinterest"><span class="fa fa-pinterest"></span> </a>
                              </li>
                          </ul>
                      </div>
                  </div>
                  <div class="w3l_form align-self">
                      <div class="left_grid_info">
                          
                      </div>
                  </div>
              </div>
          </div>
      </div>
      <div class="copyright text-center">
      </div>
  </section>
    </>
}


import { useState, useEffect } from "react";
import ReCAPTCHA from "react-google-recaptcha";
import axios from "axios";

const columnstyle = {
  "@media (minWidth: 600px)": {
    marginBottom: "50px",
  },
};

function App() {
  const [error, setError] = useState(null);
  const [disableButton, setDisableButton] = useState(true);
  const [code, setCode] = useState("");
  const [response, setResponse] = useState(null);
  const [showCaptcha, setShowCaptcha] = useState(false);
  const [loading, setLoading] = useState(false);

  const verifyCapcha = (response) => {
    if (response) {
      setDisableButton(false);
      setResponse(response);
    } else {
      setError("Please verify that you are a human!");
      setDisableButton(true);
      setResponse(null);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setLoading(true);
    const backendUrl = "https://ccb7-197-156-103-205.eu.ngrok.io/verify-captha";

    axios
      .post(backendUrl, JSON.stringify({ response, code }), {
        headers: {
          "Content-Type": "application/json",
        },
      })
      .then((res) => res.data)
      .then((data) => {
        if (data.status == 'ok') {
          window.Telegram.WebApp.sendData("You proved that you are human 😜");
          setLoading(false);
          window.Telegram.WebApp.close();
        } else {
          const message = data.message || "Something went wrong!";
          setError(message);
          setLoading(false);
          alert(message);
        }
      })
      .catch((err) => {
        console.log(err);
        setLoading(false);
        alert("Network error!");
      });
  };

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    console.log(urlParams);
    const code = urlParams.get("code");
    setCode(code);
    setError(null);
    if (code) {
      // show google captcha
      setShowCaptcha(true);
    } else {
      setError("Invalid code! Please try again.");
    }
  }, []);

  return (
    // simple navbar component
    <div>
      <div className="container" style={{ marginBottom: "10px" }}>
        <nav className="navbar navbar-expand-lg bg-light">
          <div className="container-fluid">
            <a className="navbar-brand" href="#">
              recaptchaBot
            </a>
            <button
              className="navbar-toggler"
              type="button"
              data-bs-toggle="collapse"
              data-bs-target="#navbarNav"
              aria-controls="navbarNav"
              aria-expanded="false"
              aria-label="Toggle navigation"
            >
              <span className="navbar-toggler-icon"></span>
            </button>
            <div className="collapse navbar-collapse" id="navbarNav">
              <ul className="navbar-nav">
                <li className="nav-item">
                  <a
                    className="nav-link"
                    aria-current="page"
                    href="https://chapimenge3.github.io"
                  >
                    Creator
                  </a>
                </li>
                <li className="nav-item">
                  <a className="nav-link" href="#">
                    Features
                  </a>
                </li>
                <li className="nav-item">
                  <a className="nav-link" href="#">
                    Contact
                  </a>
                </li>
                <li className="nav-item">
                  <a className="nav-link" href="#">
                    Support Us
                  </a>
                </li>
              </ul>
            </div>
          </div>
        </nav>
      </div>
      <div className="container" style={columnstyle}>
        <div className="row align-items-center ">
          <div className="col-lg-5 text-center text-lg-start">
            <h1 className="display-4 fw-bold lh-1 mb-3">recaptchabot</h1>
            <p className="col-lg-10 fs-4">
              recaptcha Telegram bot verification center.
            </p>
            <div className="d-grid gap-2 d-md-flex justify-content-md-start">
              <button
                type="button"
                className="btn btn-primary btn-lg px-4 me-md-2"
              >
                Get Started
              </button>
              <button
                type="button"
                className="btn btn-outline-secondary btn-lg px-4"
              >
                Learn More
              </button>
            </div>
          </div>

          {/* margin on mobile */}
          <div
            id="verify-form"
            // margin top on mobile
            className="col-lg-7 mt-5 mt-lg-0 p-3 p-lg-5 border form-wrapper"
          >
            {/* // className="col-md-10 mx-auto col-lg-7 "> */}
            <div id="captcha-div">
              <h5 className="card-title">This is a google recaptcha site</h5>
              <p className="card-text">please enter the captcha to continue</p>
              <form method="POST" onSubmit={handleSubmit}>
                {showCaptcha ? (
                  <ReCAPTCHA
                    sitekey="6LfCfLIhAAAAABxhJYFNbtTnRie9fgEdti30OuPu"
                    onChange={verifyCapcha}
                  />
                ) : null}
                <input type="hidden" id="response" name="response" value="" />
                <br />
                {!loading ? (
                  <button
                    type="submit"
                    id="captcha-submit"
                    className="btn btn-primary"
                    disabled={disableButton}
                  >
                    Verify
                  </button>
                ) : (
                  <div className="spinner-border" role="status">
                    <span className="sr-only"></span>
                  </div>
                )}
              </form>
            </div>
            <div id="captcha-error">
              {
                // error message
                error && <p className="text-danger">{error}</p>
              }
            </div>
          </div>
          <div id="verify-success" style={{ display: "none" }}>
            <div className="col-lg-10 mx-auto">
              <div className="alert alert-success" role="alert">
                <h4 className="alert-heading">Well done!</h4>
                <p>You have successfully verified your account.</p>
                <hr />
                <p className="mb-0">
                  You are now allowed to the group. if you still have a problem
                  please contact group admins.
                </p>

                <p>
                  Creator: <a href="https://t.me/chapimenge">Chapi Menge</a>
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div className="container">
        <footer className="py-3 my-4">
          <p className="text-center text-muted">
            &copy; 2022 recaptcha telegram bot. All rights reserved. Chapi Menge
          </p>
        </footer>
      </div>
    </div>
  );
}

export default App;

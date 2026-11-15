import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import ShowcaseNotice from "./ShowcaseNotice";
import "./style.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ShowcaseNotice />
    <App />
  </React.StrictMode>,
);

import { home_view, home_title } from "./views/home.js";
import { clicks_view, clicks_title } from "./views/clicks.js";
import { chat_view, chat_title } from "./views/chat.js";
import { login_view, login_title } from "./views/login.js";
import { register_view, register_title } from "./views/register.js";
import "./components/navbar.js";

const routes = {
    "/": { title: home_title(), render: home_view() },
    "/clicks": { title: clicks_title(), render: clicks_view() },
    "/chat": { title: chat_title(), render: chat_view() },
    "/auth/login": { title: login_title(), render: login_view() },
    "/auth/register": { title: register_title(), render: register_view() },
};

function router() {
    let view = routes[location.pathname];

    if (view) {
        document.title = view.title;
        app.innerHTML = view.render;
    } else {
        history.replaceState("", "", "/");
        router();
    }
};

window.addEventListener("click", e => {
    if (e.target.matches("[data-link]")) {
        e.preventDefault();
        history.pushState("", "", e.target.href);
        router();
    }
});

window.addEventListener("popstate", router);
window.addEventListener("DOMContentLoaded", router);
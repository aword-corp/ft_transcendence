import { home_view, home_title } from "./views/home.js";
import { clicks_view, clicks_title } from "./views/clicks.js";
import { chat_view, chat_title } from "./views/chat.js";
import { login_view, login_title } from "./views/login.js";
import { register_view, register_title } from "./views/register.js";
import "./components/navbar.js";

const routes = {
    "/": { title: home_title(), render: home_view(), auth: "no" },
    "/clicks": { title: clicks_title(), render: clicks_view(), auth: "no" },
    "/chat": { title: chat_title(), render: chat_view(), auth: "yes" },
    "/auth/login": { title: login_title(), render: login_view(), auth: "no_only" },
    "/auth/register": { title: register_title(), render: register_view(), auth: "no_only" },
};

function isAuth() {
    const token = localStorage.getItem("access-token");
    const refresh = localStorage.getItem("refresh-token");

    if (!token || !token.length || Date.now() >= (JSON.parse(atob(token.split('.')[1]))).exp * 1000) {
        localStorage.removeItem("access-token");
        if (!refresh || !refresh.length)
            return (false);
        fetch(
            "https://localhost:8443/api/auth/login/refresh",
            {
                method: "POST",
                headers: {
                    'Accept': 'application/json, text/plain',
                    'Content-Type': 'application/json;charset=UTF-8'
                },
                body: JSON.stringify({ refresh: refresh }),
            }
        ).then((response) => {
            response.json().then((json) => {
                if (!json.access) {
                    localStorage.removeItem("refresh-token");
                    return (false);
                }
                localStorage.setItem("access-token", json.access);
                return (true);
            }
            ).catch((e) => {
                localStorage.removeItem("refresh-token");
                return (false);
            })
        }).catch((e) => {
            localStorage.removeItem("refresh-token");
            return (false);
        });
    }
    return (true);
}

function checkAccess(view) {

    if (isAuth()) {
        if (view.auth == "no_only")
            return (false);
        return (true);
    }
    if (view.auth == "yes")
        return (false);
    return (true);
}

export function router() {
    if (location.pathname == "/auth/logout") {
        localStorage.removeItem("access-token");
        localStorage.removeItem("refresh-token");
        history.pushState("", "", "/");
        router();
    }
    let view = routes[location.pathname];

    if (view && checkAccess(view)) {
        document.title = ` ACorp - ${view.title} `;
        app.innerHTML = view.render;
        if (!isAuth())
            document.getElementById("nav").innerHTML = "<anon-nav-bar class=\"navbar\"></anon-nav-bar>";
        else
            document.getElementById("nav").innerHTML = "<nav-bar class=\"navbar\"></nav-bar>";
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

import { home_view, home_title } from "./views/home.js";
import { clicks_view, clicks_title } from "./views/clicks.js";
import { chat_view, chat_title } from "./views/chat.js";
import { login_view, login_title } from "./views/login.js";
import { register_view, register_title } from "./views/register.js";
import { profile_view, profile_title } from "./views/profile.js";
import { setup_2fa_view, setup_2fa_title } from "./views/setup_2fa.js";
import { leaderboard_view, leaderboard_title } from "./views/leaderboard.js";
import "./components/navbar.js";
import { closeMMSocket } from "./components/socket.js";
import { ft_callback_title, ft_callback_view } from "./views/ft_callback.js";

function logout() {
	localStorage.removeItem("access-token");
	localStorage.removeItem("refresh-token");
}

function remove_2fa() {
	fetch(
		"https://localhost:8443/api/auth/remove_2fa",
		{
			method: "POST",
			headers: {
				'Accept': 'application/json, text/plain',
				'Content-Type': 'application/json;charset=UTF-8',
				'Authorization': `Bearer ${localStorage.getItem("access-token")}`,
			},
		}
	).then((response) => {
		localStorage.removeItem("access-token");
	});
}

const routes = {
	"/": { title: home_title(), render: home_view, auth: "no" },
	"/clicks": { title: clicks_title(), render: clicks_view, auth: "no", destructor: closeMMSocket },
	"/chat": { title: chat_title(), render: chat_view, auth: "yes" },
	"/pong": { title: pong_title(), render: pong_view, auth: "yes" },
	"/auth/login": { title: login_title(), render: login_view, auth: "no_only" },
	"/auth/ft/callback": { title: ft_callback_title(), render: ft_callback_view, auth: "no_only" },
	"/auth/register": { title: register_title(), render: register_view, auth: "no_only" },
	"/profile": { title: profile_title(), render: profile_view, auth: "yes" },
	"/profile/settings/setup_2fa": { title: setup_2fa_title(), render: setup_2fa_view, auth: "yes" },
	"/leaderboard": { title: leaderboard_title(), render: leaderboard_view, auth: "no" },
};

var last_view = "";

const actions = {
	"/profile/settings/remove_2fa": { action: remove_2fa, auth: "yes" },
	"/auth/logout": { action: logout, auth: "yes" },
}

function isAuth() {
	const token = localStorage.getItem("access-token");
	const refresh = localStorage.getItem("refresh-token");

	if (token == null || !token.length || token === "undefined" || Date.now() >= (JSON.parse(atob(token.split('.')[1]))).exp * 1000) {
		localStorage.removeItem("access-token");
		if (refresh == null || !refresh.length || refresh === "undefined")
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
	else {
		fetch(
			"https://localhost:8443/api/auth/validate",
			{
				method: "GET",
				headers: {
					'Accept': 'application/json, text/plain',
					'Content-Type': 'application/json;charset=UTF-8',
					'Authorization': `Bearer ${localStorage.getItem("access-token")}`
				},
			}
		).then((response) => {
			if (response.status !== 200) {
				localStorage.removeItem("access-token");
				localStorage.removeItem("refresh-token");
				return (false);
			}
		}).catch((e) => {
			localStorage.removeItem("access-token");
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
	let view = routes[location.pathname];
	let action = actions[location.pathname];

	if (location.pathname === last_view)
		return;

	if (view && checkAccess(view)) {
		document.title = ` ACorp - ${view.title} `;
		app.innerHTML = view.render();
		if (!isAuth())
			document.getElementById("nav").innerHTML = "<anon-nav-bar class=\"navbar\"></anon-nav-bar>";
		else
			document.getElementById("nav").innerHTML = "<nav-bar class=\"navbar\"></nav-bar>";
		if (routes[last_view] && routes[last_view].destructor)
			routes[last_view].destructor();
		last_view = location.pathname;
	}
	else if (action && checkAccess(action)) {
		action.action();
		last_view = location.pathname;
		history.pushState("", "", "/");
		router();
	}
	else {
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

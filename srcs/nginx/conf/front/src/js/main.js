import { home_view, home_title } from "./views/home.js";
import { clicks_view, clicks_title } from "./views/clicks.js";
import { chat_view, chat_title } from "./views/chat.js";
import { play_view, play_title } from "./views/play.js";
import { pong_view, pong_title } from "./views/pong.js";
import { login_view, login_title } from "./views/login.js";
import { register_view, register_title } from "./views/register.js";
import { profile_view, profile_title } from "./views/profile.js";
import { setup_2fa_view, setup_2fa_title } from "./views/setup_2fa.js";
import { leaderboard_view, leaderboard_title } from "./views/leaderboard.js";
import "./components/navbar.js";
import { closeMMSocket, closeTMSocket, closePongSocket, closeSocketClick, initMMSocket, initTMSocket, initPongSocket, initSocketClick } from "./components/socket.js";
import { ft_callback_title, ft_callback_view } from "./views/ft_callback.js";
import { regular_queue_title, regular_queue_view } from "./views/regular_queue.js";
import { tournament_queue_title, tournament_queue_view } from "./views/tournament_queue.js";
import { user_profile_title, user_profile_view } from "./views/user_profile.js";
import { channels_title, channels_view } from "./views/channels.js";
import { channels_id_title, channels_id_view } from "./views/channels_id.js";

function logout() {
	localStorage.removeItem("access-token");
	localStorage.removeItem("refresh-token");
}

function remove_2fa() {
	fetch(
		"/api/auth/remove_2fa",
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
	"/": { title: home_title, render: home_view, auth: "no" },
	"/clicks": { title: clicks_title, render: clicks_view, auth: "no", constructor: initSocketClick, destructor: closeSocketClick },
	"/chat": { title: chat_title, render: chat_view, auth: "yes" },
	"/play": { title: play_title, render: play_view, auth: "yes" },
	"/play/regular": { title: regular_queue_title, render: regular_queue_view, auth: "yes", constructor: initMMSocket, destructor: closeMMSocket },
	"/play/tournament": { title: tournament_queue_title, render: tournament_queue_view, auth: "yes", constructor: initTMSocket, destructor: closeTMSocket },
	"/channels/:id": { title: channels_id_title, render: channels_id_view, auth: "yes" },
	"/channels": { title: channels_title, render: channels_view, auth: "yes" },
	"/pong/:uuid": { title: pong_title, render: pong_view, auth: "yes", constructor: initPongSocket, destructor: closePongSocket }, // AI will go here with game id "ai"
	"/pong/:uuid/iframe": { title: pong_title, render: pong_view, auth: "yes", constructor: initPongSocket, destructor: closePongSocket }, // AI will go here with game id "ai"
	"/auth/login": { title: login_title, render: login_view, auth: "no_only" },
	"/auth/ft/callback": { title: ft_callback_title, render: ft_callback_view, auth: "no_only" },
	"/auth/register": { title: register_title, render: register_view, auth: "no_only" },
	"/profile/:user": { title: user_profile_title, render: user_profile_view, auth: "yes" },
	"/profile": { title: profile_title, render: profile_view, auth: "yes" },
	"/profile/settings/setup_2fa": { title: setup_2fa_title, render: setup_2fa_view, auth: "yes" },
	"/leaderboard": { title: leaderboard_title, render: leaderboard_view, auth: "no" },
};

var last_view = {};

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
			"/api/auth/login/refresh",
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
			"/api/auth/validate",
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

function getParams(pathname) {
	for (let route in routes) {
		const paramNames = [];
		const regexPath = route.replace(/\/:(\w+)/g, (_, paramName) => {
			paramNames.push(paramName);
			return "/([^/]+)";
		});
		const regex = new RegExp(`^${regexPath}$`);
		const match = pathname.match(regex);
		if (match) {
			const params = match.slice(1).reduce((acc, value, index) => {
				acc[paramNames[index]] = value;
				return acc;
			}, {});
			return { route: routes[route], params };
		}
	}
	return null;
}

export function router() {
	let matchedRoute = getParams(location.pathname);
	let view = matchedRoute ? matchedRoute.route : null;
	let params = matchedRoute ? matchedRoute.params : {};
	let action = actions[location.pathname];


	// if (view === last_view)
	// 	return;

	if (last_view && last_view.destructor)
		last_view.destructor();

	if (view && checkAccess(view)) {
		document.title = ` ACorp - ${view.title(params)} `;
		if (view.constructor)
			view.constructor(params);
		app.innerHTML = view.render(params);
		if (location.pathname.includes("iframe"))
			document.getElementById("nav").innerHTML = "";
		else if (!isAuth())
			document.getElementById("nav").innerHTML = "<anon-nav-bar class=\"navbar\"></anon-nav-bar>";
		else
			document.getElementById("nav").innerHTML = "<nav-bar class=\"navbar\"></nav-bar>";
		last_view = view;
	}
	else if (action && checkAccess(action)) {
		action.action();
		last_view = view;
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

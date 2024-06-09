import "../components/user_profile.js";

export function user_profile_title(params) {
	return (`${params.user} profile`);
}

export function user_profile_view(params) {
	return (`<user-profile user="${params.user}"></user-profile>`);
}

import "../components/channels_id.js";

export function channels_id_title(params) {
	return (`Messages`);
}

export function channels_id_view(params) {
	return (`<channel-id id="${params.id}"></channel-id>`);
}

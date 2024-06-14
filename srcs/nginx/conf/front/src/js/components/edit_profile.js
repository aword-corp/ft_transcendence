import { router } from "../main.js";

class EditProfile extends HTMLElement {
	constructor() {
		super();

		fetch(
			"/api/user/profile",
			{
				method: "GET",
				headers: {
					'Accept': 'application/json, text/plain',
					'Authorization': 'Bearer ' + localStorage.getItem("access-token"),
				},
			}
		).then((response) => {
			response.json().then((json) => {
				if (!json.user)
					return;
				this.innerHTML = `
					<h1>Edit profile</h1>
					<a href="/profile/settings/setup_2fa" data-link id="Setup_2fa">Setup two author authentication</a>
					<form class="auth-form">
						${json.user.has_ft ? "" : `
						<p>
							<label for="id_email">Email:</label>
							<input id="id_email" type=email name="email" maxlength="320" value="${json.user.email}">
						</p>
						`}
						<p>
							<label for="id_username">Username:</label>
							<input id="id_username" type=text name="username" maxlength="32" value="${json.user.username}">
						</p>
						<p>
							<label for="id_display_name">Display name:</label>
							<input id="id_display_name" type=text name="display_name" max_length="64" ${json.user.display_name ? `value="${json.user.display_name}"` : ""}>
						</p>
						<p>
							<label for="id_bio">Bio:</label>
							<input id="id_bio" type=text name="bio" max_length="2048" ${json.user.bio ? `value="${json.user.bio}"` : ""}>
						</p>
						<p>
							<label for="id_password">Password:</label>
							<input id="id_password" type=password name="password">
						</p>
						<p>
							<label for="id_password_confirmation">Password confirmation:</label>
							<input id="id_password_confirmation" type=password name="password_confirmation">
						</p>
						
						<p>
							<label for="id_birth_date">Birth date:</label>
							<input id="id_birth_date" type=date name="birth_date" ${json.user.birth_date ? `value="${json.user.birth_date}"` : ""}>
						</p>
						${json.user.avatar_url ? `<img src="${json.user.avatar_url}" alt="avatar" />` : ""}
						<p>
							<label for="id_avatar_url">Avatar:</label>
							<input id="id_avatar_url" type="file" accept="image/png, image/gif, image/jpeg, image/webp" name="avatar_url">
						</p>
						${json.user.banner_url ? `<img src="${json.user.banner_url}" alt="banner" />` : ""}
						<p>
							<label for="id_banner_url">Banner:</label>
							<input id="id_banner_url" type="file" accept="image/png, image/gif, image/jpeg, image/webp" name="banner_url">
						</p>
						<button type="submit">Edit</button>
						<p id="form-status"></p>
					</form>
	   			`;

				let form = this.querySelector("form");

				async function onSubmit(json) {
					let formData = new FormData(form);
					for (let [name, value] of Array.from(formData.entries())) {
						if ((value === '' && !json.user[name]) || (json.user[name] && json.user[name] === value) || (value.type && !value.size)) formData.delete(name);
					}
					if (formData.entries().next().done) {
						document.getElementById("form-status").innerText = "No changes";
						return;
					}
					try {
						var response = await fetch(
							"/api/user/settings/edit",
							{
								method: "POST",
								headers: {
									'Accept': 'application/json, text/plain',
									'Authorization': 'Bearer ' + localStorage.getItem("access-token"),
								},
								body: formData,
							}
						);
						const code = response.status;
						var json = await response.json();
						if (code !== 200) {
							var msg = "";
							Object.keys(json).forEach((key) => msg += `${key} : ${json[key]}\n`);
							document.getElementById("form-status").innerText = msg;
							return;
						}
						router();
					} catch (e) { }
				}

				form.addEventListener("submit", (event) => {
					event.preventDefault();
					onSubmit(json);
				});
			});
		});

	}
}

customElements.define("edit-profile-form", EditProfile);

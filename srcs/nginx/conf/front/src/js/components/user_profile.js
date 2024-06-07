
class UserProfile extends HTMLElement {
	constructor() {
		super();

		this.innerHTML = `
		`;

		fetch(
			`/api/user/profile/${this.getAttribute("user")}`,
			{
				method: "GET",
				headers: {
					'Accept': 'application/json, text/plain',
					'Content-Type': 'application/json;charset=UTF-8',
					'Authorization': `Bearer ${localStorage.getItem("access-token")}`,
				},
			}
		).then((response) => {
			if (response.status != 200) {
				this.innerText = "";
			}
			response.json().then((json) => {
				if (json.error) {
					this.innerHTML = `
						<div>
							<h1>Error</h1>
							<p>${json.error}</p>
						</div>
						`;
				}
				else if (json.user) {
					let user = json.user;
					this.innerHTML = `
						<div>
							<img src=${user.avatar_url ? user.avatar_url : ""} />
							<img src=${user.banner_url ? user.banner_url : ""} />
							<p>${user.display_name}</p>
							<p>${user.username}</p>
							<p>${user.bio}</p>
							<p>${user.region}</p>
							<p>${user.country_code}</p>
							<p>${user.language}</p>
							<p>${user.grade}</p>
							<p>${user.created_at}</p>
							<p>${user.xp}</p>
							<p>${user.elo}</p>
							<p>${user.status}</p>
						</div>
					`;
				}
			});
		});
	}
}
customElements.define("user-profile", UserProfile);

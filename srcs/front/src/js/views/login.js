export function login_title() {
	return ("");
}

export function login_view() {

	return (`
		<form class="auth-form" method="post" action="/api/auth/login">
			<p>
				<label for="id_username">Username/Email:</label>
				<input id="id_username" type=text name="username" required>
			</p>
			<p>
				<label for="id_password">Password:</label>
				<input id="id_password" type=password name="password" required>
			</p>
			<button type="submit">Login</button>
		</form>
	`);
}
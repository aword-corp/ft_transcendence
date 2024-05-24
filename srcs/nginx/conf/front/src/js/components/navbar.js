class AnonNavbar extends HTMLElement {
	constructor() {
		super();

		this.innerHTML = `
			<div class="left-nav">
				<a href="/" data-link id="Home">Home</a>
				<a href="/clicks" data-link id="Clicks">Clicks</a>
			</div>
			<div class="right-nav">
				<a href="/auth/login" data-link id="Login">Login</a>
				<a href="/auth/register" data-link id="Register">Register</a>
			</div>
		`;
	}
}

customElements.define("anon-nav-bar", AnonNavbar);

class Navbar extends HTMLElement {
	constructor() {
		super();

		this.innerHTML = `
			<div class="left-nav">
				<a href="/" data-link id="Home">Home</a>
				<a href="/clicks" data-link id="Clicks">Clicks</a>
				<a href="/chat" data-link id="Chat">Chat</a>
			</div>
			<div class="right-nav">
				<a href="/auth/logout" data-link id="Register">Logout</a>
			</div>
		`;
	}
}

customElements.define("nav-bar", Navbar);

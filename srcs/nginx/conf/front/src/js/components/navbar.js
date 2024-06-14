import { router } from "../main.js";

class AnonNavbar extends HTMLElement {
    constructor() {
        super();

        this.innerHTML = `
            <div class="left-nav">
                <a href="/" data-link id="Home">Home</a>
                <a href="/clicks" data-link id="Clicks">Clicks</a>
                <a href="/leaderboard" data-link id="Leaderboard">Leaderboard</a>
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
                <a href="/play" data-link id="Play">Play</a>
                <a href="/clicks" data-link id="Clicks">Clicks</a>
                <a href="/channels" data-link id="Channels">Chat</a>
                <a href="/leaderboard" data-link id="Leaderboard">Leaderboard</a>
                <a href="/pong" data-link id="Pong">Pong</a>
            </div>
            <div class="right-nav">
                <a href="/profile" data-link id="Profile">Profile</a>
                <a href="/auth/logout" data-link id="Logout">Logout</a>
            </div>
        `;
    }
}

customElements.define("nav-bar", Navbar);

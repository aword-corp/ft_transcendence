class Leaderboard extends HTMLElement {
	constructor() {
		super();

		fetch("https://localhost:8443/api/leaderboard", {
			method: "GET",
			headers: {
				Accept: "application/json, text/plain",
				"Content-Type": "application/json;charset=UTF-8",
			},
		}).then((response) => {
			response.json().then((json) => {
				const leaderboardElement = document.getElementById("leaderboard");
				const leaderboardData = json.leaderboard;

				leaderboardElement.innerHTML = '';

				const table = document.createElement('table');
				table.style.width = '100%';
				table.style.borderCollapse = 'collapse';

				const header = table.createTHead();
				const headerRow = header.insertRow();
				const nameHeader = document.createElement('th');
				nameHeader.textContent = 'Name';
				nameHeader.style.border = '1px solid black';
				nameHeader.style.padding = '8px';
				const scoreHeader = document.createElement('th');
				scoreHeader.textContent = 'Score';
				scoreHeader.style.border = '1px solid black';
				scoreHeader.style.padding = '8px';

				headerRow.appendChild(nameHeader);
				headerRow.appendChild(scoreHeader);

				const tbody = table.createTBody();
				JSON.parse(leaderboardData, (name, score) => {
					if (!name || !name.length)
						return ;
					const row = tbody.insertRow();
					const nameCell = row.insertCell();
					const scoreCell = row.insertCell();

					nameCell.textContent = name;
					nameCell.style.textAlign = 'center';
					nameCell.style.border = '1px solid black';
					nameCell.style.padding = '8px';	
					scoreCell.textContent = score;
					scoreCell.style.textAlign = 'center';
					scoreCell.style.border = '1px solid black';
					scoreCell.style.padding = '8px';
				});

				leaderboardElement.appendChild(table);
			});
		});

		this.innerHTML = `
			<p id="leaderboard"></p>
		`;
	}
}

customElements.define("leader-board", Leaderboard);

document.addEventListener("DOMContentLoaded", async () => {
    const gamesList = document.getElementById("games-list");
    const API_KEY = '01bb6991110843acbf49d6d009b87355';

    async function fetchGames() {
        try {
            const response = await fetch(`https://api.rawg.io/api/games?key=${API_KEY}`);
            const data = await response.json();

            if (data.results && data.results.length > 0) {
                displayGames(data.results);
            } else {
                gamesList.innerHTML = "<p>No games found.</p>";
            }
        } catch (error) {
            console.error("Error fetching games:", error);
            gamesList.innerHTML = "<p>Failed to load games.</p>";
        }
    }

    function displayGames(games) {
        gamesList.innerHTML = games.map(game => `
            <a href="https://rawg.io/games/${game.slug}" target="_blank" class="game">
                <img src="${game.background_image}" alt="${game.name}">
                <h3>${game.name}</h3>
                <p>${game.released ? `Released: ${game.released}` : 'Release date not available'}</p>
            </a>
        `).join('');
    }

    fetchGames();
});

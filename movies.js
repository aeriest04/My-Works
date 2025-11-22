document.addEventListener("DOMContentLoaded", async () => { 
    const moviesList = document.getElementById("movies-list"); 
 
    async function fetchMovies() { 
        try { 
            const response = await 
fetch("https://api.themoviedb.org/3/movie/popular?api_key=abee0aaa4b0483c25a811589dc93d783"); 
            const data = await response.json(); 
             
            if (data.results && data.results.length > 0) { 
                displayMovies(data.results); 
            } else { 
                moviesList.innerHTML = "<p>No movies found.</p>"; 
            } 
        } catch (error) { 
            console.error("Error fetching movies:", error); 
            moviesList.innerHTML = "<p>Failed to load movies.</p>"; 
        } 
    } 
 
    function displayMovies(movies) { 
        moviesList.innerHTML = movies.map(movie => ` 
            <a href="https://www.themoviedb.org/movie/${movie.id}" 
target="_blank" class="movie"> 
                <img src="https://image.tmdb.org/t/p/w500${movie.poster_path}" 
alt="${movie.title}"> 
                <h3>${movie.title}</h3> 
                <p>${movie.overview}</p> 
            </a> 
        `).join(''); 
    } 
 
    fetchMovies(); 
});
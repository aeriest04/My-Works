const apiKey = "AIzaSyCasg7SLmG_csYEwrXmKnQWw3z_W7LRSlI";  
const searchInput = document.getElementById("search-music"); 
const searchButton = document.getElementById("search-btn"); 
const musicResults = document.getElementById("music-results"); 
 
async function searchYouTube(query) { 
    const url = 
`https://www.googleapis.com/youtube/v3/search?part=snippet&q=${encodeURIComponent
 (query)}&type=video&key=${apiKey}&maxResults=10`; 
 
    try { 
        const response = await fetch(url); 
        if (!response.ok) throw new Error(`HTTP error! Status: 
${response.status}`); 
         
        const data = await response.json(); 
        if (!data.items) throw new Error("No items found in API response."); 
         
        displayVideos(data.items); 
    } catch (error) { 
        console.error("Error fetching data:", error); 
        musicResults.innerHTML = `<p>Error fetching videos. Check your API key 
and restrictions.</p>`; 
    } 
} 
 
function displayVideos(videos) { 
    if (!videos || videos.length === 0) { 
        musicResults.innerHTML = "<p>No videos found.</p>"; 
        return; 
    } 
 
    musicResults.innerHTML = videos.map(video => ` 
        <div class="music-item"> 
            <a href="https://www.youtube.com/watch?v=${video.id.videoId}" 
target="_blank"> 
                <h3>${video.snippet.title}</h3> 
                <img src="${video.snippet.thumbnails.medium.url}" 
alt="${video.snippet.title}"> 
            </a> 
            <iframe width="300" height="200" 
src="https://www.youtube.com/embed/${video.id.videoId}" frameborder="0" 
allowfullscreen></iframe> 
        </div> 
    `).join(''); 
} 
 
searchButton.addEventListener("click", () => { 
    const query = searchInput.value.trim(); 
    if (!query) { 
        musicResults.innerHTML = "<p>Please enter a song name.</p>"; 
        return; 
    } 
    searchYouTube(query); 
});

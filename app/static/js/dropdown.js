// Message One
document.getElementById('firstMessage').addEventListener("click", () => {
  document.getElementById('addComment').value = "Did Well Today";
})

// Message Two
document.getElementById('secondMessage').addEventListener("click", () => {
  document.getElementById('addComment').value = "Misbehaved Today";
})

// Message Three
document.getElementById('thirdMessage').addEventListener("click", () => {
  document.getElementById('addComment').value = "Rewarded Points!";
})

// Add Comment
const comment = () =>{
  message = document.getElementById('addComment').value;
  document.getElementById('realComment').value = message;
}
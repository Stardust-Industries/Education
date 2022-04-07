const enterUrl = () => {
  url = document.getElementById('url').value;
  location.href = `https://education.stardust-industries.repl.co/classes/${url}`;
}